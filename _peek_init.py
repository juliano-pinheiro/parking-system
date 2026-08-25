import re

for nome in ['caixa_service', 'pagamento_service', 'mensalista_service', 'convenio_service',
             'contas_receber_service', 'desconto_service', 'cortesia_service',
             'forma_pagamento_service', 'tabela_preco_service', 'estorno_service',
             'perfil_service', 'empresa_service']:
    s = open('services/' + nome + '.py', encoding='utf-8').read()
    m = re.search(r'def __init__\(self[^)]*\):(.*?)(?=\n    def |\n# )', s, re.DOTALL)
    print('=====', nome)
    print(m.group(0)[:400] if m else 'SEM __init__')
