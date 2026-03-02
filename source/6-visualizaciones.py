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


# ==========================================================
# 3e. CANTIDAD DE VENTAS POR MÉTODO DE PAGO Y CATEGORÍA
# ==========================================================
# Consulta SQL
query_pago_categoria = """
    SELECT
        v.metodo_pago,
        v.categoria,
        COUNT(*) as cantidad_ventas
    FROM ventas v
    GROUP BY v.metodo_pago, v.categoria
    ORDER BY v.metodo_pago, cantidad_ventas DESC;
"""
df_pago_categoria = pd.read_sql(query_pago_categoria, engine)



fig, ax = plt.subplots(figsize=(12, 6))

categorias = df_pago_categoria['categoria'].unique()
metodos_pago = df_pago_categoria['metodo_pago'].unique()

x = range(len(metodos_pago))
ancho_barra = 0.15
colores = plt.cm.Set3(range(len(categorias)))

for i, categoria in enumerate(categorias):
    datos_categoria = df_pago_categoria[df_pago_categoria['categoria'] == categoria]
    valores = []
    for metodo in metodos_pago:
        valor = datos_categoria[datos_categoria['metodo_pago'] == metodo]['cantidad_ventas'].values
        valores.append(valor[0] if len(valor) > 0 else 0)
    
    posiciones = [p + i * ancho_barra for p in x]
    ax.bar(posiciones, valores, ancho_barra, label=categoria, color=colores[i], alpha=0.8)

ax.set_xlabel('Método de Pago')
ax.set_ylabel('Cantidad de Ventas')
ax.set_title('Ventas por Método de Pago y Categoría')
ax.set_xticks([p + ancho_barra * (len(categorias) - 1) / 2 for p in x])
ax.set_xticklabels(metodos_pago)
ax.legend(title='Categoría', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
savefig("ventas_por_pago_categoria.png")
print(f"6. ventas_por_pago_categoria.png \n")