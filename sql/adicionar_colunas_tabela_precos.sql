-- ============================================================
-- Adicionar colunas de precos por tipo de veiculo e regras
-- avancadas a tabela 'tabela_precos'
-- ============================================================

alter table public.tabela_precos add column if not exists fracionamento_minutos int default 60;
alter table public.tabela_precos add column if not exists tarifa_minima numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists meia_estadia_minutos int default 0;
alter table public.tabela_precos add column if not exists meia_estadia_valor numeric(10,2) default 0;

-- Precos por tipo de veiculo: CARRO GRANDE
alter table public.tabela_precos add column if not exists carro_grande_primeira_hora numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists carro_grande_hora_adicional numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists carro_grande_diaria numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists carro_grande_valor_minuto numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists carro_grande_valor_maximo_diario numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists carro_grande_mensal numeric(10,2) default 0;

-- Precos por tipo de veiculo: MOTO
alter table public.tabela_precos add column if not exists moto_primeira_hora numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists moto_hora_adicional numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists moto_diaria numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists moto_valor_minuto numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists moto_valor_maximo_diario numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists moto_mensal numeric(10,2) default 0;

-- Precos por tipo de veiculo: CAMINHONETE
alter table public.tabela_precos add column if not exists caminhonete_primeira_hora numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists caminhonete_hora_adicional numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists caminhonete_diaria numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists caminhonete_valor_minuto numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists caminhonete_valor_maximo_diario numeric(10,2) default 0;
alter table public.tabela_precos add column if not exists caminhonete_mensal numeric(10,2) default 0;
