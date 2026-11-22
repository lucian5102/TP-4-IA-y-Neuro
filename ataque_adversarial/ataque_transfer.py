"""
Ataque adversarial por transferencia (estilo M-Attack, Li et al. 2025).

Idea: no tenemos acceso a los pesos de gpt-4o-mini, así que atacamos un conjunto
de modelos abiertos de visión (CLIP) que "ven" parecido. Buscamos un ruido chico
(cada píxel cambia como mucho EPS/255) que haga que, para esos modelos, recortes
de la foto del chihuahua se parezcan a la foto de un muffin. Si el ruido engaña a
varios modelos distintos a la vez, hay chances de que también engañe a uno cerrado.

Uso (lo que corrimos, ver cluster_a100/correr_a100.sbatch):
  python ataque_transfer.py --fuente fuentes/casilla_f3c2.png \
      --objetivo fuentes/casilla_f1c1.png fuentes/casilla_f2c2.png ... \
      --lado 224 --grande --eps 8 --pasos 400 --salida resultados
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import open_clip
import torch
import torch.nn.functional as F
from PIL import Image

MODELOS = [
    ("ViT-B-32", "laion2b_s34b_b79k"),
    ("ViT-B-16", "laion2b_s34b_b88k"),
    ("ViT-B-32", "openai"),
]
# con --grande se suma un modelo más pesado; el paper de M-Attack usa uno de este tamaño
GRANDE = ("ViT-L-14", "laion2b_s32b_b82k")
MEDIA = torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(1, 3, 1, 1)
DESVIO = torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(1, 3, 1, 1)


def cargar(ruta, lado):
    im = Image.open(ruta).convert("RGB")
    w, h = im.size
    c = min(w, h)
    im = im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c)).resize((lado, lado), Image.BICUBIC)
    return torch.from_numpy(np.asarray(im)).permute(2, 0, 1).float().div(255).unsqueeze(0)


def guardar(t, ruta):
    arr = (t.squeeze(0).permute(1, 2, 0).clamp(0, 1).cpu().numpy() * 255).round().astype(np.uint8)
    Image.fromarray(arr).save(ruta)


def recorte_aleatorio(x, gen, escala=(0.5, 1.0)):
    _, _, h, w = x.shape
    s = escala[0] + (escala[1] - escala[0]) * torch.rand(1, generator=gen).item()
    ch, cw = int(h * s), int(w * s)
    i = torch.randint(0, h - ch + 1, (1,), generator=gen).item()
    j = torch.randint(0, w - cw + 1, (1,), generator=gen).item()
    return F.interpolate(x[:, :, i:i + ch, j:j + cw], size=224, mode="bilinear", align_corners=False)


def embed(modelo, x):
    x = (x - MEDIA.to(x.device)) / DESVIO.to(x.device)
    return F.normalize(modelo.encode_image(x), dim=-1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuente", required=True)
    ap.add_argument("--objetivo", nargs="*", default=[], help="una o más fotos del objetivo (por ejemplo muffins)")
    ap.add_argument("--grande", action="store_true", help="sumar ViT-L-14 al conjunto de modelos")
    ap.add_argument("--objetivo_texto", default="a photo of a blueberry muffin",
                    help="descripción del objetivo; se usa además de la foto, o sola si no hay foto")
    ap.add_argument("--eps", type=float, default=16, help="máximo cambio por píxel, en escala 0-255")
    ap.add_argument("--pasos", type=int, default=300)
    ap.add_argument("--alfa", type=float, default=1.0, help="tamaño de paso, en escala 0-255")
    ap.add_argument("--lado", type=int, default=448)
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--salida", default="resultados")
    a = ap.parse_args()

    # en una Mac M1 la CPU resultó mucho más rápida que MPS para esto
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(a.semilla)
    gen = torch.Generator().manual_seed(a.semilla)

    lista = MODELOS + ([GRANDE] if a.grande else [])
    modelos, tokenizadores = [], []
    for nombre, pesos in lista:
        m, _, _ = open_clip.create_model_and_transforms(nombre, pretrained=pesos)
        modelos.append(m.eval().to(dev).requires_grad_(False))
        tokenizadores.append(open_clip.get_tokenizer(nombre))

    x0 = cargar(a.fuente, a.lado).to(dev)
    eps, alfa = a.eps / 255, a.alfa / 255

    # el "objetivo" de cada modelo: promedio entre las fotos de muffin (si hay) y la frase
    fotos_obj = [cargar(f, a.lado).to(dev) for f in a.objetivo]
    objetivos = []
    with torch.no_grad():
        for m, tok in zip(modelos, tokenizadores):
            partes = [F.normalize(m.encode_text(tok([a.objetivo_texto]).to(dev)), dim=-1)]
            for obj in fotos_obj:
                partes.append(embed(m, F.interpolate(obj, size=224, mode="bilinear", align_corners=False)))
            objetivos.append(F.normalize(torch.stack(partes).mean(0), dim=-1))

    delta = torch.zeros_like(x0, requires_grad=True)
    t0 = time.time()
    for paso in range(a.pasos):
        x = (x0 + delta).clamp(0, 1)
        perdida = 0
        for m, e_obj in zip(modelos, objetivos):
            e_x = embed(m, recorte_aleatorio(x, gen))
            if fotos_obj:
                # además del objetivo global, un recorte de una de las fotos de muffin (local contra local)
                k = torch.randint(0, len(fotos_obj), (1,), generator=gen).item()
                with torch.no_grad():
                    e_loc = embed(m, recorte_aleatorio(fotos_obj[k], gen))
                perdida = perdida - 0.5 * ((e_x * e_obj).sum() + (e_x * e_loc).sum())
            else:
                perdida = perdida - (e_x * e_obj).sum()
        perdida = perdida / len(modelos)
        perdida.backward()
        with torch.no_grad():
            delta -= alfa * delta.grad.sign()
            delta.clamp_(-eps, eps)
            delta.copy_((x0 + delta).clamp(0, 1) - x0)
        delta.grad.zero_()
        if paso % 25 == 0 or paso == a.pasos - 1:
            print(f"paso {paso:4d}  similitud con el muffin {-perdida.item():.3f}  ({time.time() - t0:.0f}s)", flush=True)

    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    base = f"{Path(a.fuente).stem}_eps{int(a.eps)}"
    adv = (x0 + delta).clamp(0, 1).detach()
    guardar(x0, out / f"{Path(a.fuente).stem}_limpia.png")
    guardar(adv, out / f"{base}_atacada.png")
    # el ruido va de -eps a +eps; lo estiramos a 0-1 para poder verlo
    guardar(delta.detach() / (2 * eps) + 0.5, out / f"{base}_ruido_amplificado.png")

    with torch.no_grad():
        sims = {}
        for (nombre, pesos), m, e_obj in zip(lista, modelos, objetivos):
            r = lambda t: F.interpolate(t, size=224, mode="bilinear", align_corners=False)
            sims[f"{nombre}/{pesos}"] = {
                "limpia_vs_muffin": round((embed(m, r(x0)) * e_obj).sum().item(), 4),
                "atacada_vs_muffin": round((embed(m, r(adv)) * e_obj).sum().item(), 4),
            }
    print(json.dumps(sims, indent=1))


if __name__ == "__main__":
    main()
