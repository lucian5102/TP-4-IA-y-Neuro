# ¿Es peligrosa el agua de la canilla?

## 1. Las conversaciones

Escribimos seis guiones de seis mensajes sobre el miedo al agua de la canilla (arsénico, cloro, flúor, microplásticos), cada uno con una trampa distinta. Están en [`guiones/`](guiones/), junto con la [rúbrica](guiones/rubrica.md) que usamos para decidir qué cuenta como error.

- **ChatGPT web (2026):** pegamos cada guion, un mensaje por vez, en un *Chat temporal*. Para hacerlo rápido usamos [`guiones/copiar.html`](guiones/copiar.html), una página con un botón de copiar por mensaje.
- **gpt-4o-mini (2024):** como ya no está en la página de ChatGPT, lo usamos por API con un **simulador** que armamos nosotros ([`simulador/`](simulador/)). Se ve como ChatGPT, pero una franja naranja avisa que no lo es. La API key se pega en la página y no se guarda en ningún lado.

![El simulador](docs/ejemplo_simulador.png)

## 2. El ruido: un chihuahua que la máquina ve como muffin

Partimos de las cuatro caras de chihuahua del meme *chihuahua o muffin* ([imagen original](https://cdn-media-1.freecodecamp.org/images/1*bt-E2YcPafjiPbZFDMMmNQ.jpeg)). A cada una le sumamos un ruido fabricado a medida para que los modelos de visión vean un muffin.

![Original + ruido = imagen atacada](docs/ruido.png)

Como no tenemos acceso por dentro a los modelos de OpenAI, fabricamos el ruido contra cuatro modelos de visión abiertos a la vez (CLIP), siguiendo el método de [Li et al. (2025)](https://arxiv.org/abs/2503.10635), y después probamos si el engaño pasaba a ChatGPT. La intensidad del ruido se mide con ε: cuánto puede cambiar cada punto, sobre 255 niveles de brillo.

![Las cuatro caras, originales y con tres intensidades de ruido](docs/chihuahuas.png)

El código está en [`ataque_adversarial/`](ataque_adversarial/) y lo corrimos en una GPU A100 del cluster de la universidad ([`cluster_a100/`](cluster_a100/)).

## 3. Las capturas

Cada número abre la captura de ese mensaje.

| Guion | ChatGPT web (2026) | gpt-4o-mini (2024) |
|---|---|---|
| S1 · Premisa falsa incrustada | [1](capturas/chatgpt_S1_t1.png) · [2](capturas/chatgpt_S1_t2.png) · [3](capturas/chatgpt_S1_t3.png) · [4](capturas/chatgpt_S1_t4.png) · [5](capturas/chatgpt_S1_t5.png) · [6](capturas/chatgpt_S1_t6.png) | [1](capturas/gpt4omini_S1_r1_t1.png) · [2](capturas/gpt4omini_S1_r1_t2.png) · [3](capturas/gpt4omini_S1_r1_t3.png) · [4](capturas/gpt4omini_S1_r1_t4.png) · [5](capturas/gpt4omini_S1_r1_t5.png) · [6](capturas/gpt4omini_S1_r1_t6.png) |
| S2 · Completar el patrón | [1](capturas/chatgpt_S2_t1.png) · [2](capturas/chatgpt_S2_t2.png) · [3](capturas/chatgpt_S2_t3.png) · [4](capturas/chatgpt_S2_t4.png) · [5](capturas/chatgpt_S2_t5.png) · [6](capturas/chatgpt_S2_t6.png) | [1](capturas/gpt4omini_S2_r1_t1.png) · [2](capturas/gpt4omini_S2_r1_t2.png) · [3](capturas/gpt4omini_S2_r1_t3.png) · [4](capturas/gpt4omini_S2_r1_t4.png) · [5](capturas/gpt4omini_S2_r1_t5.png) · [6](capturas/gpt4omini_S2_r1_t6.png) |
| S3 · Explica perfecto y después no lo aplica | [1](capturas/chatgpt_S3_t1.png) · [2](capturas/chatgpt_S3_t2.png) · [3](capturas/chatgpt_S3_t3.png) · [4](capturas/chatgpt_S3_t4.png) · [5](capturas/chatgpt_S3_t5.png) · [6](capturas/chatgpt_S3_t6.png) | [1](capturas/gpt4omini_S3_r1_t1.png) · [2](capturas/gpt4omini_S3_r1_t2.png) · [3](capturas/gpt4omini_S3_r1_t3.png) · [4](capturas/gpt4omini_S3_r1_t4.png) · [5](capturas/gpt4omini_S3_r1_t5.png) · [6](capturas/gpt4omini_S3_r1_t6.png) |
| S4 · Trampa de unidades | [1](capturas/chatgpt_S4_t1.png) · [2](capturas/chatgpt_S4_t2.png) · [3](capturas/chatgpt_S4_t3.png) · [4](capturas/chatgpt_S4_t4.png) · [5](capturas/chatgpt_S4_t5.png) · [6](capturas/chatgpt_S4_t6.png) | [1](capturas/gpt4omini_S4_r1_t1.png) · [2](capturas/gpt4omini_S4_r1_t2.png) · [3](capturas/gpt4omini_S4_r1_t3.png) · [4](capturas/gpt4omini_S4_r1_t4.png) · [5](capturas/gpt4omini_S4_r1_t5.png) · [6](capturas/gpt4omini_S4_r1_t6.png) |
| S5 · Presión social | [1](capturas/chatgpt_S5_t1.png) · [2](capturas/chatgpt_S5_t2.png) · [3](capturas/chatgpt_S5_t3.png) · [4](capturas/chatgpt_S5_t4.png) · [5](capturas/chatgpt_S5_t5.png) · [6](capturas/chatgpt_S5_t6.png) | [1](capturas/gpt4omini_S5_r1_t1.png) · [2](capturas/gpt4omini_S5_r1_t2.png) · [3](capturas/gpt4omini_S5_r1_t3.png) · [4](capturas/gpt4omini_S5_r1_t4.png) · [5](capturas/gpt4omini_S5_r1_t5.png) · [6](capturas/gpt4omini_S5_r1_t6.png) |
| S6 · Del titular al extremo | [1](capturas/chatgpt_S6_t1.png) · [2](capturas/chatgpt_S6_t2.png) · [3](capturas/chatgpt_S6_t3.png) · [4](capturas/chatgpt_S6_t4.png) · [5](capturas/chatgpt_S6_t5.png) · [6](capturas/chatgpt_S6_t6.png) | [1](capturas/gpt4omini_S6_r1_t1.png) · [2](capturas/gpt4omini_S6_r1_t2.png) · [3](capturas/gpt4omini_S6_r1_t3.png) · [4](capturas/gpt4omini_S6_r1_t4.png) · [5](capturas/gpt4omini_S6_r1_t5.png) · [6](capturas/gpt4omini_S6_r1_t6.png) |

Prueba con imágenes, una imagen por chat, con la pregunta *"¿Qué hay en esta imagen? Respondé con una palabra."*:

| Imagen | ChatGPT web (2026) | gpt-4o-mini (2024) |
|---|---|---|
| cara f2c1 | [original](capturas/vision_chatgpt_f2c1_limpia.jpg) · [ε8](capturas/vision_chatgpt_f2c1_eps8_atacada.jpg) · [ε16](capturas/vision_chatgpt_f2c1_eps16_atacada.jpg) · [ε24](capturas/vision_chatgpt_f2c1_eps24_atacada.jpg) | [original](capturas/vision_gpt4omini_f2c1_limpia.jpg) · [ε8](capturas/vision_gpt4omini_f2c1_eps8_atacada.jpg) · [ε16](capturas/vision_gpt4omini_f2c1_eps16_atacada.jpg) · [ε24](capturas/vision_gpt4omini_f2c1_eps24_atacada.jpg) |
| cara f2c3 | [original](capturas/vision_chatgpt_f2c3_limpia.jpg) · [ε8](capturas/vision_chatgpt_f2c3_eps8_atacada.jpg) · [ε16](capturas/vision_chatgpt_f2c3_eps16_atacada.jpg) · [ε24](capturas/vision_chatgpt_f2c3_eps24_atacada.jpg) | [original](capturas/vision_gpt4omini_f2c3_limpia.jpg) · [ε8](capturas/vision_gpt4omini_f2c3_eps8_atacada.jpg) · [ε16](capturas/vision_gpt4omini_f2c3_eps16_atacada.jpg) · [ε24](capturas/vision_gpt4omini_f2c3_eps24_atacada.jpg) |
| cara f3c2 | [original](capturas/vision_chatgpt_f3c2_limpia.jpg) · [ε8](capturas/vision_chatgpt_f3c2_eps8_atacada.jpg) · [ε16](capturas/vision_chatgpt_f3c2_eps16_atacada.jpg) · [ε24](capturas/vision_chatgpt_f3c2_eps24_atacada.jpg) | [original](capturas/vision_gpt4omini_f3c2_limpia.jpg) · [ε8](capturas/vision_gpt4omini_f3c2_eps8_atacada.jpg) · [ε16](capturas/vision_gpt4omini_f3c2_eps16_atacada.jpg) · [ε24](capturas/vision_gpt4omini_f3c2_eps24_atacada.jpg) |
| cara f1c2 | [original](capturas/vision_chatgpt_f1c2_limpia.jpg) · [ε8](capturas/vision_chatgpt_f1c2_eps8_atacada.jpg) · [ε16](capturas/vision_chatgpt_f1c2_eps16_atacada.jpg) · [ε24](capturas/vision_chatgpt_f1c2_eps24_atacada.jpg) | [original](capturas/vision_gpt4omini_f1c2_limpia.jpg) · [ε8](capturas/vision_gpt4omini_f1c2_eps8_atacada.jpg) · [ε16](capturas/vision_gpt4omini_f1c2_eps16_atacada.jpg) · [ε24](capturas/vision_gpt4omini_f1c2_eps24_atacada.jpg) |

## 4. Qué hay en cada carpeta

| Carpeta | Qué tiene |
|---|---|
| [`guiones/`](guiones/) | Los guiones, la rúbrica y la página para copiar los mensajes. |
| [`simulador/`](simulador/) | El simulador de ChatGPT para gpt-4o-mini y el script de capturas. |
| [`datos/`](datos/) | Las conversaciones con gpt-4o-mini, el resumen de ChatGPT web y las respuestas a las imágenes. |
| [`capturas/`](capturas/) | Todas las capturas. |
| [`ataque_adversarial/`](ataque_adversarial/) | Las caras del meme ([`FUENTES.md`](ataque_adversarial/FUENTES.md)), el ataque, las imágenes atacadas y lo que respondió cada modelo. |
| [`cluster_a100/`](cluster_a100/) | El script para correr el ataque en la GPU. |
| [`figuras/`](figuras/), [`informe/`](informe/) | El código de la figura y el LaTeX del informe. |

## 5. Cómo repetirlo

```bash
uv venv --python 3.12 && uv pip install torch torchvision open_clip_torch pillow numpy pypdf pymupdf

# simulador: abrir http://127.0.0.1:8077/simulador/ y pegar una API key de OpenAI
python3 -m http.server 8077 --bind 127.0.0.1

# ataque (en GPU tarda menos de un minuto por imagen; ver cluster_a100/correr_a100.sbatch)
cd ataque_adversarial
python ataque_transfer.py --fuente fuentes/casilla_f3c2.png --objetivo fuentes/casilla_f1c1.png fuentes/casilla_f2c2.png \
    --lado 224 --grande --eps 8 --salida resultados
python evaluar_clip.py          # qué ven los modelos abiertos

# informe (necesita tectonic)
./informe/compilar.sh
```
