import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib.pyplot as plt


def add_value_labels(ax, values, is_money=True):
    """
    Pone etiquetas arriba de cada barra.
    - is_money=True => formato con 2 decimales y separador de miles.
    """
    max_val = max(values) if len(values) else 0
    offset = max_val * 0.01

    for i, v in enumerate(values):
        label = f"{v:,.2f}" if is_money else str(v)
        ax.text(
            i,
            v + offset,
            label,
            ha="center",
            va="bottom",
            fontsize=9,
            rotation=0
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
        c.edad,
        v.categoria,
        v.precio,
        v.cantidad,
        v.total,
        v.region_envio
        FROM ventas v
    JOIN clientes c ON c.id_cliente = v.id_cliente;
"""
df = pd.read_sql(query, engine)


for col in ["edad", "precio", "cantidad", "total"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")


numericas = ["edad", "precio", "cantidad", "total"]
rows = []
for col in numericas:
    s = df[col].dropna()
    moda = s.mode()
    rows.append({
        "Variable": col,
        "Media": s.mean(),
        "Mediana": s.median(),
        "Moda": moda.iloc[0] if len(moda) else None
    })

stats_df = pd.DataFrame(rows)

fig, ax = plt.subplots()
ax.axis("off")
tabla = ax.table(
    cellText=stats_df.round(2).values,
    colLabels=stats_df.columns,
    cellLoc="center",
    loc="center"
)
tabla.auto_set_font_size(False)
tabla.set_fontsize(10)
tabla.scale(1, 1.3)
plt.title("Estadísticas básicas (media, mediana, moda)")
plt.tight_layout()
plt.savefig("tabla_estadisticas.png", dpi=200)
plt.close()


plt.figure()
plt.hist(df["total"].dropna(), bins=20)
plt.title("Distribución del total de la orden")
plt.xlabel("Total")
plt.ylabel("Frecuencia")
plt.tight_layout()
plt.savefig("hist_total.png", dpi=200)
plt.close()


cat = df.groupby("categoria")["total"].sum().sort_values(ascending=False)

fig, ax = plt.subplots()
ax.bar(cat.index.astype(str), cat.values)
ax.set_title("Ventas (ingreso) por categoría")
ax.set_xlabel("Categoría")
ax.set_ylabel("Suma de total")
ax.tick_params(axis="x", rotation=45)

add_value_labels(ax, cat.values, is_money=True)

plt.tight_layout()
plt.savefig("ventas_por_categoria.png", dpi=200)
plt.close()


reg = df.groupby("region_envio")["total"].sum().sort_values(ascending=False)

fig, ax = plt.subplots()
ax.bar(reg.index.astype(str), reg.values)
ax.set_title("Ventas (ingreso) por región")
ax.set_xlabel("Región")
ax.set_ylabel("Suma de total")
ax.tick_params(axis="x", rotation=45)

add_value_labels(ax, reg.values, is_money=True)

plt.tight_layout()
plt.savefig("ventas_por_region.png", dpi=200)
plt.close()

print("Se han generado las siguientes imagenes:")
print("1) tabla_estadisticas.png")
print("2) hist_total.png")
print("3) ventas_por_categoria.png (con valores)")
print("4) ventas_por_region.png (con valores)")