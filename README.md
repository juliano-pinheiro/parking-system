# Sistema de Estacionamento com Controle por Ticket

Sistema completo de gerenciamento de estacionamento desenvolvido em **Python**, com
persistencia de dados em arquivos **JSON**. Disponivel em duas interfaces que compartilham
as mesmas regras de negocio:

- **Terminal** (`main.py`): menu interativo via linha de comando, sem dependencias externas.
- **Web** (`app.py`): interface grafica no navegador, usando **Flask** como backend.

## Funcionalidades

- **Emissao de ticket na entrada**: gera um ticket com numero sequencial, placa do veiculo,
  vaga atribuida e data/hora de entrada.
- **Registro de saida**: calcula automaticamente o valor a pagar com base no tempo de
  permanencia do veiculo.
- **Tabela de precos configuravel**: valor da primeira hora e valor de cada hora adicional
  podem ser ajustados pelo menu de configuracoes.
- **Controle de vagas**: acompanha o total de vagas, vagas ocupadas e vagas livres em tempo
  real.
- **Relatorio de movimentacao**: lista veiculos que entraram/sairam e o faturamento total,
  com opcao de filtrar por data.
- **Interface via terminal**: menu interativo simples e direto.
- **Interface web**: mesmas funcionalidades acima em um painel visual no navegador,
  com design moderno e responsivo (funciona em desktop e mobile).
- **Persistencia em JSON**: todos os dados (tickets e configuracoes) sao salvos em
  `data/tickets.json` e `data/configuracao.json`, preservando as informacoes entre execucoes
  e compartilhados entre as duas interfaces (terminal e web).

## Estrutura do projeto

```
parking-system/
├── main.py                          # Ponto de entrada: menu interativo do terminal
├── app.py                           # Ponto de entrada: servidor web (Flask)
├── models/
│   ├── __init__.py
│   ├── ticket.py                    # Modelo de dados do Ticket
│   └── configuracao.py              # Modelo de dados da Configuracao (precos e vagas)
├── services/
│   ├── __init__.py
│   ├── estacionamento_service.py    # Regras de negocio (entrada, saida, calculo, relatorios)
│   └── persistencia_service.py      # Leitura/escrita dos arquivos JSON
├── templates/
│   └── index.html                   # Pagina unica (SPA) da interface web
├── static/
│   ├── css/
│   │   └── style.css                # Estilos da interface web
│   └── js/
│       └── app.js                   # Logica do frontend (consome a API Flask)
├── data/
│   ├── tickets.json                 # Gerado automaticamente na primeira execucao
│   └── configuracao.json            # Gerado automaticamente na primeira execucao
└── README.md
```

## Requisitos

- **Versao terminal** (`main.py`): Python 3.8 ou superior, nenhuma biblioteca externa.
- **Versao web** (`app.py`): Python 3.8 ou superior + **Flask**.

## Como executar (terminal)

1. Abra a pasta `parking-system` no VS Code.
2. Abra um terminal integrado (``Terminal > New Terminal``).
3. Execute o comando:

```bash
python main.py
```

4. Utilize o menu numerico exibido no terminal para navegar entre as opcoes.

## Como executar (web)

1. Instale o Flask (uma unica vez):

```bash
pip install flask
```

2. Execute o servidor:

```bash
python app.py
```

3. Abra o navegador em [http://127.0.0.1:5000](http://127.0.0.1:5000).

4. Use o menu lateral para navegar entre as telas: Registrar Entrada, Registrar Saida,
   Controle de Vagas, Relatorio e Configuracoes.

> A versao web usa exatamente as mesmas regras de negocio e os mesmos arquivos de dados
> (`data/tickets.json` e `data/configuracao.json`) da versao terminal — nao ha duplicacao de
> logica, apenas uma nova camada de API (Flask) e interface (HTML/CSS/JS) sobre o servico
> existente (`EstacionamentoService`).

## Como usar o sistema

Cada funcionalidade pode ser acessada tanto pelo menu do terminal quanto pela tela
correspondente na interface web (menu lateral).

### 1. Registrar entrada de veiculo
No terminal, escolha a opcao **1** no menu; na web, use a tela **Registrar Entrada**.
Informe a placa do veiculo. O sistema atribui automaticamente uma vaga livre e emite um
ticket com numero sequencial e horario de entrada.

### 2. Registrar saida de veiculo
No terminal, escolha a opcao **2**; na web, use a tela **Registrar Saida**. Informe o
**numero do ticket** ou a **placa** do veiculo. O sistema calcula o valor a pagar com base no
tempo de permanencia e libera a vaga.

### 3. Controle de vagas
No terminal, escolha a opcao **3**; na web, use a tela **Controle de Vagas** para visualizar
o total de vagas, quantas estao ocupadas, quantas estao livres e a lista de veiculos
atualmente estacionados.

### 4. Relatorio de movimentacao
No terminal, escolha a opcao **4**; na web, use a tela **Relatorio** para ver quantos
veiculos entraram, quantos sairam e o faturamento total. E possivel filtrar o relatorio por
uma data especifica (formato `dd/mm/aaaa`).

### 5. Configuracoes
No terminal, escolha a opcao **5**; na web, use a tela **Configuracoes** para alterar o total
de vagas do estacionamento, o valor da primeira hora e o valor de cada hora adicional. Deixe
o campo em branco para manter o valor atual.

## Regra de cobranca

- **Primeira hora (ou fracao)**: valor fixo (padrao `R$ 5,00`).
- **Cada hora adicional (ou fracao)**: valor fixo por hora (padrao `R$ 3,00`).

Exemplo com os valores padrao:
- Permanencia de 40 minutos → cobra apenas a primeira hora: `R$ 5,00`.
- Permanencia de 1h30 → primeira hora + 1 hora adicional (fracao arredondada para cima):
  `R$ 5,00 + R$ 3,00 = R$ 8,00`.
- Permanencia de 3h10 → primeira hora + 3 horas adicionais (fracao arredondada para cima):
  `R$ 5,00 + 3 × R$ 3,00 = R$ 14,00`.

## Persistencia de dados

Os dados sao armazenados automaticamente na pasta `data/`:

- `tickets.json`: historico completo de todos os tickets (abertos e fechados).
- `configuracao.json`: total de vagas, valores da tabela de precos e o proximo numero de
  ticket a ser emitido.

Nao e necessario nenhum banco de dados: os arquivos sao criados automaticamente na primeira
execucao do programa.

## Observacoes

- As placas sao armazenadas em letras maiusculas, independentemente de como forem digitadas.
- Nao e permitido registrar duas entradas abertas para a mesma placa.
- Ao reduzir o total de vagas, o sistema impede valores menores que a quantidade de veiculos
  ja estacionados.
