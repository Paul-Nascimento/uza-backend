from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count

from contaazulinfos.models import ContaAPagar, CentroCusto


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_decimal(value) -> Decimal:
    return Decimal(str(value)) if value else Decimal("0.00")


def _periodo_anterior(date_from: date, date_to: date):
    delta = (date_to - date_from).days + 1
    return date_from - timedelta(days=delta), date_to - timedelta(days=delta)


def _dias_do_periodo(date_from: date, date_to: date) -> list:
    dias = []
    cursor = date_from
    while cursor <= date_to:
        dias.append(cursor)
        cursor += timedelta(days=1)
    return dias


# ── KPIs ───────────────────────────────────────────────────────────────────────

def get_kpis_despesas(date_from: date, date_to: date) -> dict:
    base = ContaAPagar.objects.filter(
        data_competencia__gte=date_from,
        data_competencia__lte=date_to,
    )

    total = base.aggregate(v=Sum("total"))["v"] or Decimal("0.00")
    aprovado = base.aggregate(v=Sum("pago"))["v"] or Decimal("0.00")
    em_aberto = base.filter(nao_pago__gt=0).aggregate(
        v=Sum("nao_pago"), c=Count("id")
    )
    reprovado = Decimal("0.00")  # pendente

    total_dec = _to_decimal(total)
    aprovado_dec = _to_decimal(aprovado)
    perc_aprovado = round((aprovado_dec / total_dec) * 100, 1) if total_dec > 0 else 0

    return {
        "total": total_dec,
        "aprovado": aprovado_dec,
        "perc_aprovado": perc_aprovado,
        "total_em_aberto": _to_decimal(em_aberto["v"]),
        "lancamentos_em_aberto": em_aberto["c"] or 0,
        "reprovado": reprovado,
    }


# ── Gráfico: Evolução Diária ───────────────────────────────────────────────────

def get_evolucao_diaria_despesas(date_from: date, date_to: date) -> list:
    date_from_ant, date_to_ant = _periodo_anterior(date_from, date_to)
    dias_atual = _dias_do_periodo(date_from, date_to)
    dias_anterior = _dias_do_periodo(date_from_ant, date_to_ant)

    qs_atual = (
        ContaAPagar.objects.filter(
            data_competencia__gte=date_from,
            data_competencia__lte=date_to,
        )
        .values("data_competencia")
        .annotate(total=Sum("pago"))
    )
    map_atual = {row["data_competencia"]: float(_to_decimal(row["total"])) for row in qs_atual}

    qs_anterior = (
        ContaAPagar.objects.filter(
            data_competencia__gte=date_from_ant,
            data_competencia__lte=date_to_ant,
        )
        .values("data_competencia")
        .annotate(total=Sum("pago"))
    )
    map_anterior = {row["data_competencia"]: float(_to_decimal(row["total"])) for row in qs_anterior}

    resultado = []
    for i, dia in enumerate(dias_atual):
        dia_ant = dias_anterior[i] if i < len(dias_anterior) else None
        resultado.append({
            "day": dia.strftime("%d/%m"),
            "atual": map_atual.get(dia, 0.0),
            "anterior": map_anterior.get(dia_ant, 0.0) if dia_ant else 0.0,
        })

    return resultado


# ── Gráfico: Top 5 Categorias ─────────────────────────────────────────────────

def get_top5_categorias_despesas(date_from: date, date_to: date) -> list:
    COLORS = ["#C9F020", "#4ADE80", "#6EE7B7", "#0EA5E9", "#ADADAD"]

    qs = (
        ContaAPagar.objects.filter(
            data_competencia__gte=date_from,
            data_competencia__lte=date_to,
            categoria_id__isnull=False,
        )
        .values("categoria_id__nome")
        .annotate(value=Sum("pago"))
        .order_by("-value")[:5]
    )

    return [
        {
            "name": row["categoria_id__nome"],
            "value": float(_to_decimal(row["value"])),
            "color": COLORS[i % len(COLORS)],
        }
        for i, row in enumerate(qs)
    ]


