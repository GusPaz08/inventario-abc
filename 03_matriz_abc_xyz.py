"""Paso 3: cruzar la clasificación ABC con la XYZ.

La ABC dice cuánto vende cada producto; la XYZ, si lo vende de forma regular o
a golpes. Juntas forman una tabla de 9 casillas, y cada casilla pide una forma
distinta de reponer. Deja en resultados/ un Excel y la tabla en imagen.
"""

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle

from formato import dar_formato

CARPETA = Path(__file__).parent
BASE = CARPETA / "datos" / "inventario.db"
SQL = CARPETA / "sql"
RESULTADOS = CARPETA / "resultados"

FILAS = ["A", "B", "C"]
COLUMNAS = ["X", "Y", "Z", "nuevo"]

SIGNIFICADO_ABC = {"A": "Vende mucho", "B": "Vende algo", "C": "Vende poco"}
SIGNIFICADO_XYZ = {
    "X": "de forma regular",
    "Y": "con altibajos",
    "Z": "a golpes",
    "nuevo": "y lleva menos de 6 meses",
}

# Política de reposición habitual para cada casilla.
QUE_HACER = {
    "AX": "Reposición automática con poco stock de seguridad",
    "AY": "Reposición automática con más stock de seguridad; revisar cada mes",
    "AZ": "Planificar a mano con previsión; no reponer en automático",
    "BX": "Reposición automática",
    "BY": "Reposición automática con revisión periódica",
    "BZ": "Pedir por temporada o bajo pedido; stock mínimo",
    "CX": "Reposición automática, en pedidos grandes y espaciados",
    "CY": "Revisar de vez en cuando; stock bajo",
    "CZ": "Candidato a liquidar o sacar del catálogo; pedir solo bajo pedido",
    "Anuevo": "Vigilar de cerca hasta tener 6 meses de ventas",
    "Bnuevo": "Vigilar hasta tener 6 meses de ventas",
    "Cnuevo": "Vigilar hasta tener 6 meses de ventas",
}


def clasificar():
    with sqlite3.connect(BASE) as con:
        con.executescript((SQL / "01_ventas_limpias.sql").read_text())
        abc = pd.read_sql((SQL / "02_abc.sql").read_text(), con)
        xyz = pd.read_sql((SQL / "03_xyz.sql").read_text(), con)
    productos = abc.merge(xyz, on="producto", how="left")
    # Los lanzados en noviembre de 2011 aún no tienen ningún mes completo.
    productos["clase_xyz"] = productos["clase_xyz"].fillna("nuevo")
    productos["casilla"] = productos["clase"] + productos["clase_xyz"]
    productos["que_hacer"] = productos["casilla"].map(QUE_HACER)
    return productos


def resumir(productos):
    resumen = (
        productos.groupby(["clase", "clase_xyz"])
        .agg(productos=("producto", "count"), importe=("importe", "sum"))
        .reindex(pd.MultiIndex.from_product([FILAS, COLUMNAS]), fill_value=0)
        .rename_axis(["clase", "clase_xyz"])
        .reset_index()
    )
    resumen["pct_productos"] = resumen["productos"] / resumen["productos"].sum()
    resumen["pct_importe"] = resumen["importe"] / resumen["importe"].sum()
    resumen["casilla"] = resumen["clase"] + resumen["clase_xyz"]
    resumen["significado"] = (
        resumen["clase"].map(SIGNIFICADO_ABC) + " " + resumen["clase_xyz"].map(SIGNIFICADO_XYZ)
    )
    resumen["que_hacer"] = resumen["casilla"].map(QUE_HACER)
    return resumen


