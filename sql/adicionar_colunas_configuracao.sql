-- Adiciona colunas extras na tabela configuracao para suportar
-- um painel de configuracoes mais completo.
-- Execute no SQL Editor do Supabase.

ALTER TABLE configuracao
  ADD COLUMN IF NOT EXISTS cnpj VARCHAR(20),
  ADD COLUMN IF NOT EXISTS telefone VARCHAR(20),
  ADD COLUMN IF NOT EXISTS endereco TEXT,
  ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),
  ADD COLUMN IF NOT EXISTS estado VARCHAR(2),
  ADD COLUMN IF NOT EXISTS cep VARCHAR(10),
  ADD COLUMN IF NOT EXISTS horario_abertura TIME,
  ADD COLUMN IF NOT EXISTS horario_fechamento TIME,
  ADD COLUMN IF NOT EXISTS cabecalho_ticket TEXT,
  ADD COLUMN IF NOT EXISTS rodape_ticket TEXT,
  ADD COLUMN IF NOT EXISTS bloquear_sem_vaga BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS exigir_observacao BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS vagas_carro INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS vagas_moto INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS vagas_carro_grande INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS vagas_caminhonete INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS pix_tipo VARCHAR(20),
  ADD COLUMN IF NOT EXISTS pix_chave VARCHAR(255),
  ADD COLUMN IF NOT EXISTS alterado_em TIMESTAMPTZ DEFAULT NOW();

-- Atualiza o registro existente com valores padrao
UPDATE configuracao
SET
  bloquear_sem_vaga = COALESCE(bloquear_sem_vaga, FALSE),
  exigir_observacao = COALESCE(exigir_observacao, TRUE),
  vagas_carro = COALESCE(vagas_carro, 0),
  vagas_moto = COALESCE(vagas_moto, 0),
  vagas_carro_grande = COALESCE(vagas_carro_grande, 0),
  vagas_caminhonete = COALESCE(vagas_caminhonete, 0)
WHERE id = 1;

-- Desabilita RLS (caso a tabela ainda nao esteja aberta para anon)
ALTER TABLE IF EXISTS configuracao DISABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE configuracao TO anon, authenticated;
