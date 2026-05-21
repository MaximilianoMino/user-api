-- Migration: Add auth_user_id to public.usuario table
-- Date: 2025-01-19
-- Description: Add UUID column to link Supabase Auth users with local user profile

-- Add auth_user_id column (UUID, unique, not null)
ALTER TABLE public.usuario
ADD COLUMN IF NOT EXISTS auth_user_id UUID UNIQUE;

-- Allow NULL in created_by and updated_by (for system user handling)
ALTER TABLE public.usuario
ALTER COLUMN created_by DROP NOT NULL;
ALTER TABLE public.usuario
ALTER COLUMN updated_by DROP NOT NULL;

-- Optional: Add unique constraint on auth_user_id if not already added
-- This ensures each Supabase user can only have one profile
-- ALTER TABLE public.usuario ADD CONSTRAINT usuario_auth_user_id_unique UNIQUE (auth_user_id);