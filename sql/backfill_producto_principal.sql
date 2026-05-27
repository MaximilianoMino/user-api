-- Backfill: Agregar producto_principal = 0 a análisis completos que no lo tienen
-- Ejecutar en el SQL Editor de Supabase
-- IMPORTANTE: Reiniciar el servidor API después de ejecutar para limpiar cache

INSERT INTO analisis_resultado (resultado_id, analisis_id, valor, unidad, out_of_range, comentario, parametro_id)
SELECT
  gen_random_uuid(),
  a.analisis_id,
  0,
  'g',
  false,
  'Backfill: producto_principal = 0 (suma parametros = peso_muestra)',
  (SELECT parametro_id FROM parametro WHERE codigo = 'producto_principal')
FROM analisis a
WHERE a.estado = 'completo'
  AND NOT EXISTS (
    SELECT 1 FROM analisis_resultado ar
    JOIN parametro p ON p.parametro_id = ar.parametro_id
    WHERE ar.analisis_id = a.analisis_id AND p.codigo = 'producto_principal'
  );

-- Verificar
SELECT
  a.analisis_id,
  ar.valor as producto_principal,
  ar.comentario
FROM analisis a
JOIN analisis_resultado ar ON ar.analisis_id = a.analisis_id
JOIN parametro p ON p.parametro_id = ar.parametro_id
WHERE a.estado = 'completo'
  AND p.codigo = 'producto_principal'
ORDER BY a.created_at DESC;
