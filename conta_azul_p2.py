
import base64, requests


def get_acess_token(client_id,client_secret,redirect_uri,code):
    url = 'https://auth.contaazul.com/oauth2/token'

    encoded_data = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Content-Type":"application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_data}"
    }
    payload = {
        
        'grant_type':"authorization_code",
        'code':code,
        'redirect_uri':redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,

    }

    r = requests.post(url,headers=headers,data=payload)
    #r.raise_for_status()
    
    print(r.content)

    print(r.json())

def common_request(access_token):
    headers = {
        "Authorization":f"Bearer {access_token}",
        "Accept": "application/json"
    }

    payload = {
        "pagina":"1",
        "tamanho_pagina":"10",
        "permite_apenas_filhos":"true"
    }

    url = 'https://api-v2.contaazul.com/v1/categorias'

    r = requests.get(url,params=payload,headers=headers)
    print(r.headers)
    print(r.content)

    print(r.json())

client_id_prod = 'mqtj80lnr02olc4m9be48jo9g'
client_secret_prod = '1hkcaftg0fvlud38tb9biqtpful9sdbuhj4h6jttbf65efmk184g'
redirect_uri_prod = 'https://www.FiscalCarvalhoEGuerra.pythonanywhere.com'

code = 'ff699b29-8b6e-4d96-a061-4afcde4aa118' #Code vem na URL de retorno
get_acess_token(client_id_prod,client_secret_prod,redirect_uri_prod,code)

