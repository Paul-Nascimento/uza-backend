import requests
import pandas as pd

token = 'eyJraWQiOiJUa1BRbWs0UlR3M3RuWlZXcDdEanBURFhcL2RTajNvMU5SckI0R3I3ZzFTMD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyOWZhMjU5Yy1mNTBhLTQxMGEtOGFkZC1kY2ZmZTI1NTBmMmYiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuc2EtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3NhLWVhc3QtMV9WcDgzSjExd0EiLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiJtcXRqODBsbnIwMm9sYzRtOWJlNDhqbzlnIiwib3JpZ2luX2p0aSI6ImQ4NGI4M2IyLTJjYzgtNGIzNi1iMjQ2LTNiYzNhMWQzOGQ4OCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4gcHJvZmlsZSIsImF1dGhfdGltZSI6MTc3ODEwNzQzNywiZXhwIjoxNzc4MTExMDM3LCJpYXQiOjE3NzgxMDc0MzcsImp0aSI6ImNmZTMzMzI4LWZlNzItNGM4MS1hZDc3LTFjNmE2NmRjNDcwZCIsInVzZXJuYW1lIjoicGF1bG9uYXNjaW1lbnRvMDkxMEBnbWFpbC5jb20ifQ.iiaf7feOwDKo_oxvVX1V0p5Cl8dME4N-ixH4Q8z1Q1rycskRkxIu2OecC2Q8sHWZg_bQhCt3Ln31q99CPuqsht9tTxZisFBTaEE3NTdFyxzg6z-pvI_5DA0xR9c7KMqt9BCvNVfN9q3AE7Bz-GHYx3nzZlf5TfGs_t6ExmWD6Sxl1MTcYP-AN_TDbFUs4WEmmKZj1C_neJsyk-FHF6y-gCA_X2aGL_5cneHyp8N8A4H00BqWtf4HZrCLnd4E5vQrWuYCpV0WpVJrwWyAMXWsIqBXxLSUTB-NIEz-7B73xi4T5RUfh5oBIHcDUKjvv2jWMaojSUXd2jf7YcMBgpc6DA'
def centros_de_custo(token):
    url = "https://api-v2.contaazul.com/v1/centro-de-custo"
    
    query = {
    "pagina": "1",
    "tamanho_pagina": "10",
    "busca": "010",
    "filtro_rapido": "ATIVO",
    "campo_ordenado_ascendente": "nome",
    "campo_ordenado_descendente": "nome"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)



    data = response.json()
    
    itens_totais = data['itens_totais']
    itens = data['itens']
    print(data)

def categorias_dre(token): 

    url = "https://api-v2.contaazul.com/v1/financeiro/categorias-dre"

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    data = response.json()
    print(data)

def contas_financeiras(token):
   

    url = "https://api-v2.contaazul.com/v1/conta-financeira"

    query = {
    "pagina": "1",
    "tamanho_pagina": "10",
    "tipos": "APLICACAO",
    "nome": "Conta corrente",
    "apenas_ativo": "true",
    "esconde_conta_digital": "true",
    "mostrar_caixinha": "true"
    }
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()
    print(data)

def get_receitas(token): ######MUITO RELEVANTE##########

    url = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"

    query = {
    "pagina": "1",
    "tamanho_pagina": "100",
    "campo_ordenado_ascendente": "nome",
    "campo_ordenado_descendente": "nome",
    #"descricao": "Conta Corrente",
    "data_vencimento_de": "2026-04-01",
    "data_vencimento_ate": "2026-04-30",
    #"data_competencia_de": "2026-04-01",
    #"data_competencia_ate": "2026-04-30",
    #"data_pagamento_de": "2025-08-15",
    #"data_pagamento_ate": "2025-08-20",
    #"data_criacao_de": "2025-11-21T00:00:00",
    #"data_criacao_ate": "2025-11-22T07:59:59",
    #"valor_de": "100",
    #"valor_ate": "500",
    #"status": "ATRASADO",
    #"ids_contas_financeiras": "string",
    #"ids_categorias": "string",
    #"ids_centros_de_custo": "string",
    #"ids_clientes": "string"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()
    print(data)

    
    import pandas as pd

    #df_all = pd.DataFrame(data)
    #df_all.to_excel('contazultotal.xlsx')

    df = pd.DataFrame(data['itens'])
    df.to_excel('contazul5.xlsx')

def get_despesas(token):
    import requests

    url = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"

    query = {
    "pagina": "1",
    "tamanho_pagina": "1000",
    "campo_ordenado_ascendente": "nome",
    "campo_ordenado_descendente": "nome",
    #"descricao": "Conta Corrente",
    "data_vencimento_de": "2026-04-01",
    "data_vencimento_ate": "2026-04-30",
    #"data_competencia_de": "2026-04-01",
    #"data_competencia_ate": "2026-04-30",
    #"data_pagamento_de": "2025-08-15",
    #"data_pagamento_ate": "2025-08-20",
    #"data_alteracao_de": "2026-04-01T07:00:00",
    #"data_alteracao_ate": "2026-04-30T07:59:59",
    #"valor_de": "100",
    #"valor_ate": "500",
    #"status": "ATRASADO",
    #"ids_contas_financeiras": "string",
    #"ids_categorias": "string",
    #"ids_centros_de_custo": "string",
    #"ids_clientes": "string"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()
    print(data)

    #import pandas as pd

    df = pd.DataFrame(data['itens'])
    df.to_excel('contazuldespesas1.xlsx')

def get_pessoas(token):
    import requests

    url = "https://api-v2.contaazul.com/v1/pessoas"

    query = {
    "pagina": "1",
    "tamanho_pagina": "10",

    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()

    total_itens = data['totalItems']
    items = data['items']
    print(data)
    print(total_itens)

    #import pandas as pd
    #df = pd.DataFrame(data['items'])
    #df.to_excel('contazulpessoas.xlsx')

def get_centros_de_custo(token):
    
    url = "https://api-v2.contaazul.com/v1/centro-de-custo"

    query = {
    "pagina": "1",
    "tamanho_pagina": "1000",
    #"busca": "010",
    #"filtro_rapido": "ATIVO",
    #"campo_ordenado_ascendente": "nome",
    #"campo_ordenado_descendente": "nome"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()
    print(data)

    data = response.json()
    print(data)

    import pandas as pd

    #df = pd.DataFrame(data['itens'])
    #df.to_excel('contazulcentrodecusto.xlsx')

def get_categorias(token):
    import requests

    url = "https://api-v2.contaazul.com/v1/categorias"

    query = {
    "pagina": "1",
    "tamanho_pagina": "10",
    #"campo_ordenado_ascendente": "NOME",
    #"campo_ordenado_descendente": "TIPO",
    #"busca": "010",
    #"tipo": "RECEITA",
    #"apenas_filhos": "true",
    #"nome": "Eletrônicos",
    #"permite_apenas_filhos": "true"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params=query)

    data = response.json()

    itens_totais = data['itens_totais']
    itens = data['itens']
    print(data)

    #import pandas as pd

    #df = pd.DataFrame(data['itens'])
    #df.to_excel('contazulcategorias.xlsx')

#categorias_dre(token)
#contas_financeiras(token)

#get_receitas(token)
get_despesas(token)
#get_centros_de_custo(token)
#get_categorias(token)
#get_pessoas(token)
#Despesas por centro de custo e categoria