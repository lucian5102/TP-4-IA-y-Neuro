"""
Prepara las imágenes del informe a partir de capturas/.
- ChatGPT web: recorta la columna de la conversación (sin re-comprimir: PNG).
- gpt-4o-mini: las capturas por turno ya salen del simulador listas para usar.
- Pruebas con imágenes: sólo la imagen subida y la respuesta.
"""
import shutil
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "informe" / "img"
OUT.mkdir(parents=True, exist_ok=True)
CAP = RAIZ / "capturas"

for f in sorted(CAP.glob("chatgpt_S*_t*.png")):
    shutil.copy(f, OUT / f.name)

for f in sorted(CAP.glob("gpt4omini_S*_t*.png")):
    shutil.copy(f, OUT / f.name)

for f in sorted(CAP.glob("vision_gpt4omini_*.jpg")):
    Image.open(f).convert("RGB").crop((300, 90, 1150, 460)).save(OUT / f"{f.stem}.png")

for f in sorted(CAP.glob("vision_chatgpt_*.jpg")):
    Image.open(f).convert("RGB").crop((470, 45, 1075, 250)).save(OUT / f"{f.stem}.png")
