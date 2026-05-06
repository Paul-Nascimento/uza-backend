from django.urls import path
from . import views

urlpatterns = [
    # Sync
    path("sync/", views.SyncAllView.as_view()),
    path("sync/expenses/", views.SyncExpensesView.as_view()),
    path("sync/projects/", views.SyncProjectsView.as_view()),
    path("sync/team-members/", views.SyncTeamMembersView.as_view()),
    path("sync/expense-types/", views.SyncExpenseTypesView.as_view()),
    # Data
    path("projects/", views.ProjectListView.as_view()),
    path("team-members/", views.TeamMemberListView.as_view()),
    path("expense-types/", views.ExpenseTypeListView.as_view()),
    path("expenses/", views.ExpenseListView.as_view()),
    path("expenses/<int:pk>/", views.ExpenseDetailView.as_view()),
]