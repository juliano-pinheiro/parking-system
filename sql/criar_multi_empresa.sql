-- Multi-empresa: cria tabela de empresas e adiciona empresa_id nas tabelas existentes
-- Execute no SQL Editor do Supabase

-- =====================================================
-- 1. TABELA DE EMPRESAS (ESTACIONAMENTOS)
-- =====================================================
CREATE TABLE IF NOT EXISTS empresas (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(20) NOT NULL UNIQUE,
  razao_social VARCHAR(200) NOT NULL,
  nome_fantasia VARCHAR(200) NOT NULL,
  telefone VARCHAR(20),
  email VARCHAR(200),
  endereco TEXT,
  cidade VARCHAR(100),
  estado VARCHAR(2),
  cep VARCHAR(10),
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMPTZ DEFAULT NOW(),
  alterado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas(cnpj);
CREATE INDEX IF NOT EXISTS idx_empresas_ativo ON empresas(ativo);

-- Empresa padrao (sera usada para migrar dados existentes)
INSERT INTO empresas (cnpj, razao_social, nome_fantasia, ativo)
VALUES ('00.000.000/0001-00', 'Empresa Padrao', 'Estacionamento Padrao', TRUE)
ON CONFLICT (cnpj) DO NOTHING;

-- =====================================================
-- 2. ADICIONAR empresa_id NAS TABELAS EXISTENTES
-- =====================================================

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS master BOOLEAN DEFAULT FALSE;

ALTER TABLE configuracao ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE caixas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE formas_pagamento ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE tabela_precos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE descontos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE cortesias ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE mensalistas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE mensalidades ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE convenios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE contas_receber ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE sangrias ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE suprimentos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE estornos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);
ALTER TABLE financeiro ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id);

-- =====================================================
-- 3. MIGRAR DADOS EXISTENTES PARA EMPRESA PADRAO
-- =====================================================
DO $$
DECLARE
  v_empresa_id INTEGER;
BEGIN
  SELECT id INTO v_empresa_id FROM empresas WHERE cnpj = '00.000.000/0001-00' LIMIT 1;

  IF v_empresa_id IS NOT NULL THEN
    UPDATE usuarios SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE configuracao SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE tickets SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE caixas SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE pagamentos SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE formas_pagamento SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE tabela_precos SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE descontos SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE cortesias SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE mensalistas SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE mensalidades SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE convenios SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE contas_receber SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE sangrias SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE suprimentos SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE estornos SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
    UPDATE financeiro SET empresa_id = v_empresa_id WHERE empresa_id IS NULL;
  END IF;
END $$;

-- =====================================================
-- 4. GARANTIR QUE O USUARIO EXISTENTE admin SEJA MASTER
-- =====================================================
UPDATE usuarios SET master = TRUE WHERE email = 'admin@teste.com' OR perfil = 'admin';

-- =====================================================
-- 5. INDICES PARA PERFORMANCE
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_usuarios_empresa ON usuarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_tickets_empresa ON tickets(empresa_id);
CREATE INDEX IF NOT EXISTS idx_caixas_empresa ON caixas(empresa_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_empresa ON pagamentos(empresa_id);
CREATE INDEX IF NOT EXISTS idx_configuracao_empresa ON configuracao(empresa_id);

-- =====================================================
-- 6. PERMISSOES
-- =====================================================
ALTER TABLE IF EXISTS empresas DISABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE empresas TO anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE empresas_id_seq TO anon, authenticated;

ALTER TABLE IF EXISTS usuarios DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS configuracao DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS caixas DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS pagamentos DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS formas_pagamento DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tabela_precos DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS descontos DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cortesias DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS mensalistas DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS mensalidades DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS convenios DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS contas_receber DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sangrias DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS suprimentos DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS estornos DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS financeiro DISABLE ROW LEVEL SECURITY;
