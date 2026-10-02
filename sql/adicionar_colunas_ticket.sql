-- Adiciona preferencias de impressao de ticket em bancos ja existentes.
ALTER TABLE public.configuracao
    ADD COLUMN IF NOT EXISTS ticket_exibir_cnpj BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS ticket_exibir_contato BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS ticket_formato_papel TEXT NOT NULL DEFAULT '80mm',
    ADD COLUMN IF NOT EXISTS ticket_exibir_codigo_barras BOOLEAN NOT NULL DEFAULT true;
