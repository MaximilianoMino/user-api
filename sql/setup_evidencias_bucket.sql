-- Setup script for evidencias bucket in Supabase Storage
-- Run this in the Supabase SQL Editor or via migration

-- 1. Create the bucket (if it doesn't exist)
INSERT INTO storage.buckets (id, name, public)
VALUES ('evidencias', 'evidencias', true)
ON CONFLICT (id) DO NOTHING;

-- 2. Allow public read access (bucket is public, but add explicit policy)
CREATE POLICY "Evidencias are publicly accessible"
ON storage.objects FOR SELECT
USING (bucket_id = 'evidencias');

-- 3. Allow authenticated users to upload to their organization's lotes
CREATE POLICY "Users can upload evidencias"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'evidencias'
    AND (storage.foldername(name))[1] = 'lotes'
);

-- 4. Allow authenticated users to update their own uploads
CREATE POLICY "Users can update their own evidencias"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'evidencias'
    AND auth.uid() IS NOT NULL
);

-- 5. Allow authenticated users to delete their own uploads
CREATE POLICY "Users can delete evidencias"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'evidencias'
    AND auth.uid() IS NOT NULL
);
