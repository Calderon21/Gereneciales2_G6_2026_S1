import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

print("Directorio actual:", os.getcwd())

# Cargar Excel
ventas = pd.read_excel("data/ventas.xlsx", sheet_name="Base de Datos")
clientes = pd.read_excel("data/ventas.xlsx", sheet_name="Clientes")

# Limpiar IDs del cliente
ventas["ID del cliente"] = ventas["ID del cliente"].astype(str).str.replace(",", "")
clientes["ID del cliente"] = clientes["ID del cliente"].astype(str).str.replace(",", "")
ventas["ID de la orden"] = ventas["ID de la orden"].astype(str).str.replace(",", "")

# Renombrar columnas 
ventas = ventas.rename(columns={
    "ID de la orden": "id_orden",
    "Fecha de la compra": "fecha_compra",
    "ID del cliente": "id_cliente",
    "Categoría del producto": "categoria",
    "Nombre del producto": "nombre_producto",
    "Precio del producto": "precio",
    "Cantidad comprada": "cantidad",
    "Total de la orden": "total",
    "Método de pago": "metodo_pago",
    "Región de envío": "region_envio"
})

clientes = clientes.rename(columns={
    "ID del cliente": "id_cliente",
    "Género del cliente": "genero",
    "Edad del cliente": "edad"
})

# Eliminar columnas que no deben ir en ventas
ventas = ventas[[
    "id_orden",
    "fecha_compra",
    "id_cliente",
    "categoria",
    "nombre_producto",
    "precio",
    "cantidad",
    "total",
    "metodo_pago",
    "region_envio"
]]

# Corrección de tipos
ventas["fecha_compra"] = pd.to_datetime(ventas["fecha_compra"])
ventas["precio"] = ventas["precio"].astype(float)
ventas["cantidad"] = ventas["cantidad"].astype(int)
ventas["total"] = ventas["total"].astype(float)

clientes["edad"] = clientes["edad"].astype(int)

# Eliminar duplicados
clientes = clientes.drop_duplicates(subset=["id_cliente"])
ventas = ventas.drop_duplicates(subset=["id_orden"])

# Cargar variables de entorno
load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Crear tablas manualmente (con PK y FK)
with engine.connect() as conn:

    conn.execute(text("""
        DROP TABLE IF EXISTS ventas;
    """))

    conn.execute(text("""
        DROP TABLE IF EXISTS clientes;
    """))

    conn.execute(text("""
        CREATE TABLE clientes (
            id_cliente VARCHAR(20) PRIMARY KEY,
            genero VARCHAR(20),
            edad INT
        );
    """))

    conn.execute(text("""
        CREATE TABLE ventas (
            id_orden VARCHAR(20) PRIMARY KEY,
            fecha_compra DATE,
            id_cliente VARCHAR(20),
            categoria VARCHAR(50),
            nombre_producto VARCHAR(100),
            precio DECIMAL(10,2),
            cantidad INT,
            total DECIMAL(10,2),
            metodo_pago VARCHAR(50),
            region_envio VARCHAR(50),
            FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
        );
    """))

# Insertar datos
clientes.to_sql("clientes", engine, if_exists="append", index=False)
ventas.to_sql("ventas", engine, if_exists="append", index=False)

print("Base de datos creada correctamente con modelo relacional.")