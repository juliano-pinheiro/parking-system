-- ============================================================
-- Habilitar acesso a tabela 'permissoes' para a aplicacao
-- (desabilita Row Level Security, como nas demais tabelas do sistema)
-- ============================================================

alter table public.permissoes disable row level security;

grant all on table public.permissoes to anon, authenticated, service_role;
grant usage on sequence public.permissoes_id_seq to anon, authenticated, service_role;

-- ============================================================
-- Seed das permissoes padrao (caso a tabela esteja vazia)
-- ============================================================

-- OPERADOR
insert into public.permissoes (perfil, modulo, acao) values
    ('operador', 'caixa', 'ver'),
    ('operador', 'caixa', 'criar'),
    ('operador', 'caixa', 'fechar_caixa'),
    ('operador', 'pagamentos', 'ver'),
    ('operador', 'pagamentos', 'criar'),
    ('operador', 'pagamentos', 'cancelar'),
    ('operador', 'formas_pagamento', 'ver'),
    ('operador', 'tabela_precos', 'ver'),
    ('operador', 'descontos', 'ver'),
    ('operador', 'cortesias', 'ver'),
    ('operador', 'cortesias', 'criar'),
    ('operador', 'mensalistas', 'ver'),
    ('operador', 'mensalistas', 'criar'),
    ('operador', 'mensalistas', 'editar'),
    ('operador', 'convenios', 'ver'),
    ('operador', 'contas_receber', 'ver'),
    ('operador', 'estornos', 'ver'),
    ('operador', 'auditoria', 'ver'),
    ('operador', 'dashboard_financeiro', 'ver'),
    ('operador', 'relatorios', 'ver'),
    ('operador', 'usuarios', 'ver')
on conflict (perfil, modulo, acao) do nothing;

-- SUPERVISOR
insert into public.permissoes (perfil, modulo, acao) values
    ('supervisor', 'caixa', 'ver'),
    ('supervisor', 'caixa', 'criar'),
    ('supervisor', 'caixa', 'editar'),
    ('supervisor', 'caixa', 'fechar_caixa'),
    ('supervisor', 'pagamentos', 'ver'),
    ('supervisor', 'pagamentos', 'criar'),
    ('supervisor', 'pagamentos', 'editar'),
    ('supervisor', 'pagamentos', 'cancelar'),
    ('supervisor', 'pagamentos', 'estornar'),
    ('supervisor', 'formas_pagamento', 'ver'),
    ('supervisor', 'formas_pagamento', 'criar'),
    ('supervisor', 'formas_pagamento', 'editar'),
    ('supervisor', 'tabela_precos', 'ver'),
    ('supervisor', 'tabela_precos', 'editar'),
    ('supervisor', 'descontos', 'ver'),
    ('supervisor', 'descontos', 'criar'),
    ('supervisor', 'descontos', 'editar'),
    ('supervisor', 'descontos', 'autorizar'),
    ('supervisor', 'cortesias', 'ver'),
    ('supervisor', 'cortesias', 'criar'),
    ('supervisor', 'cortesias', 'editar'),
    ('supervisor', 'cortesias', 'autorizar'),
    ('supervisor', 'mensalistas', 'ver'),
    ('supervisor', 'mensalistas', 'criar'),
    ('supervisor', 'mensalistas', 'editar'),
    ('supervisor', 'mensalistas', 'excluir'),
    ('supervisor', 'convenios', 'ver'),
    ('supervisor', 'convenios', 'criar'),
    ('supervisor', 'convenios', 'editar'),
    ('supervisor', 'convenios', 'excluir'),
    ('supervisor', 'contas_receber', 'ver'),
    ('supervisor', 'contas_receber', 'criar'),
    ('supervisor', 'contas_receber', 'editar'),
    ('supervisor', 'contas_receber', 'excluir'),
    ('supervisor', 'estornos', 'ver'),
    ('supervisor', 'estornos', 'criar'),
    ('supervisor', 'estornos', 'estornar'),
    ('supervisor', 'auditoria', 'ver'),
    ('supervisor', 'dashboard_financeiro', 'ver'),
    ('supervisor', 'relatorios', 'ver'),
    ('supervisor', 'usuarios', 'ver'),
    ('supervisor', 'usuarios', 'criar'),
    ('supervisor', 'usuarios', 'editar')
on conflict (perfil, modulo, acao) do nothing;
