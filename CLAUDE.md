# Inventario ABC — reglas del proyecto

Pieza de portafolio de Gustavo para puestos de operaciones, compras, cadena de suministro,
calidad y administrativo en Sevilla. La leen reclutadores y jefes de operaciones, no
programadores: el README cuenta situación → qué se hizo → resultado, en español de España,
sin jerga.

- **Ninguna cifra del README sin comprobar contra los datos.** Al cambiar una consulta,
  regenerar los resultados y revisar cada número del README.
- Cada resultado nuevo se valida con un segundo cálculo independiente (pandas desde
  `ventas_brutas`, sin pasar por las vistas SQL), como se hizo con la clasificación ABC.
- Venta neta siempre: las anulaciones (facturas `C…`) se restan, no se borran.
- `datos/` no va a git (pesa ~190 MB y se descarga de la UCI). `resultados/` sí va, porque
  es lo que se enseña.
- Citar el dataset (CC BY 4.0) en cualquier pieza que use sus datos.

Hecho: ABC (paso 1) y XYZ con la tabla de 9 casillas (paso 2).
Siguiente: paso 3, máximos, mínimos y punto de pedido por producto según su casilla, con los
supuestos (plazo del proveedor, nivel de servicio, cobertura) aprobados por Gustavo y escritos
en el README → previsión de la demanda de los A (Nixtla/statsforecast).
