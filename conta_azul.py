
import base64, requests
import requests
from urllib.parse import urlparse, parse_qs




def obter_code_requests(url, email, senha):
    """
    Faz login com requests, enviando usuário e senha nos campos:
    #signInFormUsername
    #signInFormPassword
    #signInSubmitButton
    Retorna o valor do 'code' presente na URL de redirecionamento.
    """
    with requests.Session() as session:
        # Acessa a URL inicial (importante para pegar cookies iniciais)
        response = session.get(url, allow_redirects=True)

        # Monta payload igual aos IDs do formulário HTML
        payload = {
            "signInFormUsername": email,
            "signInFormPassword": senha,
            "signInSubmitButton": "Login"  # valor pode variar, às vezes basta existir
        }

        # Faz POST para a mesma url ou para /login (depende do site)
        login_response = session.post(response.url, data=payload, allow_redirects=True)

        # Após redirecionamento, o 'code' deve aparecer na URL final
        final_url = login_response.url

        # Extrai o parâmetro `code`
        query = urlparse(final_url).query
        code = parse_qs(query).get("code", [None])[0]

        return code, final_url

def get_credentials(client_id):
    
    url_direcionamento = 'https://www.FiscalCarvalhoEGuerra.pythonanywhere.com'
    import requests


    payload = {
        "response_type":"code",
        "client_id":client_id,
        "redirect_uri":url_direcionamento,
        "state":"1",
        "scope":"profile aws.cognito.signin.user.admin"

    }

    #https://auth.contaazul.com/oauth2/authorize?response_type=code&client_id=54uiif986v7ib27gpl9ikda3vl&redirect_uri=https://www.google.com&state=ESTADO&scope=openid+profile+aws.cognito.signin.user.admin
    headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        
        }

    r =  requests.get('https://auth.contaazul.com/oauth2/authorize',params=payload,headers=headers)

    
    print(r.content)
    print(r.url)

    
    #usuario='b8c59ab4-5f6a-4af7-b99b-d353525d41f3@devportal.com'
    #password = 'b8c59ab4-5f6a-4af7-b99b-d353525d41f3'
    #code = obter_code_requests(r.url, usuario,senha )
    #print(code)

client_id_prod = 'mqtj80lnr02olc4m9be48jo9g'

get_credentials(client_id_prod)


