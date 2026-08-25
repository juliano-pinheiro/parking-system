-- ============================================================
-- ADICIONA A COLUNA 'senha' NA TABELA 'usuarios'
-- Execute este script no SQL Editor do Supabase
-- ============================================================
alter table public.usuarios
    add column if not exists senha text default '';
