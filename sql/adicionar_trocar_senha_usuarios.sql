-- ============================================================
-- ADICIONA A COLUNA 'trocar_senha_no_proximo_acesso' NA TABELA 'usuarios'
-- Execute este script no SQL Editor do Supabase
-- ============================================================
alter table public.usuarios
    add column if not exists trocar_senha_no_proximo_acesso boolean default false;
