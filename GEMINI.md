# Diretrizes do Projeto - Parking System

## Políticas de Execução de Comandos e Testes

- **Execução Automática de Testes via Python**:
  - Sempre que implementar novos módulos, rotas, serviços ou correções de bugs, execute imediatamente os testes automatizados via `python tests/run_tests.py` (ou scripts Python de validação) de forma proativa.
  - Não peça permissão ao usuário para executar testes; execute-os automaticamente e apresente o resultado no retorno.

- **Comandos via PowerShell**:
  - Comandos no terminal PowerShell (inspeção de arquivos, pesquisas de padrões, testes de rotas, verificação de processos e scripts auxiliares) estão permanentemente autorizados.
  - Execute-os diretamente sem solicitar confirmação prévia ao usuário.

