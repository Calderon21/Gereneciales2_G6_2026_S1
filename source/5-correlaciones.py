import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
import seaborn as sns

OUTPUT_DIR = "img-5"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def savefig(filename: str):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=200)
    plt.close()

def cramers_v(x, y):
    """
    Calcula el coeficiente V de Cramer para dos variables categóricas.
    V de Cramer mide la asociación entre dos variables nominales (0 a 1).
    0 = sin asociación, 1 = asociación perfecta.
    """
    confusion_matrix = pd.crosstab(x, y)
    chi2 = chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum().sum()
    min_dim = min(confusion_matrix.shape) - 1
    
    if min_dim == 0:
        return 0
    
    return np.sqrt(chi2 / (n * min_dim))

# Configuración de base de datos
load_dotenv()
engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Consulta SQL
query = """
    SELECT
        v.id_orden,
        v.id_cliente,
        v.total,
        v.categoria,
        v.metodo_pago,
        c.edad
    FROM ventas v
    JOIN clientes c ON c.id_cliente = v.id_cliente;
"""

df = pd.read_sql(query, engine)

# Conversión de tipos de datos
df["total"] = pd.to_numeric(df["total"], errors="coerce")
df["edad"] = pd.to_numeric(df["edad"], errors="coerce")
df["categoria"] = df["categoria"].fillna("Sin dato").astype(str)
df["metodo_pago"] = df["metodo_pago"].fillna("Sin dato").astype(str)

# 5a. CORRELACIÓN ENTRE TOTAL DE ORDEN Y EDAD DEL CLIENTE

print("5a. CORRELACIÓN ENTRE TOTAL DE ORDEN Y EDAD DEL CLIENTE")


# Eliminar valores nulos
df_correlacion_edad = df[["total", "edad"]].dropna()

# Calcular correlación de Pearson
pearson_corr = df_correlacion_edad["total"].corr(df_correlacion_edad["edad"])

print(f"\nCorrelación de Pearson: {pearson_corr:.4f}")

# Interpretación
if abs(pearson_corr) < 0.3:
    interpretacion = "Muy débil o inexistente"
elif abs(pearson_corr) < 0.5:
    interpretacion = "Débil"
elif abs(pearson_corr) < 0.7:
    interpretacion = "Moderada"
else:
    interpretacion = "Fuerte"

direccion = "positiva (a mayor edad, mayor total)" if pearson_corr > 0 else "negativa (a mayor edad, menor total)"
print(f"Interpretación: Correlación {interpretacion} y {direccion}")

print(f"\nNúmero de registros analizados: {len(df_correlacion_edad)}")
print(f"Edad - Media: {df_correlacion_edad['edad'].mean():.2f}, Desv. Est.: {df_correlacion_edad['edad'].std():.2f}")
print(f"Total - Media: ${df_correlacion_edad['total'].mean():.2f}, Desv. Est.: ${df_correlacion_edad['total'].std():.2f}")

# Gráfico de dispersión con línea de tendencia
fig, ax = plt.subplots(figsize=(10, 6))

ax.scatter(df_correlacion_edad["edad"], df_correlacion_edad["total"], 
           alpha=0.5, s=30, color="steelblue", edgecolors="black", linewidth=0.5)

# Línea de tendencia
z = np.polyfit(df_correlacion_edad["edad"], df_correlacion_edad["total"], 1)
p = np.poly1d(z)
x_trend = np.linspace(df_correlacion_edad["edad"].min(), df_correlacion_edad["edad"].max(), 100)
ax.plot(x_trend, p(x_trend), "r--", linewidth=2, label=f"Línea de tendencia (r={pearson_corr:.3f})")

