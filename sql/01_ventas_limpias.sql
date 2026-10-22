-- Ventas netas: mercancía vendida menos lo anulado o devuelto.
-- Las anulaciones (facturas que empiezan por C) se quedan, en negativo, para
-- que resten. Si solo se borrasen, el pedido original seguiría contando: el
-- 18-01-2011 un cliente pidió 74.215 tarros y lo anuló 16 minutos después.
-- Se quitan los ajustes de deuda (A), las mermas y regularizaciones de stock
-- (cantidad negativa sin factura de anulación), las líneas sin precio y los
-- códigos que no son producto: portes, comisiones, descuentos, vales y pruebas.
-- Los productos de verdad tienen un código que empieza por cinco cifras.
DROP VIEW IF EXISTS ventas_limpias;

CREATE VIEW ventas_limpias AS
SELECT factura,
       CASE WHEN factura LIKE 'C%' THEN 'anulacion' ELSE 'venta' END AS tipo,
       producto,
       descripcion,
       cantidad,
       precio,
       cantidad * precio AS importe,
       fecha,
       cliente,
       pais
FROM ventas_brutas
WHERE precio > 0
  AND producto GLOB '[0-9][0-9][0-9][0-9][0-9]*'
  AND (
        (factura NOT LIKE 'C%' AND factura NOT LIKE 'A%' AND cantidad > 0)
     OR (factura LIKE 'C%' AND cantidad < 0)
  );
