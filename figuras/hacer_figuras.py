"""
Figura 1: cuántos mensajes le enviamos a cada modelo hasta que dijo la primera
afirmación falsa, guion por guion. Una conversación por guion y por modelo.

Lee datos/chatgpt_web.csv (ChatGPT web) y datos/transcripciones/etiquetas.csv
(gpt-4o-mini, la primera corrida de cada guion, rep = 1).
Escribe figuras/fig1_turnos.pdf y .png
"""
import csv
import tempfile
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle

RAIZ = Path(__file__).resolve().parents[1]
TEAL, NARANJA = "#26788E", "#E2480C"
TINTA, GRIS, LINEA = "#222222", "#8a8a8a", "#e4e4e4"
ESTRATEGIAS = {
    "S1": "Premisa falsa",
    "S2": "Completar el patrón",
    "S3": "Explica y no aplica",
    "S4": "Trampa de unidades",
    "S5": "Presión social",
    "S6": "Del titular al extremo",
}
MAX_TURNO = 6


def fuente():
    """Charter (la tipografía del informe) si está en el sistema; si no, DejaVu Serif."""
    ttc = Path("/System/Library/Fonts/Supplemental/Charter.ttc")
    if ttc.exists():
        try:
            from fontTools.ttLib import TTCollection
            tmp = Path(tempfile.gettempdir()) / "tp4_charter"
            tmp.mkdir(exist_ok=True)
            for i, f in enumerate(TTCollection(str(ttc)).fonts):
                ruta = tmp / f"charter_{i}.ttf"
                if not ruta.exists():
                    f.save(str(ruta))
                fm.fontManager.addfont(str(ruta))
            return "Charter"
        except Exception:
            pass
    return "DejaVu Serif"


def leer():
    """Devuelve {modelo: {estrategia: turno del primer error o None}}."""
    datos = {"viejo": {}, "nuevo": {}}
    for fila in csv.DictReader((RAIZ / "datos/transcripciones/etiquetas.csv").read_text(encoding="utf-8").splitlines()):
        if fila["archivo"].startswith("lote_") and fila["rep"] == "1":
            t = fila["turno_falla"].strip()
            datos["viejo"][fila["estrategia"]] = int(t) if t else None
    for fila in csv.DictReader((RAIZ / "datos/chatgpt_web.csv").read_text(encoding="utf-8").splitlines()):
        if fila.get("estrategia"):
            t = (fila.get("turno_falla") or "").strip()
            datos["nuevo"][fila["estrategia"]] = int(t) if t else None
    return datos


SUPERFICIE, TINTA2, APAGADO, GRILLA, EJE = "#ffffff", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"


def mezcla(color, k):
    """Color entre blanco (k=0) y el color pleno (k=1)."""
    r, g, b = to_rgb(color)
    return (1 - k * (1 - r), 1 - k * (1 - g), 1 - k * (1 - b))


def barra(ax, y, largo, alto, color):
    """Barra horizontal desde 0."""
    if largo > 0:
        ax.add_patch(Rectangle((0, y - alto / 2), largo, alto, linewidth=0, facecolor=color, zorder=2))


