-- Tabela de perfis de acesso personalizados
-- Execute no SQL Editor do Supabase

CREATE TABLE IF NOT EXISTS perfis (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(50) NOT NULL UNIQUE,   -- slug usado nos usuarios e permissoes (ex: gerencia, supervisao, manobrista)
  nome VARCHAR(100) NOT NULL,           -- nome exibido (ex: Gerencia)
  descricao TEXT,                       -- descricao do perfil
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMPTZ DEFAULT NOW(),
  alterado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Garante que os perfis base sempre existam (admin nunca pode ser alterado/inativado)
INSERT INTO perfis (codigo, nome, descricao, ativo)
VALUES
  ('admin', 'Administrador', 'Acesso total a todos os modulos e acoes do sistema.', TRUE),
  ('supervisor', 'Supervisor', 'Gestao e autorizacoes, sem acesso total.', TRUE),
  ('operador', 'Operador', 'Operacao diaria do estacionamento.', TRUE)
ON CONFLICT (codigo) DO UPDATE SET
  nome = EXCLUDED.nome,
  descricao = EXCLUDED.descricao,
  ativo = TRUE;

-- Indices
CREATE INDEX IF NOT EXISTS idx_perfis_ativo ON perfis(ativo);
CREATE INDEX IF NOT EXISTS idx_perfis_codigo ON perfis(codigo);

-- Desabilita RLS para permitir acesso via chave anonima do Supabase
ALTER TABLE IF EXISTS perfis DISABLE ROW LEVEL SECURITY;

-- Grant de acesso (caso use roles diferentes no Supabase)
GRANT ALL ON TABLE perfis TO anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE perfis_id_seq TO anon, authenticated;
