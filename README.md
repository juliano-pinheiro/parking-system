# Sistema de Estacionamento com Controle por Ticket

Sistema completo e profissional de gerenciamento de estacionamento, com **interface web moderna e responsiva (Flask)** e **interface de terminal**, compartilhando as mesmas regras de negócio. Os dados são persistidos no **Supabase (PostgreSQL)** com suporte multi-empresa.

- **Web** (`app.py`): painel completo no navegador com login, multi-empresa (multi-CNPJ), dashboard financeiro executivo, controle de caixa, relatórios gerenciais, checkout ágil, acesso mobile para operadores e controle granular de permissões (RBAC).
- **Terminal** (`main.py`): menu interativo via linha de comando, sem dependências externas.

---

## Principais Funcionalidades

### 🚗 Operação de Pátio & Entrada/Saída
- **Emissão de Ticket**: placa no padrão Mercosul com formatação automática, categoria do veículo (Carro, Moto, Camionete, etc.), seletor de cores/avarias rápidas, vaga e data/hora.
- **Bloqueio Mandatório sem Caixa**: emissão de tickets e cobrança de tickets perdidos bloqueadas automaticamente caso o caixa do dia esteja fechado.
- **Hero Banner de Ocupação**: monitoramento visual da lotação do pátio em tempo real com barra de progresso, taxa percentual e vagas disponíveis.
- **Checkout de Saída & Pagamento**:
  - Pré-cálculo automático do valor com base no tempo de permanência e tabela de preços vigente (`GET /api/saida/calcular`).
  - Resumo do veículo (placa, tipo, vaga, permanência e observações).
  - Exibição em destaque do valor total a pagar e calculadora de troco para pagamentos em dinheiro.
  - Identificação de **Mensalistas** com isenção automática (`R$ 0,00`).
  - Emissão e abertura automática do comprovante/recibo pronto para impressão imediata.
- **Valores Acumulados em Tempo Real**: acompanhamento na lista do pátio do valor acumulado até o momento para cada veículo estacionado.
- **Ticket Perdido com Liberação de Vaga**: encerramento do ticket aberto da placa correspondente, liberando a vaga no sistema e gerando o lançamento financeiro.
- **Impressão de Tickets e Comprovantes**: suporte a bobinas térmicas (80mm e 58mm) ou A4, com código de barras SVG e cabeçalho/rodapé customizáveis.
- **Mapa Visual de Vagas**: visualização interativa de todas as vagas do pátio (livres e ocupadas com placa e categoria).

### 📱 Acesso Mobile & Terminal do Operador
- **QR Code de Acesso Rápido**: o sistema detecta o IP da rede local Wi-Fi e gera um QR Code na tela. O operador aponta a câmera do smartphone e acessa o sistema na hora.
- **Barra Inferior Rápida (Bottom Bar)**: interface 100% otimizada para toque em celulares e coletores POS, com atalhos para Entrada, Pátio, Saída, Mapa de Vagas e Menu.
- **Servidor com Vínculo Externo**: Flask configurado em `0.0.0.0` para permitir acesso de múltiplos aparelhos na rede local.

### 💰 Financeiro & Caixa
- **Caixa Completo**: abertura com fundo de troco, sangria, suprimento, fechamento cego/conferido e extrato detalhado de movimentações.
- **Dashboard Financeiro Executivo**:
  - Cockpit de KPIs: Receita do Dia, Mês, Ano, Volume de Atendimentos e Ticket Médio.
  - Painel de Evolução com alternância de abas: Diário (30 dias), Mensal (12 meses) e Anual (5 anos).
  - Mix de Meios de Pagamento: Gráfico Donut acompanhado de tabela analítica com valores e percentuais.
  - Curva de Fluxo por Horário (24h) com badge de identificação do **Horário de Pico do Dia**.
  - Ranking de Produtividade dos Operadores e Balanço Comparativo Mensal.
- **Relatório por Formas de Pagamento**: extrato analítico com filtro por período, forma de pagamento, métricas consolidadas e exportação CSV.
- **DRE e Relatório de Ocupação**: demonstrativo de resultado com receita bruta, descontos, cortesias, estornos e resultado líquido.
- **NFSe Simplificada**: emissão e cancelamento de notas fiscais de serviço.

### 🏢 Administração, Segurança & Multi-CNPJ
- **Multi-Empresa (Multi-CNPJ)**: isolamento completo de tickets, caixa, financeiro e configurações por empresa/filial, com troca rápida no cabeçalho.
- **Central de Permissões (RBAC)**: catálogo de módulos e ações (`ver`, `criar`, `editar`, `excluir`, `autorizar`), personalização de acessos e clonagem de perfis.
- **Auditoria Completa**: trilha de auditoria registrando todas as operações críticas com filtro e exportação CSV.
- **Contas a Receber, Mensalistas & Convênios**: controle de mensalidades com status de adimplência, bloqueio automático de inadimplentes na entrada e convênios comerciais.
- **Backup Completo**: exportação em formato JSON de toda a base da empresa ativa.

