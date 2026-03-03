import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine


OUTPUT_DIR = "img-4"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def savefig(filename):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=200)
    plt.close()

load_dotenv()
engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


query = """
    SELECT
        v.total,
        v.cantidad,
        c.edad,
        c.genero,
        v.nombre_producto as producto,
        v.precio
    FROM ventas v
    JOIN clientes c ON v.id_cliente = c.id_cliente;
"""

df = pd.read_sql(query, engine)

# ==============================
# 4.a) SEGMENTACIÓN POR EDAD
# ==============================

ventas_producto_edad = df.groupby(["producto", "edad"]).agg(
    cantidad_total=("cantidad", "sum"),
    monto_total=("total", "sum")
).reset_index()

# Elegir la edad con más cantidad por producto
idx = ventas_producto_edad.groupby("producto")["cantidad_total"].idxmax()
top_edad_por_producto = ventas_producto_edad.loc[idx].reset_index(drop=True)

#print(top_edad_por_producto)

# Definir rangos de edad
bins = [0, 18, 25, 35, 45, 60, 100]
labels = ["0-18", "19-25", "26-35", "36-45", "46-60", "60+"]
df["rango_edad"] = pd.cut(df["edad"], bins=bins, labels=labels)

ventas_producto_edad = df.groupby(["producto", "edad"]).agg(
    cantidad_total=("cantidad", "sum"),
    monto_total=("total", "sum"),
    precio_unitario_promedio=("precio", "mean")
).reset_index()

idx = ventas_producto_edad.groupby("producto")["cantidad_total"].idxmax()
top_edad_por_producto = ventas_producto_edad.loc[idx].reset_index(drop=True)

# Mapear la edad top al rango correspondiente
top_edad_por_producto["rango_edad_top"] = pd.cut(
    top_edad_por_producto["edad"],
    bins=bins,
    labels=labels
)

# Total de ventas por producto
total_por_producto = df.groupby("producto")["total"].sum().reset_index()
total_por_producto.rename(columns={"total": "total_producto"}, inplace=True)

# Combinar
top_edad_por_producto = top_edad_por_producto.merge(total_por_producto, on="producto")
top_edad_por_producto["%_del_producto"] = (
    top_edad_por_producto["monto_total"] / top_edad_por_producto["total_producto"] * 100
)

resumen_final = top_edad_por_producto[[
    "producto",
    "rango_edad_top",
    "cantidad_total",
    "monto_total",
    "precio_unitario_promedio",
    "%_del_producto"
]].sort_values("producto").reset_index(drop=True)

# print(resumen_final)


# Graficar 
x = resumen_final["producto"]
y = resumen_final["cantidad_total"]
colores = resumen_final["rango_edad_top"].map({
    "0-18": "skyblue",
    "19-25": "green",
    "26-35": "orange",
    "36-45": "purple",
    "46-60": "red",
    "60+": "brown"
})  

# Crear gráfica
plt.figure(figsize=(14,7))
plt.bar(x, y, color=colores)
plt.xticks(rotation=45, ha="right")
plt.ylabel("Cantidad Total Vendida")
plt.title("Productos y sus principales rangos de edad compradores")

# Leyenda manual
rangos = ["0-18","19-25","26-35","36-45","46-60","60+"]
colores_leg = ["skyblue","green","orange","purple","red","brown"]
patches = [mpatches.Patch(color=c, label=r) for r,c in zip(rangos,colores_leg)]
plt.legend(handles=patches, title="Rango de Edad Top")

# Guardar en PNG
savefig("ventas_por_edad.png")


# Agrupar por rango de edad sumando el monto total
poder_compra_total = df.groupby("rango_edad").agg(
    monto_total=("total", "sum"),
    cantidad_total=("cantidad", "sum")
).reset_index()

# Ordenar los rangos de edad
poder_compra_total["rango_edad"] = pd.Categorical(
    poder_compra_total["rango_edad"], categories=labels, ordered=True
)
poder_compra_total = poder_compra_total.sort_values("rango_edad")


# Datos para la gráfica de pie
labels = poder_compra_total["rango_edad"]
sizes = poder_compra_total["monto_total"]

# Crear pie chart
plt.figure(figsize=(8,8))
plt.pie(
    sizes,
    labels=labels,
    autopct="%1.1f%%",  
    startangle=90,      
    colors=["skyblue","lightgreen","orange","purple","red","brown"]
)
plt.title("Poder de compra por rango de edad")
savefig("poder_compra_edad.png")


# ==============================
# 4.a) COMPARACIÓN POR GÉNERO
# ==============================
# Agrupar por producto y género sumando la cantidad
ventas_genero = df.groupby(["producto", "genero"]).agg(
    cantidad_total=("cantidad", "sum")
).reset_index()

# Separar columnas por género
ventas_genero_pivot = ventas_genero.pivot_table(
    index="producto",
    columns="genero",
    values="cantidad_total",
    fill_value=0  
).reset_index()

ventas_genero_pivot = ventas_genero_pivot.rename(columns={
    "Femenino": "Cantidad_Mujeres",
    "Masculino": "Cantidad_Hombres"
})

print(ventas_genero_pivot)

# Datos para la gráfica
productos = ventas_genero_pivot["producto"]
cantidad_mujeres = ventas_genero_pivot["Cantidad_Mujeres"]
cantidad_hombres = ventas_genero_pivot["Cantidad_Hombres"]

# Posición de las barras
x = np.arange(len(productos))
width = 0.35  # ancho de cada barra

# Crear la gráfica
plt.figure(figsize=(14,7))
plt.bar(x - width/2, cantidad_mujeres, width, label="Mujeres", color="pink")
plt.bar(x + width/2, cantidad_hombres, width, label="Hombres", color="skyblue")

# Configuración de ejes y etiquetas
plt.xticks(x, productos, rotation=45, ha="right")
plt.ylabel("Cantidad Total Comprada")
plt.title("Comparación de cantidades compradas por género y producto")
plt.legend()
plt.tight_layout()

savefig("ventas_por_genero_producto.png")