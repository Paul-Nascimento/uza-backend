from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as drf_status

from .services import (
    get_visao_geral,
    get_despesas,
    get_colaboradores,
    get_fluxo_caixa,
    get_filter_options,
)


def _dates(request):
    hoje = date.today()
    df = date.fromisoformat(request.query_params.get("date_from", hoje.replace(day=1).isoformat()))
    dt = date.fromisoformat(request.query_params.get("date_to",   hoje.isoformat()))
    return df, dt


class VisaoGeralView(APIView):
    def get(self, request):
        try:
            df, dt = _dates(request)
            cat = request.query_params.get("categoria_id")    or None
            cc  = request.query_params.get("centro_custo_id") or None
            return Response(get_visao_geral(df, dt,
                int(cat) if cat else None,
                int(cc)  if cc  else None,
            ))
        except ValueError as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


class DespesasView(APIView):
    def get(self, request):
        try:
            df, dt = _dates(request)
            cat  = request.query_params.get("categoria_id")    or None
            cc   = request.query_params.get("centro_custo_id") or None
            pes  = request.query_params.get("pessoa_id")       or None
            sta  = request.query_params.get("status")          or None
            return Response(get_despesas(df, dt,
                int(cat) if cat else None,
                int(cc)  if cc  else None,
                int(pes) if pes else None,
                sta))
        except ValueError as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


class ColaboradoresView(APIView):
    def get(self, request):
        try:
            df, dt = _dates(request)
            uid = request.query_params.get("user_id") or None
            return Response(get_colaboradores(df, dt, int(uid) if uid else None))
        except ValueError as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


class FluxoCaixaView(APIView):
    def get(self, request):
        try:
            df, dt = _dates(request)
            return Response(get_fluxo_caixa(df, dt))
        except ValueError as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)


class FilterOptionsView(APIView):
    def get(self, request):
        try:
            return Response(get_filter_options())
        except Exception as e:
            return Response({"error": str(e)}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)