"""Clasificación ABC-XYZ de cada producto, a partir de las consultas SQL."""

import sqlite3
from pathlib import Path

import pandas as pd

CARPETA = Path(__file__).parent
BASE = CARPETA / "datos" / "inventario.db"
SQL = CARPETA / "sql"


def clasificar_abc_xyz():
    with sqlite3.connect(BASE) as con:
        con.executescript((SQL / "01_ventas_limpias.sql").read_text())
        abc = pd.read_sql((SQL / "02_abc.sql").read_text(), con)
        xyz = pd.read_sql((SQL / "03_xyz.sql").read_text(), con)
    productos = abc.merge(xyz, on="producto", how="left")
    # Los lanzados en noviembre de 2011 aún no tienen ningún mes completo.
    productos["clase_xyz"] = productos["clase_xyz"].fillna("nuevo")
    productos["casilla"] = productos["clase"] + productos["clase_xyz"]
    return productos
