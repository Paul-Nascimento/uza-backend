import requests
import pprint
import pandas as pd

token = 'v4RNRlSmtvFV897mfOdIxLLzAkODTRlZyEiDaf2y2OQb3N59QL2O4bHOsgCC'


def get_team_members(token):
    url = 'https://api.vexpenses.com/v2/team-members'

    data = {
        "Authorization":token
    }


    params = {
        "include": "costsCenters,projects",

        "paginate":True,

        "page":1,

        "per_page":500
    }

    req = requests.get(url,headers=data,params=params)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])



    df = pd.DataFrame(req.json()['data'])

    df.to_excel('team_members_vexpenses.xlsx')

def get_expenses(token):
    url = 'https://api.vexpenses.com/v2/expenses'

    headers = {"Authorization": token}

    params = {
        "include": "user,report,payment_method",
        "search": "date:2026-04-01,2026-04-30",
        "searchFields": "date:between",
        "searchJoin": "and"
    }

    req = requests.get(url, headers=headers, params=params)

    df = pd.DataFrame(req.json()['data'])

    # Extrai o status do relatório aninhado em 'report' -> 'data' -> 'status'
    df['aprovado'] = df['report'].apply(
        lambda r: r['data']['status'] if r and r.get('data') else None
    )

    df.to_excel('expenses_vexpenses_v3.xlsx', index=False)
    
def get_expenses_types(token):
    url = 'https://api.vexpenses.com/v2/expenses-type'

    data = {
        "Authorization":token
    }

    req = requests.get(url,headers=data)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])

    df = pd.DataFrame(req.json()['data'])

    df.to_excel('expenses_vexpenses_type.xlsx')

def get_cost_centers(token):
    url = 'https://api.vexpenses.com/v2/costs-centers'

    data = {
        "Authorization":token
    }


    params = {
        
        "paginate":True,

        "page":1,

        "per_page":5
    }

    req = requests.get(url,headers=data,params=params)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])

def get_projects(token):
    url = 'https://api.vexpenses.com/v2/projects'

    data = {
        "Authorization":token
    }


    params = {
        
        "paginate":True,

        "page":1,

        "per_page":100
    }

    req = requests.get(url,headers=data,params=params)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])

    df = pd.DataFrame(req.json()['data'])

    df.to_excel('projects_vexpenses.xlsx')

def get_approval_flows(token):
    url = 'https://api.vexpenses.com/v2/approval-flows'

    data = {
        "Authorization":token
    }




    req = requests.get(url,headers=data)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])



    df = pd.DataFrame(req.json()['data'])

    df.to_excel('approval_flows_vexpenses.xlsx')

def get_currencies(token):
    url = 'https://api.vexpenses.com/v2/currencies'

    data = {
        "Authorization":token
    }

    req = requests.get(url,headers=data)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])

def get_reports(token):
    url = 'https://api.vexpenses.com/v2/reports'

    data = {
        "Authorization":token
    }


    params = {
        "include": "expenses",


    }

    req = requests.get(url,headers=data,params=params)
    #print(req.content)
    #req = requests.get("https://api.vexpenses.com/v2/currencies",headers=data)
    pprint.pprint(req.json()['data'])

    pprint.pprint(req.json()['data'])

    df = pd.DataFrame(req.json()['data'])

    df.to_excel('reports_vexpenses.xlsx')
get_expenses(token)
#get_expenses_types(token)
#get_team_members(token)
#get_cost_centers(token)
#get_projects(token)
#get_approval_flows(token)
#get_currencies(token)
#get_reports(token)


"""
OBSERVAÇÕES UZA | VEXPENSES

Temos muitos projetos
Temos muitos usuarios
Temos 1 centro de custos apenas


Pra reunião:
    Puxar as despesas de abril e fazer 3 cards:
        -TOTAL
        -Por projeto
        -Por usuario

"""