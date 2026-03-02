import os
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Configuracion bd
OUTPUT_DIR = "img-3"
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
        v.fecha_compra,
        v.categoria,
        v.nombre_producto,
        v.cantidad,
        v.total
    FROM ventas v
    ORDER BY v.fecha_compra;
"""
df = pd.read_sql(query, engine)

df["fecha_compra"] = pd.to_datetime(df["fecha_compra"])
df["mes"] = df["fecha_compra"].dt.to_period("M").astype(str)

# 3a. MESES ORDENADOS POR VENTAS (TODOS)
ventas_mes = df.groupby("mes")["total"].sum().reset_index()
ventas_mes = ventas_mes.sort_values("total", ascending=False)

print("\n" + "="*60)
print("3a. MESES ORDENADOS POR VENTAS (DE MAYOR A MENOR)")
print("="*60)

print("\nTODOS LOS MESES ORDENADOS DE MAYOR A MENOR VENTA:")
for idx, row in ventas_mes.iterrows():
    print(f"  {idx+1:2d}. {row['mes']}: ${row['total']:,.2f}")

# Ventas menor a mayor
ventas_mes_asc = ventas_mes.sort_values("total", ascending=True)
print("\n" + "="*60)
print("MESES ORDENADOS POR VENTAS (DE MENOR A MAYOR)")
print("="*60)
for idx, row in ventas_mes_asc.iterrows():
    print(f"  {idx+1:2d}. {row['mes']}: ${row['total']:,.2f}")

# Gráfico de barras horizontales con todos los meses
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))

# Gráfico de mayor a menor
ax1.barh(ventas_mes["mes"], ventas_mes["total"], color='green', alpha=0.7)
ax1.set_title('Meses Ordenados de Mayor a Menor Venta')
ax1.set_xlabel('Total Ventas ($)')
ax1.invert_yaxis()

# Gráfico de menor a mayor
ax2.barh(ventas_mes_asc["mes"], ventas_mes_asc["total"], color='red', alpha=0.7)
ax2.set_title('Meses Ordenados de Menor a Mayor Venta')
ax2.set_xlabel('Total Ventas ($)')
ax2.invert_yaxis()

plt.tight_layout()
savefig("ventas_meses.png")
print(f"\nGrafico guardado: ventas_meses.png")

# 3b. PRODUCTOS ORDENADOS POR VENTAS (TODOS)
productos_vendidos = df.groupby(["categoria", "nombre_producto"])["cantidad"].sum().reset_index()

# Ordenar de mayor a menor
productos_mayor_menor = productos_vendidos.sort_values("cantidad", ascending=False)

# Ordenar de menor a mayor
productos_sin_cero = productos_vendidos[productos_vendidos["cantidad"] > 0]
productos_menor_mayor = productos_sin_cero.sort_values("cantidad", ascending=True)

print("\n" + "="*60)
print("3b. PRODUCTOS ORDENADOS POR VENTAS (TODOS)")
print("="*60)

print("\nPRODUCTOS ORDENADOS DE MAYOR A MENOR VENDIDOS:")
print("-" * 60)
for idx, row in productos_mayor_menor.iterrows():
    print(f"{row['nombre_producto'][:40]:40} [{row['categoria']}]: {int(row['cantidad']):5d} unidades")

print("\n" + "="*60)
print("PRODUCTOS ORDENADOS DE MENOR A MAYOR VENDIDOS:")
print("-" * 60)
for idx, row in productos_menor_mayor.iterrows():
    print(f"{row['nombre_producto'][:40]:40} [{row['categoria']}]: {int(row['cantidad']):5d} unidades")

fig, ax = plt.subplots(figsize=(12, 10))

top_20_mas = productos_mayor_menor.head(20).copy()
top_20_mas = top_20_mas.sort_values("cantidad", ascending=True)  # Esto hace que el mayor quede arriba en el gráfico

nombres_mas = [f"{row['nombre_producto'][:30]}... [{row['categoria']}]" if len(row['nombre_producto']) > 30 
               else f"{row['nombre_producto']} [{row['categoria']}]" 
               for idx, row in top_20_mas.iterrows()]

ax.barh(nombres_mas, top_20_mas["cantidad"], color='blue', alpha=0.7)
ax.set_title('Top 20 Productos Más Vendidos')
ax.set_xlabel('Cantidad (unidades)')
ax.set_ylabel('Productos')

plt.tight_layout()
savefig("productos_mas_vendidos.png")
print(f"\nGrafico guardado: productos_mas_vendidos.png")

fig, ax = plt.subplots(figsize=(12, 10))

top_20_menos = productos_menor_mayor.head(20).copy()
top_20_menos = top_20_menos.sort_values("cantidad", ascending=False)

nombres_menos = [f"{row['nombre_producto'][:30]}... [{row['categoria']}]" if len(row['nombre_producto']) > 30 
                 else f"{row['nombre_producto']} [{row['categoria']}]" 
                 for idx, row in top_20_menos.iterrows()]

ax.barh(nombres_menos, top_20_menos["cantidad"], color='orange', alpha=0.7)
ax.set_title('Top 20 Productos Menos Vendidos')
ax.set_xlabel('Cantidad (unidades)')
ax.set_ylabel('Productos')

plt.tight_layout()
savefig("productos_menos_vendidos.png")
print(f"Grafico guardado: productos_menos_vendidos.png")
