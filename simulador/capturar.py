"""
Saca capturas de conversaciones guardadas en JSONL, con el formato del simulador.

Usa Chrome en modo headless (sin abrir ventanas) y el modo ?captura= del simulador.
Antes hay que levantar el servidor en la raíz del repo:
  python3 -m http.server 8077 --bind 127.0.0.1

Uso:
  python simulador/capturar.py datos/transcripciones/lote_gpt-4o-mini_20261121-0310.jsonl S1:1 S2:1 ...
  python simulador/capturar.py datos/transcripciones/vision_gpt-4o-mini_X.jsonl n:0 n:1 ...
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RAIZ = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8077/simulador/"


def capturar(jsonl, clave, salida, ancho=1200):
    if clave.startswith("n:"):
        q = f"n={clave[2:]}"
    else:
        partes = clave.split(":")
        q = "e={}&r={}".format(*partes[:2]) + (f"&turno={partes[2]}" if len(partes) > 2 else "")
    url = f"{BASE}?captura=../{jsonl}&{q}"
    with tempfile.TemporaryDirectory() as perfil:
        tmp = Path(perfil) / "c.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={perfil}", f"--window-size={ancho},12000",
                        "--virtual-time-budget=6000", f"--screenshot={tmp}", url],
                       check=True, capture_output=True)
        im = Image.open(tmp).convert("RGB")
    # recorta el fondo vacío de abajo
    a = np.asarray(im.convert("L"))[:, 40:]
    fondo = a[-1, -1]
    filas = np.where((np.abs(a.astype(int) - int(fondo)) > 6).any(1))[0]
    alto = min(im.height, int(filas.max()) + 40)
    im.crop((0, 0, im.width, alto)).save(salida)
    return salida


if __name__ == "__main__":
    jsonl = sys.argv[1]
    modelo = "gpt4omini"
    for clave in sys.argv[2:]:
        if clave.startswith("n:"):
            nombre, ancho = f"imagen_{clave[2:]}", 1200
        else:
            p = clave.split(":")
            nombre = f"{p[0]}_r{p[1]}" + (f"_t{p[2]}" if len(p) > 2 else "")
            ancho = 900 if len(p) > 2 else 1200
        destino = RAIZ / "capturas" / f"{modelo}_{nombre}.png"
        print(capturar(jsonl, clave, destino, ancho))
