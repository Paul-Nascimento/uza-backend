from django.urls import path
from .views import (
    VisaoGeralView,
    DespesasView,
    ColaboradoresView,
    FluxoCaixaView,
    FilterOptionsView,
)

urlpatterns = [
    path("visao-geral/",    VisaoGeralView.as_view()),
    path("despesas/",       DespesasView.as_view()),
    path("colaboradores/",  ColaboradoresView.as_view()),
    path("fluxo-caixa/",    FluxoCaixaView.as_view()),
    path("filter-options/", FilterOptionsView.as_view()),
]