def guardar_excel(productos, resumen, ruta):
    tabla = resumen.rename(columns={
        "casilla": "Casilla", "significado": "Qué significa", "que_hacer": "Qué hacer",
        "productos": "Productos", "pct_productos": "% de productos",
        "importe": "Venta neta (£)", "pct_importe": "% de la venta",
    })[["Casilla", "Qué significa", "Qué hacer", "Productos", "% de productos",
        "Venta neta (£)", "% de la venta"]]

    detalle = productos.rename(columns={
        "producto": "Código", "descripcion": "Descripción", "clase": "ABC",
        "clase_xyz": "XYZ", "casilla": "Casilla", "que_hacer": "Qué hacer",
        "importe": "Venta neta (£)", "unidades": "Unidades netas",
        "meses": "Meses medidos", "meses_con_venta": "Meses con venta",
        "media_mensual": "Media mensual (uds.)", "cv": "Variación (CV)",
    })[["Código", "Descripción", "ABC", "XYZ", "Casilla", "Qué hacer", "Venta neta (£)",
        "Unidades netas", "Meses medidos", "Meses con venta", "Media mensual (uds.)",
        "Variación (CV)"]]

    como_leerlo = pd.DataFrame({"Cómo leer este Excel": [
        "Datos: Online Retail II (UCI, CC BY 4.0). Ventas netas de diciembre de 2010 a noviembre de 2011.",
        "ABC (cuánto vende): A = productos que hacen el primer 80 % de la venta; B = hasta el 95 %; C = el resto.",
        "XYZ (cómo de regular vende): se mide la variación de las unidades vendidas mes a mes.",
        "Variación (CV) = desviación típica mensual / media mensual. X: hasta 0,5. Y: hasta 1. Z: más de 1.",
        "Los meses sin ventas cuentan como 0. Un mes con más anulaciones que ventas cuenta como 0.",
        "Los productos lanzados durante el año se miden desde su primer mes completo; con menos de 6 meses son 'nuevo'.",
    ]})

    formatos = {
        "Productos": "#,##0", "% de productos": "0.0%", "Venta neta (£)": "#,##0",
        "% de la venta": "0.0%", "Unidades netas": "#,##0", "Media mensual (uds.)": "#,##0.0",
        "Variación (CV)": "0.00",
    }
    with pd.ExcelWriter(ruta, engine="openpyxl") as libro:
        for nombre, df in (("Matriz", tabla), ("Productos", detalle), ("Cómo leerlo", como_leerlo)):
            df.to_excel(libro, sheet_name=nombre, index=False)
            dar_formato(libro.sheets[nombre], df, formatos, ancho_maximo=110)


def dibujar_matriz(resumen, ruta):
    escala = LinearSegmentedColormap.from_list("azul", ["#EEF2F8", "#1F3864"])
    normal = Normalize(vmin=0, vmax=resumen["pct_importe"].max())
    celdas = resumen.set_index("casilla")

    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=150)
    hueco = 0.03
    for f, abc in enumerate(FILAS):
        for c, xyz in enumerate(COLUMNAS):
            celda = celdas.loc[abc + xyz]
            # La columna de nuevos va un poco separada: no es una clase XYZ.
            x = c + (0.25 if xyz == "nuevo" else 0)
            y = len(FILAS) - 1 - f
            fondo = escala(normal(celda["pct_importe"]))
            ax.add_patch(Rectangle((x + hueco, y + hueco), 1 - 2 * hueco, 1 - 2 * hueco,
                                   facecolor=fondo, edgecolor="none"))
            claro = celda["pct_importe"] < normal.vmax * 0.45
            tinta = "#1A1A1A" if claro else "#FFFFFF"
            secundaria = "#555555" if claro else "#DCE3EE"
            ax.text(x + 0.5, y + 0.68, abc + xyz if xyz != "nuevo" else f"{abc} nuevo",
                    ha="center", fontsize=15, fontweight="bold", color=tinta)
            ax.text(x + 0.5, y + 0.43, f"{celda['pct_importe'] * 100:.1f} % de la venta".replace(".", ","),
                    ha="center", fontsize=10.5, color=tinta)
            ax.text(x + 0.5, y + 0.22, f"{celda['productos']:,} productos".replace(",", "."),
                    ha="center", fontsize=9.5, color=secundaria)

    for c, xyz in enumerate(COLUMNAS):
        x = c + (0.25 if xyz == "nuevo" else 0)
        rotulo = {"X": "X · regular", "Y": "Y · altibajos", "Z": "Z · a golpes",
                  "nuevo": "Nuevos\n(< 6 meses)"}[xyz]
        ax.text(x + 0.5, 3.12, rotulo, ha="center", va="bottom", fontsize=11, color="#333333")
    for f, abc in enumerate(FILAS):
        rotulo = {"A": "A · vende mucho", "B": "B · vende algo", "C": "C · vende poco"}[abc]
        ax.text(-0.08, len(FILAS) - 1 - f + 0.5, rotulo, ha="right", va="center",
                fontsize=11, color="#333333")

    ax.set_xlim(-1.35, 4.3)
    ax.set_ylim(-0.05, 3.55)
    ax.set_aspect("auto")
    ax.axis("off")
    ax.set_title("Tabla ABC-XYZ · cuánto vende cada producto y con qué regularidad",
                 loc="left", fontsize=13, x=0.0)

    barra = fig.colorbar(plt.cm.ScalarMappable(norm=normal, cmap=escala), ax=ax,
                         fraction=0.025, pad=0.01)
    barra.set_label("% de la venta neta")
    barra.ax.yaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f} %")
    barra.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta)


def main():
    RESULTADOS.mkdir(exist_ok=True)
    productos = clasificar()
    resumen = resumir(productos)
    guardar_excel(productos, resumen, RESULTADOS / "matriz_abc_xyz.xlsx")
    dibujar_matriz(resumen, RESULTADOS / "matriz_abc_xyz.png")
    print(resumen[["casilla", "productos", "pct_productos", "importe", "pct_importe"]].to_string(index=False))


if __name__ == "__main__":
    main()
