"""
Densidad del product space de cada país hacia una canasta de productos
del ciclo nuclear (HS92), usando datos de comercio BACI (CEPII).

Método: exportaciones -> RCA (Balassa) -> matriz binaria M -> proximidad Phi
-> densidad omega. Ejecutar desde la raíz del repo:
    python src/product_space_nuclear.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

# ============ 0. PARÁMETROS ============
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data' / 'BACI_HS92_V202601'
RESULTS_DIR = ROOT / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

YEARS = [2021, 2022, 2023]          # años que se promedian
MIN_EXPORT = 100                    # miles de USD por año
MIN_COUNTRY_TOTAL = 1_000_000       # miles de USD (= USD 1.000 millones)
BASKET_PREFIXES = ['8401', '2844', '8109']   # uranio, circonio, reactores
CHECK_COUNTRIES = ['RUS', 'KOR', 'CAN', 'IND', 'ARG', 'BRA']

# ============ 1. Diccionarios ============
print('Cargando diccionarios de países y productos...')
df_countries = pd.read_csv(DATA_DIR / 'country_codes_V202601.csv')
df_products = pd.read_csv(DATA_DIR / 'product_codes_HS92_V202601.csv')

df_products['code'] = pd.to_numeric(df_products['code'], errors='coerce')
df_products = df_products.dropna(subset=['code'])
df_products['code'] = df_products['code'].astype(int)

country_map = dict(zip(df_countries['country_code'], df_countries['country_iso3']))
product_map = dict(zip(df_products['code'], df_products['description']))

# ============ 2. Cargar varios años y promediar ============
frames = []
for y in YEARS:
    f = DATA_DIR / f'BACI_HS92_Y{y}_V202601.csv'
    print(f'Procesando {f.name}...')
    d = pd.read_csv(f, usecols=['i', 'k', 'v'])   # i=exportador, k=producto, v=miles USD
    frames.append(d.groupby(['i', 'k'])['v'].sum())

df_trade = (pd.concat(frames).groupby(level=[0, 1]).sum() / len(YEARS)).reset_index()
df_trade['country'] = df_trade['i'].map(country_map)
df_trade = df_trade.dropna(subset=['country'])

# ============ 3. Matriz País x Producto ============
print('Construyendo matriz de exportaciones...')
X = df_trade.pivot_table(index='country', columns='k', values='v',
                         aggfunc='sum', fill_value=0.0)
X = X.loc[X.sum(axis=1) > MIN_COUNTRY_TOTAL]
X = X.loc[:, X.sum(axis=0) > 0]
print(f'Matriz limpia: {X.shape[0]} países x {X.shape[1]} productos')

# ============ 4. RCA + umbral mínimo ============
X_vals = X.values
country_totals = X_vals.sum(axis=1, keepdims=True)
product_totals = X_vals.sum(axis=0, keepdims=True)
world_total = X_vals.sum()

RCA = (X_vals / country_totals) / (product_totals / world_total)
M = ((RCA >= 1.0) & (X_vals >= MIN_EXPORT)).astype(int)

# ============ 5. Proximidad entre productos (Phi) ============
print('Calculando la red de proximidades...')
C = M.T @ M
ubiq = M.sum(axis=0)
max_ubiq = np.maximum(ubiq[:, None], ubiq[None, :])
Phi = np.divide(C, max_ubiq, out=np.zeros(C.shape, dtype=float), where=max_ubiq != 0)
np.fill_diagonal(Phi, 0.0)

# ============ 6. Canasta nuclear ============
cols = list(X.columns)
# zfill(6): los códigos HS pierden el cero inicial al leerse como número
# (081090 -> 81090), y se colaría una fruta en la canasta del circonio.
basket = [c for c in cols if str(int(c)).zfill(6).startswith(tuple(BASKET_PREFIXES))]
idxs = [cols.index(c) for c in basket]

print('\nCanasta nuclear (verifica que sean los productos que quieres):')
for c, j in zip(basket, idxs):
    print(f'  {c} | exportadores competitivos: {ubiq[j]:3d} | {str(product_map.get(c, "?"))[:70]}')

den = Phi[:, idxs].sum(axis=0).astype(float)
den[den == 0] = np.nan
Omega = pd.DataFrame((M @ Phi[:, idxs]) / den, index=X.index, columns=basket)
omega_basket = Omega.mean(axis=1)

print('\nTop 10 países por densidad hacia la canasta nuclear:')
print(omega_basket.sort_values(ascending=False).head(10).round(3))

ranks = omega_basket.rank(ascending=False)
print('\nPuesto de países de control (NaN = no está en la matriz):')
print(ranks.reindex(CHECK_COUNTRIES))

omega_basket.sort_values(ascending=False).to_csv(
    RESULTS_DIR / 'densidad_por_pais.csv', header=['omega'])

# ============ 7. Colombia ============
if 'COL' in X.index:
    i_col = list(X.index).index('COL')
    val = omega_basket['COL']
    rank = int(ranks['COL'])
    print(f'\n>>> Densidad de COL hacia la canasta nuclear: {val:.4f}')
    print(f'>>> Puesto {rank} de {len(omega_basket)} países')

    den_all = Phi.sum(axis=0).astype(float)
    den_all[den_all == 0] = np.nan
    omega_col_all = (M[i_col] @ Phi) / den_all
    pct = np.nanmean(omega_col_all < val) * 100
    print(f'>>> Promedio de COL hacia cualquier producto: {np.nanmean(omega_col_all):.4f}')
    print(f'>>> La canasta nuclear está en el percentil {pct:.0f} de los productos de Colombia')

    print('\nDensidad de COL por código de la canasta:')
    print(Omega.loc['COL'].round(4).to_string())
    Omega.loc['COL'].round(4).to_csv(
        RESULTS_DIR / 'densidad_col_por_codigo.csv', header=['omega'])
else:
    print("No se encontró 'COL' en la lista de países.")
