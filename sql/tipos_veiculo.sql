-- ============================================================
-- TIPOS DE VEICULO
-- Executar no SQL Editor do Supabase.
--
-- Cria a tabela de tipos de veiculo por empresa. Os quatro tipos
-- do sistema (Carro, Moto, Carro Grande, Caminhonete) sao semeados
-- automaticamente pelo aplicativo na primeira carga e nao podem ser
-- excluidos. Tipos personalizados podem ter precos proprios; campos
-- zerados herdam os precos de carro.
-- ============================================================

CREATE TABLE IF NOT EXISTS tipos_veiculo (
    id INTEGER PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    nome TEXT NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TEXT,
    primeira_hora NUMERIC NOT NULL DEFAULT 0,
    hora_adicional NUMERIC NOT NULL DEFAULT 0,
    diaria NUMERIC NOT NULL DEFAULT 0,
    valor_minuto NUMERIC NOT NULL DEFAULT 0,
    valor_maximo_diario NUMERIC NOT NULL DEFAULT 0,
    mensal NUMERIC NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tipos_veiculo_empresa ON tipos_veiculo(empresa_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tipos_veiculo_empresa_nome ON tipos_veiculo(empresa_id, nome);

-- Libera o acesso (mesmo padrao das demais tabelas do sistema)
ALTER TABLE tipos_veiculo DISABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE tipos_veiculo TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
