-- ============================================================
-- ADICIONA A COLUNA 'nome_estacionamento' NA TABELA 'configuracao'
-- Execute este script no SQL Editor do Supabase
-- ============================================================
alter table public.configuracao
    add column if not exists nome_estacionamento text default 'Estaciona Parking';
