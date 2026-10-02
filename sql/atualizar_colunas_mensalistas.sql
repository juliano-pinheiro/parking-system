-- ============================================================
-- ATUALIZACAO: ADICIONAR PLACA E TIPO_VEICULO EM MENSALISTAS
-- Execute este script no SQL Editor do Supabase
-- ============================================================

ALTER TABLE IF EXISTS public.mensalistas ADD COLUMN IF NOT EXISTS placa TEXT;
ALTER TABLE IF EXISTS public.mensalistas ADD COLUMN IF NOT EXISTS tipo_veiculo TEXT DEFAULT 'Carro';

CREATE INDEX IF NOT EXISTS idx_mensalistas_placa ON public.mensalistas(placa);

