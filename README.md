# Sistema de Estacionamento com Controle por Ticket

Sistema completo de gerenciamento de estacionamento, com **interface web (Flask)** e
**interface de terminal**, compartilhando as mesmas regras de negocio. Os dados sao
persistidos no **Supabase (PostgreSQL)**.

- **Web** (`app.py`): painel completo no navegador com login, multi-empresa, financeiro,
  caixa, relatorios e controle de acesso por perfil.
- **Terminal** (`main.py`): menu interativo via linha de comando, sem dependencias externas.

## Funcionalidades

### Operacao
- Emissao de ticket na entrada: numero sequencial, placa, vaga, tipo de veiculo, data/hora.
- Registro de saida com calculo automatico do valor (primeira hora + adicionais, fracionamento,
  diaria, meia estadia, tabela noturna/fim de semana/feriado, pernoite).
- Controle de vagas em tempo real, com vagas separadas por tipo de veiculo (carro, moto,
  carro grande, caminhonete) e mapa de vagas visual.
- Ticket perdido (com tarifa configurável e exigencia de autorizacao).
- Lista negra de placas, reservas de vaga e registro de ocorrencias.
- Impressao de ticket com codigo de barras (barcode SVG).

### Financeiro
- Caixa: abertura/fechamento, sangria, suprimento, totais por forma de pagamento.
- Pagamentos (dinheiro, PIX, cartao etc.) com formas de pagamento configuraveis.
- Cancelamento e estorno de pagamentos com autorizacao.
- Financeiro: lancamentos manuais, contas a receber, convenios, mensalistas com mensalidades
  e controle de inadimplencia, descontos e cortesias.
- Emissao de NFSe simplificada (com cancelamento).
- Dashboard financeiro (receita do dia/mes/ano, ticket medio) e relatorio financeiro com
  agrupamento por dia/semana/mes, exportavel em **CSV e PDF**.
- Relatorio de ocupacao e DRE (receita bruta, descontos, cortesias, estornos).

### Administracao
- **Multi-empresa (multi-CNPJ)**: cadastro de empresas e isolamento dos dados por CNPJ.
- **Autenticacao**: login com email/senha, troca de senha, usuarios por empresa.
- **Perfis e permissoes**: perfis (admin, supervisor, operador, etc.), matriz de permissoes
  por modulo e acao, clonagem de perfil, aplicacao no menu e nas APIs.
- **Auditoria**: registro de alteracoes e logs de acesso (com filtros e exportacao CSV).
- **Notificacoes**: central de avisos de vencimento/inadimplencia de mensalistas.
- **Backup**: exportacao completa do backup da empresa ativa em JSON.

## Arquitetura

```
parking-system/
├── app.py                          # Interface web (Flask): cria o app e registra os blueprints
├── main.py                         # Interface terminal (menu interativo)
├── services_registry.py            # Instancias dos servicos + helpers (auth, permissoes, serializacao)
├── routes/                         # Blueprints da API (cada modulo um arquivo)
│   ├── auth.py                     # Login, sessao, troca de senha, troca de empresa
│   ├── operacao.py                 # Status, vagas, dashboard, entrada/saida, ticket perdido
│   ├── financeiro.py               # Financeiro, caixa, pagamentos, estornos, formas
│   ├── precos.py                   # Configuracoes, tabela de precos, tipos, descontos, cortesias
│   ├── clientes.py                 # Clientes, mensalistas, convenios, contas a receber
│   ├── administracao.py            # Usuarios, empresas, perfis, permissoes, auditoria
│   ├── relatorios.py               # Movimentacao, financeiro (CSV/PDF), ocupacao, DRE
│   ├── extras.py                   # NFSe, lista negra, reservas, ocorrencias, backup
│   └── paginas.py                  # Frontend (/) e login (/login)
├── supabase_client.py              # Cliente do Supabase (carregado do .env)
├── requirements.txt                # Dependencias do projeto (pip install -r)
├── models/                         # Modelos de dados (dataclasses)
│   ├── ticket.py, configuracao.py, cliente.py, usuario.py, empresa.py ...
│   └── (financeiro, caixa, pagamento, mensalista, convenio, nfse, etc.)
├── services/                       # Regras de negocio e persistencia
│   ├── estacionamento_service.py   # Regras principais (entrada, saida, calculo)
│   ├── persistencia_service.py     # Acesso ao Supabase (tickets, configuracao)
│   ├── base_supabase_service.py    # Base CRUD para os demais modulos
│   └── ... (um servico por modulo)
├── sql/                            # Scripts SQL para o Supabase (criacao/evolucao)
├── templates/
│   ├── index.html                  # SPA principal (painel)
│   └── login.html                  # Pagina de login
├── static/
│   ├── css/style.css
│   └── js/app.js                   # Logica do frontend (consumo da API)
├── tests/                          # Testes de integracao (test client do Flask)
└── data/                           # Pasta de dados locais (gerada automaticamente)
```

