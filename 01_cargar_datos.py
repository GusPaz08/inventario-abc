"""Paso 1: pasar el Excel de ventas a una base de datos SQL.

El Excel original (Online Retail II, UCI) trae dos hojas, una por año, con más
de un millón de líneas de venta. En SQL se consultan en segundos; en Excel no.
"""

import sqlite3
from pathlib import Path

import pandas as pd

CARPETA = Path(__file__).parent
EXCEL = CARPETA / "datos" / "online_retail_II.xlsx"
BASE = CARPETA / "datos" / "inventario.db"

# Nombres en español para que las consultas se lean sin traducir.
COLUMNAS = {
    "Invoice": "factura",
    "StockCode": "producto",
    "Description": "descripcion",
    "Quantity": "cantidad",
    "InvoiceDate": "fecha",
    "Price": "precio",
    "Customer ID": "cliente",
    "Country": "pais",
}


def main():
    hojas = pd.read_excel(EXCEL, sheet_name=None, dtype={"Invoice": str, "StockCode": str})
    ventas = pd.concat(hojas.values(), ignore_index=True).rename(columns=COLUMNAS)
    ventas["fecha"] = ventas["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(BASE) as con:
        ventas.to_sql("ventas_brutas", con, if_exists="replace", index=False)

    print(f"Hojas leídas: {list(hojas)}")
    print(f"Líneas cargadas: {len(ventas):,}".replace(",", "."))


if __name__ == "__main__":
    main()
