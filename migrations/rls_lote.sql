-- ============================================================
-- Row Level Security Policies for table: lote
-- ============================================================
-- Habilitar RLS en la tabla lote (si no está habilitado)
ALTER TABLE IF EXISTS lote ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Política de SELECT: Permite leer lotes de organizaciones
-- donde el usuario tiene rol en usuario_organizacion_rol
-- ============================================================
CREATE POLICY "Users can view lotes of their organizations"
ON lote
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM usuario_organizacion_rol uor
        JOIN public.usuario u ON u.user_id = uor.user_id
        WHERE uor.org_id = lote.org_id
        AND u.auth_user_id = auth.uid()
    )
);

-- ============================================================
-- Política de INSERT: Permite insertar lotes en organizaciones
-- donde el usuario tiene rol en usuario_organizacion_rol
-- ============================================================
CREATE POLICY "Users can create lotes in their organizations"
ON lote
FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM usuario_organizacion_rol uor
        JOIN public.usuario u ON u.user_id = uor.user_id
        WHERE uor.org_id = lote.org_id
        AND u.auth_user_id = auth.uid()
    )
);

-- ============================================================
-- Política de UPDATE: Permite actualizar lotes de organizaciones
-- donde el usuario tiene rol en usuario_organizacion_rol
-- ============================================================
CREATE POLICY "Users can update lotes of their organizations"
ON lote
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM usuario_organizacion_rol uor
        JOIN public.usuario u ON u.user_id = uor.user_id
        WHERE uor.org_id = lote.org_id
        AND u.auth_user_id = auth.uid()
    )
);

-- ============================================================
-- Política de DELETE: Permite eliminar lotes de organizaciones
-- donde el usuario tiene rol en usuario_organizacion_rol
-- (Solo soft delete, no se elimina realmente el registro)
-- ============================================================
CREATE POLICY "Users can delete lotes of their organizations"
ON lote
FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM usuario_organizacion_rol uor
        JOIN public.usuario u ON u.user_id = uor.user_id
        WHERE uor.org_id = lote.org_id
        AND u.auth_user_id = auth.uid()
    )
);

-- ============================================================
-- Verificar que las políticas se crearon correctamente
-- ============================================================
-- SELECT policyname, cmd, qual FROM pg_policies WHERE tablename = 'lote';