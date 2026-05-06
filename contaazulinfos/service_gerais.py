from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum

from contaazulinfos.models import ContaAPagar, CentroCusto
from vexpensesinfos.models import Expense


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_decimal(value) -> Decimal:
    return Decimal(str(value)) if value else Decimal("0.00")

def _periodo_anterior(date_from: date, date_to: date):
    delta = (date_to - date_from).days + 1
    return date_from - timedelta(days=delta), date_to - timedelta(days=delta)


# ── KPIs ───────────────────────────────────────────────────────────────────────

def get_kpis(date_from: date, date_to: date) -> dict:
    conta_azul = ContaAPagar.objects.filter(
        data_vencimento__gte=date_from,
        data_vencimento__lte=date_to,
        status_traduzido="ACQUITTED",
    )

    vexpenses_aprovadas = Expense.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
        report_status="APROVADO",
    )

    vexpenses_nao_aprovadas = Expense.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
    ).exclude(report_status="APROVADO")

    total_conta_azul = float(_to_decimal(conta_azul.aggregate(total=Sum("pago"))["total"]))
    total_vexpenses = float(_to_decimal(vexpenses_aprovadas.aggregate(total=Sum("value"))["total"]))
    total_nao_aprovadas = float(_to_decimal(vexpenses_nao_aprovadas.aggregate(total=Sum("value"))["total"]))

    return {
        "despesas_conta_azul": total_conta_azul,
        "despesas_vexpenses": total_vexpenses,
        "despesas_agregadas": total_conta_azul + total_vexpenses,
        "despesas_nao_aprovadas": total_nao_aprovadas,
    }


# ── Gráfico: Evolução ─────────────────────────────────────────────────────────

def _evolucao_diaria(date_from: date, date_to: date) -> list:
    date_from_ant, date_to_ant = _periodo_anterior(date_from, date_to)
    delta_ant = date_from_ant - date_from

    qs_atual = (
        ContaAPagar.objects.filter(
            data_vencimento__gte=date_from,
            data_vencimento__lte=date_to,
        )
        .values("data_vencimento")
        .annotate(total=Sum("pago"))
    )
    map_atual = {row["data_vencimento"]: float(_to_decimal(row["total"])) for row in qs_atual}

    qs_anterior = (
        ContaAPagar.objects.filter(
            data_vencimento__gte=date_from_ant,
            data_vencimento__lte=date_to_ant,
        )
        .values("data_vencimento")
        .annotate(total=Sum("pago"))
    )
    map_anterior = {row["data_vencimento"]: float(_to_decimal(row["total"])) for row in qs_anterior}

    resultado = []
    cursor = date_from
    while cursor <= date_to:
        dia_ant = cursor + delta_ant
        resultado.append({
            "label": cursor.strftime("%d/%m"),
            "atual": map_atual.get(cursor, 0.0),
            "anterior": map_anterior.get(dia_ant, 0.0),
        })
        cursor += timedelta(days=1)
    return resultado


def _evolucao_semanal(date_from: date, date_to: date) -> list:
    date_from_ant, _ = _periodo_anterior(date_from, date_to)

    resultado = []
    cursor = date_from
    cursor_ant = date_from_ant
    semana_num = 1

    while cursor <= date_to:
        fim = min(cursor + timedelta(days=6), date_to)
        fim_ant = cursor_ant + timedelta(days=6)

        atual = ContaAPagar.objects.filter(
            data_vencimento__gte=cursor,
            data_vencimento__lte=fim,
        ).aggregate(total=Sum("pago"))["total"] or 0

        anterior = ContaAPagar.objects.filter(
            data_vencimento__gte=cursor_ant,
            data_vencimento__lte=fim_ant,
        ).aggregate(total=Sum("pago"))["total"] or 0

        resultado.append({
            "label": f"Sem {semana_num}",
            "atual": float(_to_decimal(atual)),
            "anterior": float(_to_decimal(anterior)),
        })

        cursor = fim + timedelta(days=1)
        cursor_ant = fim_ant + timedelta(days=1)
        semana_num += 1

    return resultado


def _evolucao_mensal(date_from: date, date_to: date) -> list:
    date_from_ant, date_to_ant = _periodo_anterior(date_from, date_to)

    MESES_PT = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
        5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
    }

    qs_atual = (
        ContaAPagar.objects.filter(
            data_vencimento__gte=date_from,
            data_vencimento__lte=date_to,
        )
        .values("data_vencimento__year", "data_vencimento__month")
        .annotate(total=Sum("pago"))
    )
    map_atual = {
        (r["data_vencimento__year"], r["data_vencimento__month"]): float(_to_decimal(r["total"]))
        for r in qs_atual
    }

    qs_anterior = (
        ContaAPagar.objects.filter(
            data_vencimento__gte=date_from_ant,
            data_vencimento__lte=date_to_ant,
        )
        .values("data_vencimento__year", "data_vencimento__month")
        .annotate(total=Sum("pago"))
    )
    map_anterior = {
        (r["data_vencimento__year"], r["data_vencimento__month"]): float(_to_decimal(r["total"]))
        for r in qs_anterior
    }

    resultado = []
    cursor = date_from.replace(day=1)
    cursor_ant = date_from_ant.replace(day=1)
    while cursor <= date_to:
        chave = (cursor.year, cursor.month)
        chave_ant = (cursor_ant.year, cursor_ant.month)
        resultado.append({
            "label": f"{MESES_PT[cursor.month]}/{str(cursor.year)[2:]}",
            "atual": map_atual.get(chave, 0.0),
            "anterior": map_anterior.get(chave_ant, 0.0),
        })
        cursor = cursor.replace(month=cursor.month % 12 + 1, year=cursor.year + (cursor.month // 12))
        cursor_ant = cursor_ant.replace(month=cursor_ant.month % 12 + 1, year=cursor_ant.year + (cursor_ant.month // 12))

    return resultado


def get_evolucao(date_from: date, date_to: date) -> list:
    delta = (date_to - date_from).days
    if delta <= 31:
        return _evolucao_diaria(date_from, date_to)
    elif delta <= 90:
        return _evolucao_semanal(date_from, date_to)
    else:
        return _evolucao_mensal(date_from, date_to)


# ── Gráfico: Top 5 Categorias ─────────────────────────────────────────────────

def get_top5_categorias(date_from: date, date_to: date) -> list:
    COLORS = ["#C9F020", "#4ADE80", "#6EE7B7", "#0EA5E9", "#ADADAD"]
    qs = (
        ContaAPagar.objects.filter(
            data_vencimento__gte=date_from,
            data_vencimento__lte=date_to,
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


# ── Gráfico: Top 5 Projetos ───────────────────────────────────────────────────

def get_top5_projetos(date_from: date, date_to: date) -> list:
    qs = (
        ContaAPagar.objects.filter(
            data_vencimento__gte=date_from,
            data_vencimento__lte=date_to,
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


# ── Agregado ───────────────────────────────────────────────────────────────────

def get_visao_geral(date_from: date, date_to: date) -> dict:
    return {
        "kpis": get_kpis(date_from, date_to),
        "evolucao": get_evolucao(date_from, date_to),
        "top5_categorias": get_top5_categorias(date_from, date_to),
        "top5_projetos": get_top5_projetos(date_from, date_to),
    }