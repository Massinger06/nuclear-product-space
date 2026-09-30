# Product space y cercanía a la cadena nuclear

Exploración de qué tan cerca están las capacidades exportadoras de un país
(Colombia como caso) de un conjunto de productos del ciclo nuclear, usando
la metodología del *product space*.

## Pregunta
¿Qué tan cerca está Colombia, en términos de capacidades exportadoras,
de productos como uranio, circonio y reactores nucleares (HS92)?

## Datos
BACI (CEPII), HS92 V202601, promedio 2021-2023. No se incluyen en el repo;
ver `data/README.md`.

## Método
1. **RCA** (ventaja comparativa revelada, Balassa): un país es "competitivo"
   en un producto si su peso en las exportaciones del país supera su peso mundial.
2. **Proximidad**: dos productos son cercanos si los mismos países los exportan.
3. **Densidad**: fracción de los productos vecinos de uno objetivo que el país ya exporta.

Canasta nuclear: capítulos 2844 (uranio y radiactivos), 8109 (circonio) y 8401 (reactores).

## Resultados preliminares
- Colombia: densidad 0.072, puesto 73 de 164 países.
- Su promedio hacia cualquier producto es 0.090; la canasta nuclear queda
  en el percentil 20 de sus productos.
- *Pendiente:* sensibilidad al umbral `MIN_EXPORT`.

## Limitaciones
- La densidad parece medir sobre todo **diversificación industrial**: el top
  lo lideran economías diversificadas (DEU, ITA, FRA, CHN...).
- Pocos países exportan estos productos (3 a 10), así que la proximidad es ruidosa.
- BACI es a nivel de país, no de departamento.
- Mide cercanía de capacidades exportadoras, **no** la viabilidad de una planta nuclear.

## Cómo reproducir
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python src/product_space_nuclear.py
