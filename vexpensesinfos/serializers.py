from rest_framework import serializers
from .models import Project, TeamMember, ExpenseType, Expense


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "company_name", "city", "state", "on", "integration_id"]


class TeamMemberSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "name",
            "email",
            "user_type",
            "active",
            "confirmed",
            "approval_flow_id",
            "projects",
        ]


class ExpenseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseType
        fields = ["id", "description", "on"]


class ExpenseSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "user_id",
            "user_name",
            "user_email",
            "date",
            "value",
            "converted_value",
            "converted_currency_iso",
            "title",
            "observation",
            "reimbursable",
            "rejected",
            "on",
            "receipt_url",
            "expense_type_id",
            "payment_method_id",
            "report_id",
            "report_status",
            "report_description",
            "created_at",
            "updated_at",
        ]


class ExpenseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "user_id",
            "user_name",
            "date",
            "value",
            "title",
            "report_id",
            "report_status",
        ]