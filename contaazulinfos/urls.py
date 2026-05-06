from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CentroCustoViewSet,
    PessoaViewSet,
    CategoriaViewSet,
    ContaAReceberViewSet,
    ContaAPagarViewSet,
    SyncCentroCustoView,
    SyncCategoriasView,
    SyncPessoasView,
    SyncContasAReceberView,
    SyncContasAPagarView,
    SyncAllView,
)


router = DefaultRouter()
router.register("centros-custo", CentroCustoViewSet)
router.register("pessoas", PessoaViewSet)
router.register("categorias", CategoriaViewSet)
router.register("contas-a-receber", ContaAReceberViewSet, basename="contaareceber")
router.register("contas-a-pagar", ContaAPagarViewSet, basename="contaapagar")


sync_urlpatterns = [
    path("sync/", SyncAllView.as_view()),
    path("sync/centros-custo/", SyncCentroCustoView.as_view()),
    path("sync/categorias/", SyncCategoriasView.as_view()),
    path("sync/pessoas/", SyncPessoasView.as_view()),
    path("sync/contas-a-receber/", SyncContasAReceberView.as_view()),
    path("sync/contas-a-pagar/", SyncContasAPagarView.as_view()),

]

urlpatterns = router.urls + sync_urlpatterns