def main():
    r"""Escribe figuras/fig1_turnos.tex (pgfplots), que el informe incluye con \input."""
    datos = leer()
    filas = list(ESTRATEGIAS)
    n = len(filas)
    pos = {sid: n - i for i, sid in enumerate(filas)}          # S1 arriba

    def coords(clave, con_error):
        pts = []
        for sid in filas:
            t = datos[clave].get(sid)
            if (t is not None) == con_error:
                pts.append(f"({t if con_error else MAX_TURNO},{pos[sid]})")
        return " ".join(pts)

    def barras(clave, color, shift, con_error):
        c = coords(clave, con_error)
        if not c:
            return ""
        if con_error:
            estilo = (f"fill={color}, draw=none, bar shift={shift}, forget plot, nodes near coords, "
                      "nodes near coords style={font=\\footnotesize, text=black!70, anchor=west, xshift=1pt}")
        else:
            estilo = f"fill={color}!22, draw=none, bar shift={shift}, forget plot"
        return "\\addplot[" + estilo + "] coordinates {" + c + "};\n"

    etiquetas = ",".join(f"{{{sid}\\enspace {ESTRATEGIAS[sid]}}}" for sid in reversed(filas))
    err_viejo, err_nuevo = barras("viejo", "viejo", "3.9pt", True), barras("nuevo", "nuevo", "-3.9pt", True)
    ok_viejo, ok_nuevo = barras("viejo", "viejo", "3.9pt", False), barras("nuevo", "nuevo", "-3.9pt", False)
    tex = rf"""% Generado por figuras/hacer_figuras.py a partir de los CSV. No editar a mano.
\begin{{tikzpicture}}
\begin{{axis}}[
  width=0.70\linewidth, height=7.6cm,
  xbar, bar width=5.5pt, xmax=6.02,
  xmin=0, xtick={{0,...,{MAX_TURNO}}},
  ymin=0.4, ymax={n + 0.6}, ytick={{1,...,{n}}},
  yticklabels={{{etiquetas}}},
  axis x line*=bottom, axis y line*=left,
  y axis line style={{draw=none}}, ytick style={{draw=none}},
  x axis line style={{gris!70}}, xtick style={{gris!70}},
  tick label style={{font=\small}}, xticklabel style={{text=gris}},
  xmajorgrids, major grid style={{gris!25, line width=0.4pt}},
  xlabel={{Mensajes enviados hasta la primera afirmación falsa}},
  xlabel style={{font=\small, text=black!75}},
  legend style={{draw=none, font=\small, at={{(0,1.02)}}, anchor=south west,
                legend columns=3, /tikz/every even column/.append style={{column sep=1.2em}}}},
  legend image code/.code={{\fill[#1] (0cm,-0.1cm) rectangle (0.32cm,0.12cm);}},
  clip=false,
]
% leyenda fija (no depende de que haya barras de cada tipo)
\addlegendimage{{legend image code/.code={{\fill[viejo] (0cm,-0.1cm) rectangle (0.32cm,0.12cm);}}}}
\addlegendentry{{gpt-4o-mini (2024)}}
\addlegendimage{{legend image code/.code={{\fill[nuevo] (0cm,-0.1cm) rectangle (0.32cm,0.12cm);}}}}
\addlegendentry{{ChatGPT web (2026)}}
\addlegendimage{{legend image code/.code={{\fill[viejo!22] (0cm,0.01cm) rectangle (0.32cm,0.12cm);
                                          \fill[nuevo!22] (0cm,-0.1cm) rectangle (0.32cm,-0.01cm);}}}}
\addlegendentry{{sin error}}
% barras llenas: el modelo dijo una afirmación falsa en ese mensaje
{err_viejo}{err_nuevo}
% barras claras: la conversación llegó al final sin errores
{ok_viejo}
{ok_nuevo}
\end{{axis}}
\end{{tikzpicture}}
"""
    (RAIZ / "figuras" / "fig1_turnos.tex").write_text(tex, encoding="utf-8")
    suelta = r"""\documentclass[11pt,border=6pt]{standalone}
\usepackage{fontspec}\setmainfont{Charter}
\usepackage{pgfplots}\pgfplotsset{compat=1.18}
\definecolor{nuevo}{HTML}{26788E}\definecolor{viejo}{HTML}{E2480C}\definecolor{gris}{HTML}{777777}
\newlength{\anchotexto}\setlength{\anchotexto}{16.4cm}
\begin{document}\let\linewidth\anchotexto
\input{fig1_turnos.tex}
\end{document}
"""
    import shutil, subprocess, tempfile
    carpeta = RAIZ / "figuras"
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(carpeta / "fig1_turnos.tex", tmp)
        (Path(tmp) / "fig1_suelta.tex").write_text(suelta, encoding="utf-8")
        subprocess.run(["tectonic", "fig1_suelta.tex"], cwd=tmp, check=True, capture_output=True)
        shutil.copy(Path(tmp) / "fig1_suelta.pdf", carpeta / "fig1_turnos.pdf")
    import pymupdf
    pymupdf.open(carpeta / "fig1_turnos.pdf")[0].get_pixmap(dpi=250).save(carpeta / "fig1_turnos.png")
    print(datos)


if __name__ == "__main__":
    main()