## Requisitos

- Python 3.10 ou superior.
- Um projeto [Supabase](https://supabase.com) com as tabelas criadas (ver abaixo).
- Dependencias: `Flask`, `supabase`, `python-dotenv` e `reportlab` (apenas para a interface
  web; a versao terminal nao exige bibliotecas externas).

## Configuracao inicial

1. **Instale as dependencias** (interface web):

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure o `.env`** na raiz do projeto, apontando para o seu projeto Supabase:

   ```
   SUPABASE_URL=https://SEU-PROJETO.supabase.co
   SUPABASE_KEY=sua-service-role-key-ou-anon-key
   ```

3. **Crie as tabelas no Supabase**: execute os scripts da pasta `sql/` no SQL Editor do
   Supabase, na ordem adequada:
   - `sql/criar_tabela_financeiro.sql` e `sql/criar_tabelas_financeiro.sql` (tabelas base)
   - `sql/criar_tabela_perfis.sql`, `sql/criar_tabela_permissoes.sql`
   - `sql/criar_multi_empresa.sql` (empresas e coluna empresa_id)
   - `sql/modulos_avancados.sql` (nfse, lista negra, reservas, ocorrencias)
   - `sql/tipos_veiculo.sql`
   - `sql/adicionar_colunas_*.sql` e `sql/correcao_colunas_pendentes.sql` (evolucao)
   - `sql/corrigir_rls_empresas.sql` (ajusta Row Level Security para acesso via chave do app)

   > Os scripts usam `IF NOT EXISTS` / `IF EXISTS` e podem ser executados mais de uma vez.

> A migracao dos dados locais (JSON) para o Supabase ja foi concluida: o sistema le e
> grava tudo diretamente no Supabase. Nao ha mais arquivos JSON em uso.

## Como executar

### Interface web

```bash
python app.py
```

Acesse [http://127.0.0.1:5000](http://127.0.0.1:5000). Faca login com um usuario
cadastrado (perfis: `admin`, `supervisor`, `operador`, etc.). A tela inicial e o
**Dashboard**, com o menu lateral para: Registrar Entrada/Saida, Pátio/Vagas, Financeiro,
Caixa, Mensalistas, Clientes, Relatorios, Configuracoes, Usuarios, Empresas, Permissoes,
Auditoria, NFSe, Lista Negra, Reservas, Ocorrencias e Avisos.

### Interface terminal

```bash
python main.py
```

Menu numerico com: Registrar Entrada, Registrar Saida, Controle de Vagas, Relatorio e
Configuracoes. Usa as mesmas regras de negocio e o mesmo banco (Supabase) da versao web.

## Executar os testes

Os testes usam o test client do Flask (em memoria, sem servidor e sem dados reais):

```bash
pip install -r requirements.txt   # inclui pytest na secao de desenvolvimento
python -m pytest tests/ -v
```

Cobrem paginas publicas, rotas publicas da API, redirecionamentos de autenticacao e a
protecao das rotas que exigem sessao. Nao dependem de credenciais nem de dados do banco.

## Primeiro acesso

Para criar o primeiro usuario (admin), execute no SQL Editor do Supabase ou utilize um
script de bootstrap:

```sql
-- Exemplo: criar um usuario admin (substitua os valores)
INSERT INTO usuarios (nome, email, senha, perfil, master, ativo)
VALUES ('Administrador', 'admin@exemplo.com', '<hash-da-senha>', 'admin', TRUE, TRUE);
```

> A senha e armazenada como hash. O cadastro de usuarios tambem pode ser feito pela tela
> **Usuarios** no painel web, desde que exista ao menos um usuario master/admin.

## Observacoes

- Placas sao armazenadas em letras maiusculas.
- Nao e permitido registrar duas entradas abertas para a mesma placa.
- Ao reduzir o total de vagas, o sistema impede valores menores que a quantidade de
  veiculos ja estacionados.
- Os dados sao persistidos no Supabase; a pasta `data/` e ignorada pelo `.gitignore`.
