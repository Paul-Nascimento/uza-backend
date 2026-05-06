from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .models import Project, TeamMember, ExpenseType, Expense
from .serializers import (
    ProjectSerializer,
    TeamMemberSerializer,
    ExpenseTypeSerializer,
    ExpenseSerializer,
    ExpenseListSerializer,
)
from . import services


VEXPENSES_TOKEN = getattr(settings, "VEXPENSES_TOKEN", "")


# ── Sync endpoints ─────────────────────────────────────────────────────────────

class SyncAllView(APIView):
    """
    POST /api/sync/
    Body: { "date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD" }
    Runs a full sync in dependency order.
    """

    def post(self, request):
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")
        if not date_from or not date_to:
            return Response(
                {"error": "date_from and date_to are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = services.sync_all(VEXPENSES_TOKEN, date_from, date_to)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncExpensesView(APIView):
    """
    POST /api/sync/expenses/
    Body: { "date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD" }
    """

    def post(self, request):
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")
        if not date_from or not date_to:
            return Response(
                {"error": "date_from and date_to are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = services.sync_expenses(VEXPENSES_TOKEN, date_from, date_to)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncProjectsView(APIView):
    """POST /api/sync/projects/"""

    def post(self, request):
        try:
            result = services.sync_projects(VEXPENSES_TOKEN)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncTeamMembersView(APIView):
    """POST /api/sync/team-members/"""

    def post(self, request):
        try:
            result = services.sync_team_members(VEXPENSES_TOKEN)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class SyncExpenseTypesView(APIView):
    """POST /api/sync/expense-types/"""

    def post(self, request):
        try:
            result = services.sync_expense_types(VEXPENSES_TOKEN)
            return Response(result)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


# ── Data endpoints ─────────────────────────────────────────────────────────────

class ProjectListView(APIView):
    """GET /api/projects/"""

    def get(self, request):
        qs = Project.objects.filter(on=True).order_by("name")
        return Response(ProjectSerializer(qs, many=True).data)


class TeamMemberListView(APIView):
    """GET /api/team-members/?active=true"""

    def get(self, request):
        qs = TeamMember.objects.prefetch_related("projects")
        active = request.query_params.get("active")
        if active is not None:
            qs = qs.filter(active=active.lower() == "true")
        return Response(TeamMemberSerializer(qs.order_by("name"), many=True).data)


class ExpenseTypeListView(APIView):
    """GET /api/expense-types/"""

    def get(self, request):
        qs = ExpenseType.objects.filter(on=True).order_by("description")
        return Response(ExpenseTypeSerializer(qs, many=True).data)


class ExpenseListView(APIView):
    """
    GET /api/expenses/
    Query params:
      - date_from / date_to   → filter by date range
      - user_id               → filter by team member
      - report_status         → filter by report status
    """

    def get(self, request):
        qs = Expense.objects.select_related("user")

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        user_id = request.query_params.get("user_id")
        report_status = request.query_params.get("report_status")

        if date_from:
            qs = qs.filter(date__date__gte=date_from)
        if date_to:
            qs = qs.filter(date__date__lte=date_to)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if report_status:
            qs = qs.filter(report_status__iexact=report_status)

        return Response(ExpenseListSerializer(qs.order_by("-date"), many=True).data)


class ExpenseDetailView(APIView):
    """GET /api/expenses/<pk>/"""

    def get(self, request, pk):
        try:
            obj = Expense.objects.select_related("user").get(pk=pk)
        except Expense.DoesNotExist:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ExpenseSerializer(obj).data)