#!/bin/bash
#SBATCH --job-name=tp4-ataque
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%j.out
# Ajustar --partition / --account / --gres (por ejemplo gpu:a100:1) según el cluster.

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source .venv/bin/activate

{ date; hostname; nvidia-smi; python -c "import torch, open_clip; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0)); print('open_clip', open_clip.__version__)"; } > entorno.txt 2>&1

OBJ=(fuentes/casilla_f1c1.png fuentes/casilla_f1c3.png fuentes/casilla_f2c2.png fuentes/casilla_f2c4.png fuentes/casilla_f3c1.png fuentes/casilla_f3c3.png fuentes/casilla_f4c4.png)
for c in f2c1 f2c3 f3c2 f1c2; do
  for e in 8 16 24; do
    python ataque_transfer.py --fuente fuentes/casilla_$c.png --objetivo "${OBJ[@]}" \
      --lado 224 --grande --eps $e --pasos 400 --salida resultados
  done
done
python evaluar_clip.py resultados respuestas_clip.csv
echo LISTO
