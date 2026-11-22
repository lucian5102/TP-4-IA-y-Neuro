"""
Genera informe/anexos.tex: los guiones y las capturas de las conversaciones.
Correr después de informe/preparar_imagenes.py.

Cada captura es un link a la imagen completa en el repositorio (\repourl en informe.tex).
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
IMG = RAIZ / "informe" / "img"
CARAS = ["f2c1", "f2c3", "f3c2", "f1c2"]
VERSIONES = ["limpia", "eps8_atacada", "eps16_atacada", "eps24_atacada"]

def tex(s):
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ('"', "''")]:
        s = s.replace(a, b)
    return s


def imagen(archivo_img, archivo_repo, opciones):
    """Una imagen que, al hacer clic, abre la captura original en el repositorio."""
    return rf"\href{{\repourl/blob/main/capturas/{archivo_repo}}}{{\includegraphics[{opciones}]{{img/{archivo_img}}}}}"


def grilla(pares, ancho=r"0.48\linewidth"):
    out = []
    for i, (img, repo) in enumerate(pares):
        out.append(imagen(img, repo, f"width={ancho}") + (r"\hfill" if i % 2 == 0 else r"\par\medskip"))
    return r"\begin{center}" + "\n".join(out) + r"\end{center}"


guiones = json.load(open(RAIZ / "guiones/estrategias.json", encoding="utf-8"))["estrategias"]
p = []

# ---------- A. guiones ----------
p.append(r"\phantomsection\label{anexoA}\section*{Anexo A. Los seis guiones}\addcontentsline{toc}{section}{Anexo A}")
p.append("Cada guion se pegó textual, un mensaje por vez, en una conversación nueva.\n")
for g in guiones:
    p.append(rf"\paragraph{{{g['id']} · {tex(g['nombre'])}.}} \textit{{{tex(g['idea'])}}}")
    p.append(r"\begin{enumerate}[itemsep=1pt,topsep=2pt]")
    p += [rf"\item {tex(t)}" for t in g["turnos"]]
    p.append(r"\end{enumerate}")

# ---------- B. ChatGPT web ----------
inicial = json.load(open(RAIZ / "guiones/estrategias.json", encoding="utf-8"))["mensaje_inicial"]
p.append(r"\clearpage\phantomsection\label{anexoB}\section*{Anexo B. Capturas: ChatGPT web (2026)}\addcontentsline{toc}{section}{Anexo B}")
p.append(r"\emph{Chat temporal}, 21/11/2026. Cada guion fue una conversación nueva. Antes del primer mensaje le mandamos "
         rf"\enquote{{{tex(inicial)}}} Cada captura muestra el mensaje que mandamos y la respuesta completa. "
         r"Haciendo clic en una captura se abre la imagen original."
         "\n")
for k, g in enumerate(guiones):
    if k:
        p.append(r"\clearpage")
    p.append(rf"\subsection*{{{g['id']} · {tex(g['nombre'])}}}")
    for n in range(1, len(g["turnos"]) + 1):
        f = f"chatgpt_{g['id']}_t{n}.png"
        # la etiqueta y su captura van juntas en un bloque que no se parte entre páginas
        p.append(r"\par\noindent\begin{minipage}{\linewidth}" + rf"\textbf{{Mensaje {n}}}\par\smallskip\centering"
                 + imagen(f, f, r"width=0.86\linewidth,height=0.40\textheight,keepaspectratio") + r"\end{minipage}\par\bigskip")

p.append(r"\clearpage\subsection*{Prueba con imágenes}")
p.append("Las cuatro caras del meme, cada una original y con $\\varepsilon=8$, 16 y 24. Una imagen por chat temporal, "
         "con la pregunta \\enquote{¿Qué hay en esta imagen? Respondé con una palabra.}\n")
p.append(grilla([(f"vision_chatgpt_{c}_{v}.png", f"vision_chatgpt_{c}_{v}.jpg") for c in CARAS for v in VERSIONES]))

# ---------- C. gpt-4o-mini ----------
p.append(r"\clearpage\phantomsection\label{anexoC}\section*{Anexo C. Capturas: gpt-4o-mini (2024)}\addcontentsline{toc}{section}{Anexo C}")
p.append("Conversaciones con el simulador. Cada imagen es un mensaje: arriba lo que mandamos y debajo la respuesta completa.\n")
for k, g in enumerate(guiones):
    if k:
        p.append(r"\clearpage")
    p.append(rf"\subsection*{{{g['id']} · {tex(g['nombre'])}}}")
    for n in range(1, len(g["turnos"]) + 1):
        f = f"gpt4omini_{g['id']}_r1_t{n}.png"
        p.append(r"\begin{center}" + imagen(f, f, r"width=0.86\linewidth,height=0.80\textheight,keepaspectratio") + r"\end{center}")

p.append(r"\clearpage\subsection*{Prueba con imágenes}")
p.append("Las cuatro caras del meme, cada una original y con $\\varepsilon=8$, 16 y 24. Una imagen por chat, "
         "con la misma pregunta.\n")
p.append(grilla([(f"vision_gpt4omini_{c}_{v}.png", f"vision_gpt4omini_{c}_{v}.jpg")
                 for c in CARAS for v in VERSIONES]))

(RAIZ / "informe" / "anexos.tex").write_text("\n".join(p) + "\n", encoding="utf-8")
print("anexos.tex listo")
