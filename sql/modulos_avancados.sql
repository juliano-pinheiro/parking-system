-- ============================================================
-- MODULOS AVANCADOS — Novas tabelas e colunas
-- Sistema de Estacionamento (Flask + Supabase)
-- Execute este script no SQL Editor do Supabase.
-- ============================================================

-- ------------------------------------------------------------
-- 1. NFSe (Nota Fiscal de Servico simplificada)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.nfse (
  id BIGINT PRIMARY KEY,
  numero BIGINT NOT NULL,
  ticket_numero BIGINT,
  placa TEXT,
  valor NUMERIC(12,2) NOT NULL DEFAULT 0,
  cpf_cnpj TEXT,
  razao_social TEXT,
  servico TEXT,
  data TEXT,
  usuario TEXT,
  status TEXT NOT NULL DEFAULT 'emitida',
  empresa_id BIGINT,
  criado_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_nfse_empresa ON public.nfse(empresa_id);
CREATE INDEX IF NOT EXISTS idx_nfse_ticket ON public.nfse(ticket_numero);
CREATE UNIQUE INDEX IF NOT EXISTS idx_nfse_empresa_numero ON public.nfse(empresa_id, numero);

-- ------------------------------------------------------------
-- 2. LISTA NEGRA (bloqueio de veiculos)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.lista_negra (
  id BIGINT PRIMARY KEY,
  placa TEXT NOT NULL,
  motivo TEXT,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  usuario TEXT,
  data TEXT,
  empresa_id BIGINT,
  criado_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_lista_negra_empresa ON public.lista_negra(empresa_id);
CREATE INDEX IF NOT EXISTS idx_lista_negra_placa ON public.lista_negra(placa);

-- ------------------------------------------------------------
-- 3. RESERVAS DE VAGA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reservas (
  id BIGINT PRIMARY KEY,
  cliente TEXT,
  telefone TEXT,
  placa TEXT,
  tipo_veiculo TEXT,
  vaga INTEGER,
  data_inicio TEXT,
  data_fim TEXT,
  valor NUMERIC(12,2) NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ativa',
  observacao TEXT,
  usuario TEXT,
  empresa_id BIGINT,
  criado_em TEXT,
  alterado_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_reservas_empresa ON public.reservas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_reservas_status ON public.reservas(status);

-- ------------------------------------------------------------
-- 4. OCORRENCIAS / TERMO DE AVARIAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ocorrencias (
  id BIGINT PRIMARY KEY,
  tipo TEXT NOT NULL DEFAULT 'avaria',
  placa TEXT,
  ticket_numero BIGINT,
  descricao TEXT,
  status TEXT NOT NULL DEFAULT 'aberta',
  usuario TEXT,
  autorizador TEXT,
  data TEXT,
  empresa_id BIGINT,
  criado_em TEXT,
  alterado_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_ocorrencias_empresa ON public.ocorrencias(empresa_id);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_placa ON public.ocorrencias(placa);

-- ------------------------------------------------------------
-- 5. TABELA DE PRECOS — novas colunas (ticket perdido + pernoite)
-- ------------------------------------------------------------
ALTER TABLE public.tabela_precos ADD COLUMN IF NOT EXISTS valor_ticket_perdido NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE public.tabela_precos ADD COLUMN IF NOT EXISTS pernoite_valor NUMERIC(12,2) NOT NULL DEFAULT 0;
ALTER TABLE public.tabela_precos ADD COLUMN IF NOT EXISTS pernoite_a_partir_horas INTEGER NOT NULL DEFAULT 12;

-- ------------------------------------------------------------
-- Libera acesso (padrao de RLS do projeto)
-- ------------------------------------------------------------
ALTER TABLE public.nfse DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.lista_negra DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.reservas DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ocorrencias DISABLE ROW LEVEL SECURITY;

GRANT ALL ON public.nfse TO anon, authenticated, service_role;
GRANT ALL ON public.lista_negra TO anon, authenticated, service_role;
GRANT ALL ON public.reservas TO anon, authenticated, service_role;
GRANT ALL ON public.ocorrencias TO anon, authenticated, service_role;
GRANT ALL ON public.tabela_precos TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
