"""
Barrido de sensibilidad: ¿cuánto cambia el puesto de Colombia al variar
MIN_EXPORT (valor mínimo exportado para contar como "competitivo")?
Ejecutar desde la raíz del repo:
    python src/sweep_min_export.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data' / 'BACI_HS92_V202601'
RESULTS_DIR = ROOT / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

YEARS = [2021, 2022, 2023]
MIN_COUNTRY_TOTAL = 1_000_000            # miles de USD
BASKET_PREFIXES = ['8401', '2844', '8109']
THRESHOLDS = [0, 10, 100, 1000, 10000]   # miles de USD por año

# ---------- 1. Cargar datos UNA sola vez ----------
df_countries = pd.read_csv(DATA_DIR / 'country_codes_V202601.csv')
country_map = dict(zip(df_countries['country_code'], df_countries['country_iso3']))

frames = []
for y in YEARS:
    f = DATA_DIR / f'BACI_HS92_Y{y}_V202601.csv'
    print(f'Procesando {f.name}...')
    d = pd.read_csv(f, usecols=['i', 'k', 'v'])
    frames.append(d.groupby(['i', 'k'])['v'].sum())

df_trade = (pd.concat(frames).groupby(level=[0, 1]).sum() / len(YEARS)).reset_index()
df_trade['country'] = df_trade['i'].map(country_map)
df_trade = df_trade.dropna(subset=['country'])

X = df_trade.pivot_table(index='country', columns='k', values='v',
                         aggfunc='sum', fill_value=0.0)
X = X.loc[X.sum(axis=1) > MIN_COUNTRY_TOTAL]
X = X.loc[:, X.sum(axis=0) > 0]

X_vals = X.values
RCA = (X_vals / X_vals.sum(axis=1, keepdims=True)) / (
    X_vals.sum(axis=0, keepdims=True) / X_vals.sum())

cols = list(X.columns)
# zfill(6): evita que 081090 (fruta) se cuele como 81090 en el prefijo 8109
basket = [c for c in cols if str(int(c)).zfill(6).startswith(tuple(BASKET_PREFIXES))]
idxs = [cols.index(c) for c in basket]
i_col = list(X.index).index('COL')


# ---------- 2. Lo que se repite: una función ----------
def densidad(min_export):
    """Devuelve la densidad de cada país hacia la canasta y la de COL hacia todo."""
    M = ((RCA >= 1.0) & (X_vals >= min_export)).astype(int)
    C = M.T @ M
    ubiq = M.sum(axis=0)
    max_ubiq = np.maximum(ubiq[:, None], ubiq[None, :])
    Phi = np.divide(C, max_ubiq, out=np.zeros(C.shape, dtype=float),
                    where=max_ubiq != 0)
    np.fill_diagonal(Phi, 0.0)

    den = Phi[:, idxs].sum(axis=0).astype(float)
    den[den == 0] = np.nan
    omega_basket = pd.DataFrame((M @ Phi[:, idxs]) / den, index=X.index).mean(axis=1)

    den_all = Phi.sum(axis=0).astype(float)
    den_all[den_all == 0] = np.nan
    omega_col_all = (M[i_col] @ Phi) / den_all
    return omega_basket, omega_col_all, ubiq[idxs].sum()


# ---------- 3. El barrido ----------
rows = []
for t in THRESHOLDS:
    om, om_col_all, n_exp = densidad(t)
    val = om['COL']
    rows.append({
        'MIN_EXPORT': t,
        'omega_COL': round(val, 4),
        'puesto_COL': int(om.rank(ascending=False)['COL']),
        'n_paises': len(om.dropna()),
        'percentil_canasta': round(np.nanmean(om_col_all < val) * 100),
        'exportadores_canasta': int(n_exp),
    })

df = pd.DataFrame(rows)
print('\nBarrido de MIN_EXPORT (miles de USD por año):')
print(df.to_string(index=False))
df.to_csv(RESULTS_DIR / 'barrido_min_export.csv', index=False)

# ---------- 4. Figura ----------
fig, ax = plt.subplots(figsize=(6, 4))
pos = range(len(df))
ax.plot(pos, df['puesto_COL'], marker='o')
ax.set_xticks(list(pos))
ax.set_xticklabels(df['MIN_EXPORT'])
ax.invert_yaxis()                      # puesto 1 = mejor, va arriba
ax.set_xlabel('MIN_EXPORT (miles de USD por año)')
ax.set_ylabel(f"Puesto de Colombia (de {int(df['n_paises'].max())})")
ax.set_title('Sensibilidad del puesto de Colombia al umbral')
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(RESULTS_DIR / 'barrido_min_export.png', dpi=200)
print('\nGuardado en results/: barrido_min_export.csv y barrido_min_export.png')
