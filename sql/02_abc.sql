-- Clasificación ABC por valor de venta de los últimos 12 meses completos
-- (diciembre de 2010 a noviembre de 2011; diciembre de 2011 solo tiene 9 días).
-- A: los productos que forman el primer 80 % del importe.
-- B: los que llevan del 80 % al 95 %.
-- C: el resto.
-- Un producto entra en una clase si el acumulado ANTES de él no ha llegado al
-- límite; así el producto que cruza el 80 % cuenta como A.
WITH periodo AS (
    SELECT *
    FROM ventas_limpias
    WHERE fecha >= '2010-12-01' AND fecha < '2011-12-01'
),
por_producto AS (
    SELECT producto,
           SUM(cantidad) AS unidades,
           COUNT(DISTINCT CASE WHEN tipo = 'venta' THEN factura END) AS pedidos,
           SUM(importe) AS importe
    FROM periodo
    GROUP BY producto
    -- Fuera los productos que en el año solo tuvieron anulaciones.
    HAVING SUM(importe) > 0
),
-- Un mismo código aparece con varias descripciones; se usa la más repetida.
descripciones AS (
    SELECT producto,
           descripcion,
           ROW_NUMBER() OVER (PARTITION BY producto ORDER BY COUNT(*) DESC) AS orden
    FROM periodo
    WHERE descripcion IS NOT NULL AND tipo = 'venta'
    GROUP BY producto, descripcion
),
acumulado AS (
    SELECT *,
           SUM(importe) OVER (ORDER BY importe DESC, producto ROWS UNBOUNDED PRECEDING)
               / SUM(importe) OVER () AS pct_acumulado,
           (SUM(importe) OVER (ORDER BY importe DESC, producto ROWS UNBOUNDED PRECEDING) - importe)
               / SUM(importe) OVER () AS pct_previo
    FROM por_producto
)
SELECT a.producto,
       d.descripcion,
       a.unidades,
       a.pedidos,
       ROUND(a.importe, 2) AS importe,
       a.pct_acumulado,
       CASE WHEN a.pct_previo < 0.80 THEN 'A'
            WHEN a.pct_previo < 0.95 THEN 'B'
            ELSE 'C' END AS clase
FROM acumulado a
LEFT JOIN descripciones d ON d.producto = a.producto AND d.orden = 1
ORDER BY a.importe DESC;
