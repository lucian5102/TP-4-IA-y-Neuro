"""
¿Qué "ven" los modelos abiertos en cada imagen? Clasificación sin entrenamiento extra
(zero-shot) entre dos frases: "a photo of a chihuahua" y "a photo of a blueberry muffin".

Sirve para ver si el ataque funcionó sobre los modelos que usamos para fabricarlo,
antes de probarlo en gpt-4o-mini y ChatGPT.

Uso:  python evaluar_clip.py                          (lee resultados/*.png y escribe respuestas_clip.csv)
"""
import csv
from pathlib import Path

import open_clip
import torch
import torch.nn.functional as F
from PIL import Image

import sys

from ataque_transfer import GRANDE, MODELOS, cargar, embed

FRASES = ["a photo of a chihuahua", "a photo of a blueberry muffin"]
AQUI = Path(__file__).resolve().parent


def main():
    carpeta = AQUI / (sys.argv[1] if len(sys.argv) > 1 else "resultados")
    destino = AQUI / (sys.argv[2] if len(sys.argv) > 2 else "respuestas_clip.csv")
    imagenes = sorted(carpeta.glob("*_limpia.png")) + sorted(carpeta.glob("*_atacada.png"))
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    filas = []
    for nombre, pesos in MODELOS + [GRANDE]:
        m, _, _ = open_clip.create_model_and_transforms(nombre, pretrained=pesos)
        m.eval().to(dev)
        tok = open_clip.get_tokenizer(nombre)
        with torch.no_grad():
            textos = F.normalize(m.encode_text(tok(FRASES).to(dev)), dim=-1)
            for ruta in imagenes:
                x = F.interpolate(cargar(ruta, 448).to(dev), size=224, mode="bilinear", align_corners=False)
                p = (100 * embed(m, x) @ textos.T).softmax(-1)[0]
                filas.append({"imagen": ruta.name, "modelo": f"{nombre}/{pesos}",
                              "prob_chihuahua": round(p[0].item(), 3), "prob_muffin": round(p[1].item(), 3),
                              "respuesta": "muffin" if p[1] > p[0] else "chihuahua"})
                print(filas[-1])
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    main()
