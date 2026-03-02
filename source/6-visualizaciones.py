import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib.pyplot as plt


OUTPUT_DIR = "img-6"  
os.makedirs(OUTPUT_DIR, exist_ok=True)

def savefig(filename: str):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=200)
    plt.close()

def add_chart_type_label(ax, chart_type: str):
    """Etiqueta pequeña dentro del gráfico indicando el tipo de gráfica."""
    ax.text(
        0.98, 0.02, f"Tipo: {chart_type}",
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.25", alpha=0.2)
    )


load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

query = """
    SELECT
        v.id_orden,
        v.fecha_compra,
        v.id_cliente,
        c.genero,
        v.categoria,
        v.precio,
        v.cantidad,
        v.total
    FROM ventas v
    JOIN clientes c ON c.id_cliente = v.id_cliente;
"""
df = pd.read_sql(query, engine)


df["fecha_compra"] = pd.to_datetime(df["fecha_compra"], errors="coerce")
df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
df["total"] = pd.to_numeric(df["total"], errors="coerce")

df["genero"] = df["genero"].fillna("Sin dato")
df.loc[df["genero"].astype(str).str.strip() == "", "genero"] = "Sin dato"

# ==========================================================
# iv. Cantidad de productos por rango de precios y categoría
# ==========================================================
bins = [0, 50, 100, 150, 200, 10**9]
labels = ["0-50", "50-100", "100-150", "150-200", "200+"]

df_prices = df.dropna(subset=["precio", "cantidad", "categoria"]).copy()
df_prices["rango_precio"] = pd.cut(df_prices["precio"], bins=bins, labels=labels, right=False)

tabla_rangos = (
    df_prices.groupby(["categoria", "rango_precio"])["cantidad"]
    .sum()
    .unstack(fill_value=0)
)

fig, ax = plt.subplots()
tabla_rangos.plot(kind="bar", stacked=True, ax=ax)
ax.set_title("Unidades vendidas por rango de precio y categoría")
ax.set_xlabel("Categoría")
ax.set_ylabel("Unidades (SUM(cantidad))")
ax.tick_params(axis="x", rotation=45)
add_chart_type_label(ax, "Barras apiladas")
savefig("p6_unidades_rango_precio_categoria.png")

# ==========================================================
# v. Cantidad de ventas realizadas por género y mes
# ==========================================================
df_month = df.dropna(subset=["fecha_compra"]).copy()
df_month["mes"] = df_month["fecha_compra"].dt.to_period("M").astype(str)

ventas_genero_mes = (
    df_month.groupby(["mes", "genero"])["id_orden"]
    .nunique()
    .unstack(fill_value=0)
    .sort_index()
)

fig, ax = plt.subplots()

for genero in ventas_genero_mes.columns:
    ax.plot(ventas_genero_mes.index, ventas_genero_mes[genero].values, marker="o", label=str(genero))

ax.set_title("Cantidad de ventas (órdenes) por género y mes")
ax.set_xlabel("Mes")
ax.set_ylabel("Número de órdenes")
ax.tick_params(axis="x", rotation=45)
ax.legend(title="Género", fontsize=8)

add_chart_type_label(ax, "Líneas")
savefig("p6_ventas_genero_mes.png")


print("Se generaron las graficas 4 y 5:", OUTPUT_DIR)
print("4) p6_unidades_rango_precio_categoria.png")
print("5) p6_ventas_genero_mes.png")
