-- Script para insertar parámetros estándar de análisis
-- Ejecución: psql -h <host> -d <database> -U <user> -f insert_parametros_analisis.sql

-- Insertar parámetros por defecto para análisis de calidad
INSERT INTO public.parametro (codigo, value_type, unidad_default, activo, created_by, updated_by) VALUES
  ('humedad', 'porcentaje', '%', true, 0, 0),
  ('impurezas', 'porcentaje', '%', true, 0, 0),
  ('granos_partidos', 'porcentaje', '%', true, 0, 0),
  ('proteina', 'porcentaje', '%', true, 0, 0),
  ('producto_principal', 'peso', 'g', true, 0, 0)
ON CONFLICT (codigo) DO NOTHING;

-- Verificar inserción
SELECT parametro_id, codigo, value_type, unidad_default, activo
FROM public.parametro
WHERE codigo IN ('humedad', 'impurezas', 'granos_partidos', 'proteina', 'producto_principal')
ORDER BY codigo;