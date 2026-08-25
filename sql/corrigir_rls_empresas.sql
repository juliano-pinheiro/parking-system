-- CORRECAO: empresas/perfis com RLS ativo e vazias
-- Execute no SQL Editor do Supabase (pode rodar quantas vezes precisar)

-- =====================================================
-- 1. EMPRESA PADRAO (se nao existir)
-- =====================================================
INSERT INTO empresas (cnpj, razao_social, nome_fantasia, ativo)
SELECT '00.000.000/0001-00', 'Empresa Padrao', 'Estacionamento Padrao', TRUE
WHERE NOT EXISTS (SELECT 1 FROM empresas WHERE cnpj = '00.000.000/0001-00');

-- =====================================================
-- 2. PERFIS BASE (se nao existirem)
-- =====================================================
INSERT INTO perfis (codigo, nome, descricao, ativo)
SELECT 'admin', 'Administrador', 'Acesso total a todos os modulos e acoes do sistema.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM perfis WHERE codigo = 'admin');

INSERT INTO perfis (codigo, nome, descricao, ativo)
SELECT 'supervisor', 'Supervisor', 'Gestao e autorizacoes, sem acesso total.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM perfis WHERE codigo = 'supervisor');

INSERT INTO perfis (codigo, nome, descricao, ativo)
SELECT 'operador', 'Operador', 'Operacao diaria do estacionamento.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM perfis WHERE codigo = 'operador');

-- =====================================================
-- 3. DESABILITAR RLS EM EMPRESAS E PERFIS
-- =====================================================
ALTER TABLE empresas DISABLE ROW LEVEL SECURITY;
ALTER TABLE perfis DISABLE ROW LEVEL SECURITY;

-- =====================================================
-- 4. GRANTS DE ACESSO (anon e authenticated)
-- =====================================================
GRANT ALL ON TABLE empresas TO anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE empresas_id_seq TO anon, authenticated;

GRANT ALL ON TABLE perfis TO anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE perfis_id_seq TO anon, authenticated;

-- =====================================================
-- 5. GARANTIR ADMIN MASTER
-- =====================================================
UPDATE usuarios SET master = TRUE WHERE email = 'admin@teste.com' OR perfil = 'admin';

-- =====================================================
-- 6. RECHECAR SE OUTRAS TABELAS ESTAO SEM RLS (idempotente)
-- =====================================================
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
ALTER TABLE IF EXISTS auditoria DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS logs_acesso DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS movimentacoes_caixa DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS clientes DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS permissoes DISABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE permissoes TO anon, authenticated;
