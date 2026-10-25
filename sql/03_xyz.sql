-- Clasificación XYZ: lo estable que es la demanda de cada producto, mes a mes,
-- en el mismo periodo que la ABC (diciembre de 2010 a noviembre de 2011).
-- Se mide con el coeficiente de variación (CV): la desviación típica de las
-- unidades vendidas cada mes dividida entre su media. Cuanto más alto, más
-- imprevisible.
--   X: CV <= 0,5  demanda estable
--   Y: CV <= 1,0  demanda variable
--   Z: CV >  1,0  demanda irregular
-- Son los cortes más usados; se pueden ajustar.
--
-- Se mide por meses y no por semanas porque la tienda cierra en Navidad y en
-- Semana Santa: esas semanas casi vacías harían parecer irregular a todo el
-- catálogo.
--
-- Tres decisiones que cambian el resultado:
-- 1. Los meses sin ventas cuentan como 0. Si se ignorasen, un producto que solo
--    vende en noviembre parecería estable.
-- 2. Un mes con más anulaciones que ventas (se anula un pedido de un mes
--    anterior) cuenta como 0: la demanda negativa no existe.
-- 3. Los productos lanzados durante el año se miden desde el primer mes
--    completo tras el lanzamiento, porque el mes en que salen suele estar a
--    medias. Con menos de 6 meses medidos quedan como 'nuevo', sin clase.
WITH RECURSIVE meses(mes) AS (
    SELECT '2010-12'
    UNION ALL
    SELECT strftime('%Y-%m', mes || '-01', '+1 month') FROM meses WHERE mes < '2011-11'
),
-- La primera venta se busca en todo el histórico, desde diciembre de 2009.
inicio AS (
    SELECT producto,
           CASE WHEN substr(MIN(fecha), 1, 7) < '2010-12' THEN '2010-12'
                ELSE strftime('%Y-%m', MIN(fecha), 'start of month', '+1 month') END AS desde
    FROM ventas_limpias
    WHERE tipo = 'venta'
    GROUP BY producto
),
ventas_mes AS (
    SELECT producto, substr(fecha, 1, 7) AS mes, SUM(cantidad) AS unidades
    FROM ventas_limpias
    WHERE fecha >= '2010-12-01' AND fecha < '2011-12-01'
    GROUP BY producto, mes
),
demanda AS (
    SELECT i.producto, m.mes, MAX(COALESCE(v.unidades, 0), 0) AS unidades
    FROM inicio i
    JOIN meses m ON m.mes >= i.desde
    LEFT JOIN ventas_mes v ON v.producto = i.producto AND v.mes = m.mes
),
estadisticas AS (
    SELECT producto,
           COUNT(*) AS meses,
           SUM(unidades > 0) AS meses_con_venta,
           AVG(unidades) AS media,
           sqrt(MAX(AVG(unidades * unidades) - AVG(unidades) * AVG(unidades), 0)) AS desviacion
    FROM demanda
    GROUP BY producto
)
SELECT producto,
       meses,
       meses_con_venta,
       media AS media_mensual,
       desviacion,
       desviacion / NULLIF(media, 0) AS cv,
       CASE WHEN meses < 6 THEN 'nuevo'
            WHEN media = 0 THEN 'Z'
            WHEN desviacion / media <= 0.5 THEN 'X'
            WHEN desviacion / media <= 1.0 THEN 'Y'
            ELSE 'Z' END AS clase_xyz
FROM estadisticas;