---

## Arquitetura do Projeto

```
parking-system/
├── app.py                          # Ponto de entrada Flask (host 0.0.0.0)
├── main.py                         # Interface terminal (modo texto)
├── services_registry.py            # Registry de serviços, RBAC e serializadores
├── routes/                         # Blueprints da API REST
│   ├── auth.py                     # Login, sessão, troca de senha e empresa
│   ├── operacao.py                 # Pátio, entrada, checkout, pré-cálculo e acesso mobile
│   ├── financeiro.py               # Dashboard financeiro, caixa, pagamentos, formas
│   ├── precos.py                   # Tabela de preços, configurações e tipos de veículo
│   ├── clientes.py                 # Clientes, mensalistas, convênios e contas a receber
│   ├── administracao.py            # Usuários, empresas, perfis RBAC e auditoria
│   ├── relatorios.py               # Relatórios financeiros, formas de pagamento, DRE
│   ├── extras.py                   # NFSe, lista negra, reservas, ocorrências, backup
│   └── paginas.py                  # Servidor de páginas HTML
├── models/                         # Dataclasses de domínio (Ticket, Caixa, Empresa, etc.)
├── services/                       # Serviços de negócio e persistência Supabase
├── sql/                            # Scripts de banco de dados PostgreSQL (Supabase)
├── templates/
│   ├── index.html                  # SPA principal com todos os módulos e modais
│   └── login.html                  # Tela de autenticação moderna
├── static/
│   ├── css/style.css               # Folha de estilos completa e responsiva
│   └── js/app.js                   # Lógica e interatividade do frontend
└── tests/                          # Suíte de testes automatizados
    ├── run_tests.py                # Executor unificado de testes
    ├── test_routes.py              # Testes de rotas públicas e autenticação
    ├── test_fluxos_principais.py   # Testes de pátio, checkout, dashboard e mobile
    ├── test_caixa_otimizado.py     # Testes de caixa, sangrias e bloqueio de tickets
    ├── test_permissoes_detalhadas.py# Testes da central de permissões RBAC
    ├── test_configuracoes_revisadas.py # Testes de validação de configurações
    └── test_relatorio_pagamentos.py# Testes de relatórios e filtros
```

---

## Configuração Inicial

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure o `.env`**:
   ```env
   SUPABASE_URL=https://SEU-PROJETO.supabase.co
   SUPABASE_KEY=sua-service-role-key-ou-anon-key
   SECRET_KEY=sua-chave-secreta
   ```

3. **Banco de dados**:
   Execute os scripts SQL na pasta `sql/` no editor do Supabase.

---

## Publicação da Aplicação

O GitHub Pages hospeda apenas arquivos estáticos e **não executa o Flask nem a
API** usada pelo sistema. Para publicar a aplicação completa, conecte este
repositório ao Render e crie um Web Service usando o arquivo `render.yaml`.
Essa configuração usa o plano gratuito e persiste os dados da aplicação no
Supabase. Configure `SUPABASE_URL` e `SUPABASE_KEY` como variáveis secretas do
serviço; `SECRET_KEY` é gerada automaticamente pelo Render. O serviço usa um
worker Gunicorn para evitar divergência entre estado mantido em memória por
workers distintos.

Antes do primeiro deploy, configure o projeto Supabase e aplique as migrações
necessárias em `sql/` no SQL Editor. Esses arquivos são scripts incrementais
para tabelas existentes; eles não compõem um instalador completo para um banco
vazio, e o Render não os executa automaticamente.

O deploy de produção inicia com Gunicorn. `FLASK_DEBUG` fica desativado por
padrão; só habilite o modo debug localmente quando necessário.

### Execução local

### Interface Web
```bash
python app.py
```
Acesse `http://localhost:5000` (ou utilize o IP e QR Code exibidos pelo menu **Acesso Mobile** para conectar pelo celular).

### Interface Terminal
```bash
python main.py
```

---

## Testes Automatizados

O sistema inclui uma suíte de testes automatizados:

```bash
python tests/run_tests.py
```
*(Executa 37 testes automatizados cobrindo rotas, bloqueio sem caixa aberto, pré-cálculo de pátio, liberação de vaga em ticket perdido, dashboard financeiro, RBAC, multi-CNPJ, persistência e relatórios).*