ax.set_xlabel("Edad del Cliente (años)", fontsize=11)
ax.set_ylabel("Total de Orden ($)", fontsize=11)
ax.set_title("Correlación entre Total de Orden y Edad del Cliente", fontsize=13, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

savefig("5a_correlacion_total_edad_dispersión.png")
print("Gráfico guardado: 5a_correlacion_total_edad_dispersión.png")

# Gráfico hexbin (densidad)
fig, ax = plt.subplots(figsize=(10, 6))

hexbin = ax.hexbin(df_correlacion_edad["edad"], df_correlacion_edad["total"], 
                   gridsize=20, cmap="YlOrRd", mincnt=1)

ax.set_xlabel("Edad del Cliente (años)", fontsize=11)
ax.set_ylabel("Total de Orden ($)", fontsize=11)
ax.set_title("Densidad de Órdenes por Edad (Hexbin)", fontsize=13, fontweight="bold")

cbar = plt.colorbar(hexbin, ax=ax)
cbar.set_label("Número de órdenes", fontsize=10)

savefig("5a_correlacion_total_edad_hexbin.png")
print("Gráfico guardado: 5a_correlacion_total_edad_hexbin.png")

# 5b. CORRELACIÓN ENTRE CATEGORÍA Y MÉTODO DE PAGO (V DE CRAMER)
print("5b. CORRELACIÓN ENTRE CATEGORÍA Y MÉTODO DE PAGO (V DE CRAMER)")


# Eliminar valores nulos
df_categorias = df[["categoria", "metodo_pago"]].dropna()

# Calcular V de Cramer
v_cramer = cramers_v(df_categorias["categoria"], df_categorias["metodo_pago"])

print(f"\nV de Cramer: {v_cramer:.4f}")

# Interpretación de V de Cramer
if v_cramer < 0.1:
    interpretacion_cramer = "Negligible o inexistente"
elif v_cramer < 0.3:
    interpretacion_cramer = "Débil"
elif v_cramer < 0.5:
    interpretacion_cramer = "Moderada"
else:
    interpretacion_cramer = "Fuerte"

print(f"Interpretación: Asociación {interpretacion_cramer} entre categoría y método de pago")
print(f"\nNúmero de registros analizados: {len(df_categorias)}")

# Tabla de contingencia
contingencia = pd.crosstab(df_categorias["categoria"], df_categorias["metodo_pago"])
print("\nTabla de Contingencia (Categoría vs Método de Pago):")
print(contingencia)

# Calcular chi-cuadrado
chi2, p_value, dof, expected = chi2_contingency(contingencia)
print(f"\nPrueba Chi-Cuadrado:")
print(f"   Chi² = {chi2:.4f}")
print(f"   p-value = {p_value:.4e}")
print(f"   Grados de libertad = {dof}")
print(f"   Resultado: {'Hay asociación significativa' if p_value < 0.05 else 'No hay asociación significativa'} (α=0.05)")

# Gráfico de heatmap con la tabla de contingencia normalizada
fig, ax = plt.subplots(figsize=(10, 6))

# Normalizar por filas (porcentaje de método de pago por categoría)
contingencia_norm = contingencia.div(contingencia.sum(axis=1), axis=0) * 100

sns.heatmap(contingencia_norm, annot=True, fmt=".1f", cmap="YlGnBu", 
            cbar_kws={"label": "Porcentaje (%)"}, ax=ax, linewidths=0.5)

ax.set_xlabel("Método de Pago", fontsize=11)
ax.set_ylabel("Categoría de Producto", fontsize=11)
ax.set_title(f"Distribución de Métodos de Pago por Categoría\n(V de Cramer = {v_cramer:.4f})", 
             fontsize=13, fontweight="bold")

plt.tight_layout()
savefig("5b_correlacion_categoria_metodo_pago_heatmap.png")
print("Gráfico guardado: 5b_correlacion_categoria_metodo_pago_heatmap.png")

# Gráfico de barras agrupadas alternativo
fig, ax = plt.subplots(figsize=(12, 6))

contingencia.T.plot(kind="bar", ax=ax, width=0.8)

ax.set_xlabel("Método de Pago", fontsize=11)
ax.set_ylabel("Cantidad de Transacciones", fontsize=11)
ax.set_title(f"Transacciones por Categoría y Método de Pago\n(V de Cramer = {v_cramer:.4f})", 
             fontsize=13, fontweight="bold")
ax.legend(title="Categoría", bbox_to_anchor=(1.05, 1), loc="upper left")
ax.tick_params(axis="x", rotation=45)

savefig("5b_correlacion_categoria_metodo_pago_barras.png")
print("Gráfico guardado: 5b_correlacion_categoria_metodo_pago_barras.png")


