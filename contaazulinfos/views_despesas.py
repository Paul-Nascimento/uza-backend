from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services_despesas import get_despesas


class DespesasView(APIView):
    """
    GET /api/dashboard/despesas/
    Query params:
      - date_from       YYYY-MM-DD
      - date_to         YYYY-MM-DD
      - categoria_id    int (opcional)
      - centro_custo_id int (opcional)
      - pessoa_id       int (opcional)
      - status          string (opcional)
    """

    def get(self, request):
        try:
            hoje = date.today()
            date_from = date.fromisoformat(
                request.query_params.get("date_from", hoje.replace(day=1).isoformat())
            )
            date_to = date.fromisoformat(
                request.query_params.get("date_to", hoje.isoformat())
            )

            categoria_id = request.query_params.get("categoria_id") or None
            centro_custo_id = request.query_params.get("centro_custo_id") or None
            pessoa_id = request.query_params.get("pessoa_id") or None
            status_param = request.query_params.get("status") or None

            data = get_despesas(
                date_from,
                date_to,
                int(categoria_id) if categoria_id else None,
                int(centro_custo_id) if centro_custo_id else None,
                int(pessoa_id) if pessoa_id else None,
                status_param,
            )
            return Response(data)

        except ValueError as e:
            return Response({"error": f"Parâmetro inválido: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)