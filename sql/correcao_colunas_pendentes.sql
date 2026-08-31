-- ============================================================
-- CORRECAO DE COLUNAS PENDENTES
-- Executar no SQL Editor do Supabase.
--
-- Adiciona colunas que faltam em tabelas criadas antes de
-- scripts mais recentes:
--   1. tickets.forma_pagamento  (usada ao registrar a saida)
--   2. clientes.empresa_id      (isolamento de dados por CNPJ)
-- ============================================================

-- 1) tickets: forma de pagamento usada na saida do veiculo
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS forma_pagamento text;

-- 2) clientes: vinculo com a empresa (multi-CNPJ)
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);

-- 3) Preenche a empresa padrao nos registros existentes sem empresa
UPDATE tickets  SET empresa_id = (SELECT MIN(id) FROM empresas) WHERE empresa_id IS NULL;
UPDATE clientes SET empresa_id = (SELECT MIN(id) FROM empresas) WHERE empresa_id IS NULL;

-- 4) Indice de filtro por empresa
CREATE INDEX IF NOT EXISTS idx_clientes_empresa ON clientes(empresa_id);

-- 5) Recarrega o cache de schema do PostgREST
NOTIFY pgrst, 'reload schema';
