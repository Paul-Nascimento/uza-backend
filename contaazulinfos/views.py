from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import CentroCusto, Pessoa, Categoria, ContaAReceber, ContaAPagar
from .serializers import (
    CentroCustoSerializer,
    PessoaSerializer,
    CategoriaSerializer,
    ContaAReceberSerializer,
    ContaAPagarSerializer,
)
from .token_manager import ContaAzulTokenManager
from . import services


# ── ViewSets (CRUD / leitura) ─────────────────────────────────────────────────

class CentroCustoViewSet(ModelViewSet):
    queryset = CentroCusto.objects.all()
    serializer_class = CentroCustoSerializer


class PessoaViewSet(ModelViewSet):
    queryset = Pessoa.objects.all()
    serializer_class = PessoaSerializer


class CategoriaViewSet(ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ContaAReceberViewSet(ModelViewSet):
    serializer_class = ContaAReceberSerializer

    def get_queryset(self):
        qs = ContaAReceber.objects.select_related("pessoa_id")
        data_de = self.request.query_params.get("data_de")
        data_ate = self.request.query_params.get("data_ate")
        status_param = self.request.query_params.get("status")
        pessoa_id = self.request.query_params.get("pessoa_id")

        if data_de:
            qs = qs.filter(data_vencimento__gte=data_de)
        if data_ate:
            qs = qs.filter(data_vencimento__lte=data_ate)
        if status_param:
            qs = qs.filter(status__iexact=status_param)
        if pessoa_id:
            qs = qs.filter(pessoa_id=pessoa_id)

        return qs.order_by("-data_vencimento")


class ContaAPagarViewSet(ModelViewSet):
    serializer_class = ContaAPagarSerializer

    def get_queryset(self):
        qs = ContaAPagar.objects.select_related("pessoa_id", "categoria_id", "centro_custo_id")
        data_de = self.request.query_params.get("data_de")
        data_ate = self.request.query_params.get("data_ate")
        status_param = self.request.query_params.get("status")
        pessoa_id = self.request.query_params.get("pessoa_id")
        categoria_id = self.request.query_params.get("categoria_id")
        centro_custo_id = self.request.query_params.get("centro_custo_id")

        if data_de:
            qs = qs.filter(data_vencimento__gte=data_de)
        if data_ate:
            qs = qs.filter(data_vencimento__lte=data_ate)
        if status_param:
            qs = qs.filter(status__iexact=status_param)
        if pessoa_id:
            qs = qs.filter(pessoa_id=pessoa_id)
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        if centro_custo_id:
            qs = qs.filter(centro_custo_id=centro_custo_id)

        return qs.order_by("-data_vencimento")


# ── Sync views ────────────────────────────────────────────────────────────────

class SyncCentroCustoView(APIView):
    """POST /api/sync/centros-custo/"""

    def post(self, request):
        try:
            token = ContaAzulTokenManager.get_valid_access_token()
            result = services.cadastrar_centro_de_custo_via_api(token)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncCategoriasView(APIView):
    """POST /api/sync/categorias/"""

    def post(self, request):
        try:
            token = ContaAzulTokenManager.get_valid_access_token()
            result = services.cadastrar_categoria_via_api(token)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncPessoasView(APIView):
    """POST /api/sync/pessoas/"""

    def post(self, request):
        try:
            token = ContaAzulTokenManager.get_valid_access_token()
            result = services.cadastrar_pessoa_via_api(token)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncContasAReceberView(APIView):
    """
    POST /api/sync/contas-a-receber/
    Body: { "data_de": "YYYY-MM-DD", "data_ate": "YYYY-MM-DD" }
    """

    def post(self, request):
        data_de = request.data.get("data_de")
        data_ate = request.data.get("data_ate")
        if not data_de or not data_ate:
            return Response(
                {"error": "data_de e data_ate são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = ContaAzulTokenManager.get_valid_access_token()
            result = services.cadastrar_conta_a_receber_via_api(token, data_de, data_ate)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncContasAPagarView(APIView):
    """
    POST /api/sync/contas-a-pagar/
    Body: { "data_de": "YYYY-MM-DD", "data_ate": "YYYY-MM-DD" }
    """

    def post(self, request):
        data_de = request.data.get("data_de")
        data_ate = request.data.get("data_ate")
        if not data_de or not data_ate:
            return Response(
                {"error": "data_de e data_ate são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = ContaAzulTokenManager.get_valid_access_token()
            result = services.cadastrar_conta_a_pagar_via_api(token, data_de, data_ate)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncAllView(APIView):
    """
    POST /api/sync/
    Sync completo em ordem de dependência.
    Body: { "data_de": "YYYY-MM-DD", "data_ate": "YYYY-MM-DD" }
    """

    def post(self, request):
        data_de = request.data.get("data_de")
        data_ate = request.data.get("data_ate")
        if not data_de or not data_ate:
            return Response(
                {"error": "data_de e data_ate são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        token = ContaAzulTokenManager.get_valid_access_token()
        print(token)
        try:
            
            return Response({
                "centros_custo": services.cadastrar_centro_de_custo_via_api(token),
                "categorias": services.cadastrar_categoria_via_api(token),
                "pessoas": services.cadastrar_pessoa_via_api(token),
                "contas_a_receber": services.cadastrar_conta_a_receber_via_api(token, data_de, data_ate),
                "contas_a_pagar": services.cadastrar_conta_a_pagar_via_api(token, data_de, data_ate),
            })
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)