# ── Gráfico: Top 5 Projetos (Centro de Custo) ────────────────────────────────

def get_top5_projetos_despesas(date_from: date, date_to: date) -> list:
    qs = (
        ContaAPagar.objects.filter(
            data_competencia__gte=date_from,
            data_competencia__lte=date_to,
            centro_custo_id__isnull=False,
        )
        .values("centro_custo_id__nome")
        .annotate(value=Sum("pago"))
        .order_by("-value")[:5]
    )

    return [
        {
            "name": row["centro_custo_id__nome"],
            "value": float(_to_decimal(row["value"])),
        }
        for row in qs
    ]


# ── Gráfico: Status por Semana ────────────────────────────────────────────────

def get_status_por_semana_despesas(date_from: date, date_to: date) -> list:
    hoje = date.today()

    semanas = []
    cursor = date_from
    semana_num = 1
    while cursor <= date_to:
        fim = min(cursor + timedelta(days=6), date_to)
        semanas.append({"label": f"Sem {semana_num}", "inicio": cursor, "fim": fim})
        cursor = fim + timedelta(days=1)
        semana_num += 1

    resultado = []
    for semana in semanas:
        base = ContaAPagar.objects.filter(
            data_competencia__gte=semana["inicio"],
            data_competencia__lte=semana["fim"],
        )
        recebido = base.filter(pago__gt=0).aggregate(total=Sum("pago"), count=Count("id"))
        atrasado = base.filter(nao_pago__gt=0, data_competencia__lt=hoje).aggregate(
            total=Sum("nao_pago"), count=Count("id")
        )
        resultado.append({
            "week": semana["label"],
            "recebido": float(_to_decimal(recebido["total"])),
            "recebido_count": recebido["count"] or 0,
            "atrasado": float(_to_decimal(atrasado["total"])),
            "atrasado_count": atrasado["count"] or 0,
        })

    return resultado


# ── Tabela: Detalhamento de Contas a Pagar ────────────────────────────────────

def get_tabela_despesas(
    date_from: date,
    date_to: date,
    categoria_id: int = None,
    centro_custo_id: int = None,
    pessoa_id: int = None,
    status: str = None,
) -> list:
    qs = ContaAPagar.objects.select_related(
        "categoria_id", "centro_custo_id", "pessoa_id"
    ).filter(
        data_competencia__gte=date_from,
        data_competencia__lte=date_to,
    )

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if centro_custo_id:
        qs = qs.filter(centro_custo_id=centro_custo_id)
    if pessoa_id:
        qs = qs.filter(pessoa_id=pessoa_id)
    if status:
        qs = qs.filter(status_traduzido__iexact=status)

    qs = qs.order_by("-data_competencia")

    return [
        {
            "id": item.id,
            "data_competencia": item.data_competencia.strftime("%d/%m/%Y") if item.data_competencia else "-",
            "descricao": item.descricao,
            "categoria": item.categoria_id.nome if item.categoria_id else "-",
            "projeto": item.centro_custo_id.nome if item.centro_custo_id else "-",
            "pessoa": item.pessoa_id.nome if item.pessoa_id else "-",
            "total": float(_to_decimal(item.total)),
            "status": item.status_traduzido or "-",
        }
        for item in qs
    ]


# ── Agregado ───────────────────────────────────────────────────────────────────

def get_despesas(
    date_from: date,
    date_to: date,
    categoria_id: int = None,
    centro_custo_id: int = None,
    pessoa_id: int = None,
    status: str = None,
) -> dict:
    return {
        "kpis": get_kpis_despesas(date_from, date_to),
        "evolucao_diaria": get_evolucao_diaria_despesas(date_from, date_to),
        "top5_categorias": get_top5_categorias_despesas(date_from, date_to),
        "top5_projetos": get_top5_projetos_despesas(date_from, date_to),
        "status_por_semana": get_status_por_semana_despesas(date_from, date_to),
        "tabela": get_tabela_despesas(date_from, date_to, categoria_id, centro_custo_id, pessoa_id, status),
    }