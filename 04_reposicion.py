"""Paso 4: cuánto pedir y cuándo, producto a producto.

Para cada producto de demanda regular o con altibajos (X e Y) calcula una regla
de reposición: cuando el stock, contando lo pedido que aún no ha llegado, baje
del punto de pedido, se pide una cantidad fija. Deja el resultado en un Excel.
"""

import math
from pathlib import Path
from statistics import NormalDist

import pandas as pd

from clasificacion import clasificar_abc_xyz
from formato import dar_formato

RESULTADOS = Path(__file__).parent / "resultados"

# Supuestos aprobados por Gustavo el 25-10-2026. Los datos no traen el plazo del
# proveedor ni los costes de pedir y almacenar, así que se fijan aquí.
PLAZO_DIAS = 21
NIVEL_SERVICIO = {"A": 0.98, "B": 0.95, "C": 0.90}
SEMANAS_POR_PEDIDO = {"A": 2, "B": 4, "C": 8}

DIAS_POR_MES = 365 / 12

MOTIVO_SIN_REGLA = {
    "AZ": "Vende mucho a golpes: planificar con previsión de temporada",
    "BZ": "Vende a golpes: planificar con previsión de temporada",
    "CZ": "Vende poco y a golpes: pedir solo bajo pedido, sin stock fijo",
    "nuevo": "Menos de 6 meses a la venta: sin historia suficiente",
}


def calcular_reglas(productos):
    """Punto de pedido, cantidad a pedir y máximo de cada producto X o Y."""
    reglas = productos[productos["clase_xyz"].isin(["X", "Y"])].copy()
    plazo_en_meses = PLAZO_DIAS / DIAS_POR_MES
    z = reglas["clase"].map(lambda c: NormalDist().inv_cdf(NIVEL_SERVICIO[c]))

    reglas["venta_en_plazo"] = reglas["media_mensual"] * plazo_en_meses
    # La variación mensual se escala al plazo: crece con la raíz del tiempo.
    reglas["seguridad"] = z * reglas["desviacion"] * math.sqrt(plazo_en_meses)
    # Se redondea hacia arriba: mejor una unidad de más que una rotura.
    reglas["punto_pedido"] = (reglas["venta_en_plazo"] + reglas["seguridad"]).apply(math.ceil)
    venta_semanal = reglas["media_mensual"] / DIAS_POR_MES * 7
    reglas["cantidad"] = (venta_semanal * reglas["clase"].map(SEMANAS_POR_PEDIDO)).apply(math.ceil)
    reglas["maximo"] = reglas["punto_pedido"] + reglas["cantidad"]
    reglas["regla"] = reglas.apply(
        lambda r: f"Cuando queden {miles(r.punto_pedido)}, pide {miles(r.cantidad)}", axis=1)
    return reglas


def miles(n):
    return f"{n:,}".replace(",", ".")


def sin_regla(productos):
    resto = productos[~productos["clase_xyz"].isin(["X", "Y"])].copy()
    clave = resto["clase_xyz"].where(resto["clase_xyz"] == "nuevo", resto["casilla"])
    resto["motivo"] = clave.map(MOTIVO_SIN_REGLA)
    return resto


def guardar_excel(reglas, resto, ruta):
    hoja_reglas = reglas.rename(columns={
        "producto": "Código", "descripcion": "Descripción", "casilla": "Casilla",
        "regla": "Regla", "media_mensual": "Venta media mensual (uds.)",
        "venta_en_plazo": "Venta durante el plazo (uds.)", "seguridad": "Stock de seguridad (uds.)",
        "punto_pedido": "Punto de pedido (mínimo)", "cantidad": "Cantidad a pedir",
        "maximo": "Máximo",
    })[["Código", "Descripción", "Casilla", "Regla", "Punto de pedido (mínimo)",
        "Cantidad a pedir", "Máximo", "Venta media mensual (uds.)",
        "Venta durante el plazo (uds.)", "Stock de seguridad (uds.)"]]

    hoja_resto = resto.rename(columns={
        "producto": "Código", "descripcion": "Descripción", "casilla": "Casilla",
        "motivo": "Por qué no lleva regla", "importe": "Venta neta (£)",
    })[["Código", "Descripción", "Casilla", "Por qué no lleva regla", "Venta neta (£)"]]

    nivel = ", ".join(f"{c} {v:.0%}" for c, v in NIVEL_SERVICIO.items())
    semanas = ", ".join(f"{c} {v} semanas" for c, v in SEMANAS_POR_PEDIDO.items())
    supuestos = pd.DataFrame({
        "Supuesto": ["Plazo del proveedor", "Nivel de servicio", "Cuánto pedir cada vez",
                     "Demanda", "Qué productos", "Cómo se usa la regla"],
        "Valor": [
            f"{PLAZO_DIAS} días para todos los productos (no viene en los datos)",
            f"{nivel}: de cada 100 pedidos, en cuántos no se agota el stock mientras llega",
            f"{semanas} de venta media",
            "Venta media y variación de los meses medidos (dic 2010 – nov 2011), sin temporada",
            "Solo X e Y. Los Z se planifican con previsión; los nuevos esperan a tener 6 meses",
            "Se compara con el stock disponible más lo pedido que aún no ha llegado",
        ],
    })

    formatos = {
        "Punto de pedido (mínimo)": "#,##0", "Cantidad a pedir": "#,##0", "Máximo": "#,##0",
        "Venta media mensual (uds.)": "#,##0", "Venta durante el plazo (uds.)": "#,##0",
        "Stock de seguridad (uds.)": "#,##0", "Venta neta (£)": "#,##0",
    }
    with pd.ExcelWriter(ruta, engine="openpyxl") as libro:
        for nombre, df in (("Reglas", hoja_reglas), ("Sin regla", hoja_resto), ("Supuestos", supuestos)):
            df.to_excel(libro, sheet_name=nombre, index=False)
            dar_formato(libro.sheets[nombre], df, formatos, ancho_maximo=90)


def main():
    RESULTADOS.mkdir(exist_ok=True)
    productos = clasificar_abc_xyz()
    reglas = calcular_reglas(productos)
    resto = sin_regla(productos)
    guardar_excel(reglas, resto, RESULTADOS / "reposicion.xlsx")

    venta_total = productos["importe"].sum()
    print(f"Con regla: {len(reglas)} productos, {reglas['importe'].sum() / venta_total:.1%} de la venta")
    print(f"Sin regla: {len(resto)} productos")
    print(resto["motivo"].value_counts().to_string())
    print(reglas[["producto", "descripcion", "casilla", "regla", "maximo"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
