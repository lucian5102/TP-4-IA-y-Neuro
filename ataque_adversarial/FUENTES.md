# Fuentes de las imágenes y referencias

## Las imágenes

Las casillas de `fuentes/` salen de la grilla "chihuahua o muffin" de Karen Zack (@teenybiscuit, 2016), el meme que inspira esta parte del trabajo. Las usamos con fines académicos y citando la fuente; los derechos son de su autora.

La grilla original tiene 4 filas y 4 columnas; guardamos sólo las casillas que usamos, con el nombre `casilla_f{fila}c{columna}.png`:

| Uso | Casillas |
|---|---|
| Caras de chihuahua (las que atacamos) | `f1c2`, `f2c1`, `f2c3`, `f3c2` |
| Muffins de arándanos (el objetivo del ataque) | `f1c1`, `f1c3`, `f2c2`, `f2c4`, `f3c1`, `f3c3`, `f4c4` |

## Referencias

- **El meme**: Karen Zack (@teenybiscuit), 2016.
- **Paper que usa el meme como caso de estudio**: Togootogtokh, E. y Amartuvshin, A. (2018). *Deep Learning Approach for Very Similar Objects Recognition Application on Chihuahua and Muffin Problem*. https://arxiv.org/abs/1801.09573
- **El ataque que seguimos** (transferencia con varios modelos CLIP y recortes aleatorios): Li, Z. et al. (2025). *A Frustratingly Simple Yet Highly Effective Attack Baseline: Over 90% Success Rate Against the Strong Black-box Models of GPT-4.5/4o/o1*. https://arxiv.org/abs/2503.10635
- **Origen de los ejemplos adversariales**: Szegedy, C. et al. (2014). *Intriguing properties of neural networks*. ICLR. https://arxiv.org/abs/1312.6199
