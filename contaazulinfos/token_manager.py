import base64
import logging
import requests
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import ContaAzulToken

logger = logging.getLogger(__name__)

MARGEM_RENOVACAO_SEGUNDOS = 300  # renova 5 min antes de expirar


class ContaAzulTokenManager:
    # Nova API — a legada (api.contaazul.com) foi descontinuada
    TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

    @classmethod
    def _basic_auth_header(cls) -> str:
        """
        A nova API exige autenticação via header Authorization: Basic base64(client_id:client_secret)
        O client_id e client_secret NÃO vão no body.
        """
        credentials = f"{settings.CONTA_AZUL_CLIENT_ID}:{settings.CONTA_AZUL_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @classmethod
    def get_valid_access_token(cls) -> str:
        token = ContaAzulToken.objects.first()

        if not token:
            raise Exception(
                "Token da Conta Azul não configurado. "
                "Realize o fluxo OAuth inicial e salve o token no banco."
            )

        limite_seguro = timezone.now() + timedelta(seconds=MARGEM_RENOVACAO_SEGUNDOS)

        if token.expires_at > limite_seguro:
            logger.debug("Token ainda válido, retornando sem renovar.")
            return token.access_token

        logger.info("Token expirado ou próximo de expirar. Renovando...")
        return cls._refresh_token(token)

    @classmethod
    def _refresh_token(cls, token_obj: ContaAzulToken) -> str:
        """
        Realiza o refresh na nova API da Conta Azul.

        ATENÇÃO: o refresh_token é de uso único — após utilizado, o novo
        refresh_token retornado na resposta deve ser salvo imediatamente,
        caso contrário a sessão é perdida.
        """
        headers = {
            "Authorization": cls._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # client_id e client_secret vão apenas no header Authorization: Basic
        # o body contém somente grant_type e refresh_token
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": token_obj.refresh_token,
        }

        try:
            response = requests.post(
                cls.TOKEN_URL,
                headers=headers,
                data=payload,
                timeout=10,
            )
        except requests.Timeout:
            raise Exception("Timeout ao tentar renovar token da Conta Azul.")
        except requests.ConnectionError:
            raise Exception("Sem conexão ao tentar renovar token da Conta Azul.")

        if response.status_code != 200:
            raise Exception(
                f"Erro ao renovar token: status {response.status_code} — {response.text}"
            )

        data = response.json()

        for campo in ["access_token", "refresh_token", "expires_in"]:
            if campo not in data:
                raise Exception(
                    f"Resposta do refresh inválida: campo '{campo}' ausente. Resposta: {data}"
                )

        # Salva imediatamente — refresh_token é de uso único na Conta Azul
        token_obj.access_token = data["access_token"]
        token_obj.refresh_token = data["refresh_token"]
        token_obj.expires_at = timezone.now() + timedelta(seconds=data["expires_in"])
        token_obj.save()

        logger.info(
            f"Token renovado com sucesso. "
            f"Expira em: {token_obj.expires_at.strftime('%d/%m/%Y %H:%M:%S')}"
        )
        return token_obj.access_token