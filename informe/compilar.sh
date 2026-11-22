#!/bin/zsh
# Compila el informe, le pone la portada y deja Estrada_Kuschnir.pdf en la raíz del repo y en el Escritorio.
set -e
cd "$(dirname "$0")"
../.venv/bin/python ../figuras/hacer_figuras.py > /dev/null
../.venv/bin/python preparar_imagenes.py > /dev/null
../.venv/bin/python generar_anexos.py > /dev/null
tectonic -X compile informe.tex 2>&1 | grep -iE "^error|overfull" || true
../.venv/bin/python - <<'PY'
from pypdf import PdfReader, PdfWriter
from pathlib import Path
from pypdf import PageObject, Transformation
A4 = (595.28, 841.89)
w = PdfWriter()
# la portada viene en otro tamaño: se escala de forma uniforme a A4 y se centra
port = PdfReader("portada.pdf").pages[0]
ancho, alto = float(port.mediabox.width), float(port.mediabox.height)
k = min(A4[0] / ancho, A4[1] / alto)
hoja = PageObject.create_blank_page(width=A4[0], height=A4[1])
hoja.merge_transformed_page(port, Transformation().scale(k, k).translate((A4[0] - ancho * k) / 2, (A4[1] - alto * k) / 2))
w.add_page(hoja)
for pg in PdfReader("informe.pdf").pages:
    w.add_page(pg)
# se escribe encima del mismo archivo (sin reemplazarlo) para que el visor de VS Code lo recargue
import io
buf = io.BytesIO()
w.write(buf)
with open("../Estrada_Kuschnir.pdf", "r+b" if Path("../Estrada_Kuschnir.pdf").exists() else "wb") as f:
    f.seek(0); f.write(buf.getvalue()); f.truncate()
print(len(w.pages), "páginas")
PY
