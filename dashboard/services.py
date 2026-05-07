from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count

from contaazulinfos.models import ContaAPagar, ContaAReceber, CentroCusto, Categoria, Pessoa
from vexpensesinfos.models import Expense, TeamMember


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _dec(value) -> Decimal:
    return Decimal(str(value)) if value else Decimal("0.00")

def _f(value) -> float:
    return float(_dec(value))

def _periodo_anterior(date_from: date, date_to: date):
    delta = (date_to - date_from).days + 1
    return date_from - timedelta(days=delta), date_to - timedelta(days=delta)

def _dias(date_from: date, date_to: date) -> list:
    dias, cursor = [], date_from
    while cursor <= date_to:
        dias.append(cursor)
        cursor += timedelta(days=1)
    return dias

MESES_PT = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
            7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

PIE_COLORS = ["#C9F020","#4ADE80","#6EE7B7","#0EA5E9","#ADADAD",
              "#22C55E","#F59E0B","#EF4444","#8B5CF6","#EC4899"]


# ══════════════════════════════════════════════════════════════════════════════
# VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════

def _vg_kpis(date_from: date, date_to: date) -> dict:
    ca = ContaAPagar.objects.filter(
        data_vencimento__gte=date_from,
        data_vencimento__lte=date_to,
        status="ACQUITTED",
    ).exclude(categoria_id__nome="Remessas Campo")

    vex_aprov = Expense.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
        report_status="APROVADO",
    )
    vex_nao_aprov = Expense.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
    ).exclude(report_status="APROVADO")

    total_ca  = _f(ca.aggregate(v=Sum("pago"))["v"])
    total_vex = _f(vex_aprov.aggregate(v=Sum("value"))["v"])
    nao_aprov = _f(vex_nao_aprov.aggregate(v=Sum("value"))["v"])


    return {
        "despesas_agregadas":    total_ca + total_vex,
        "despesas_conta_azul":   total_ca,
        "despesas_vexpenses":    total_vex,
        "despesas_nao_aprovadas": nao_aprov,
    }


def _vg_evolucao(date_from: date, date_to: date) -> list:
    delta = (date_to - date_from).days
    ant_from, ant_to = _periodo_anterior(date_from, date_to)

    if delta <= 31:
        # diário
        dias_atual = _dias(date_from, date_to)
        dias_ant   = _dias(ant_from, ant_to)
        qs_a = (ContaAPagar.objects.filter(data_vencimento__gte=date_from, data_vencimento__lte=date_to)
                .exclude(categoria_id__nome="Remessas Campo")
                .values("data_vencimento").annotate(t=Sum("pago")))
        qs_b = (ContaAPagar.objects.filter(data_vencimento__gte=ant_from, data_vencimento__lte=ant_to)
                .exclude(categoria_id__nome="Remessas Campo")
                .values("data_vencimento").annotate(t=Sum("pago")))
        map_a = {r["data_vencimento"]: _f(r["t"]) for r in qs_a}
        map_b = {r["data_vencimento"]: _f(r["t"]) for r in qs_b}
        return [{"label": d.strftime("%d/%m"), "atual": map_a.get(d,0.0),
                 "anterior": map_b.get(dias_ant[i],0.0) if i < len(dias_ant) else 0.0}
                for i,d in enumerate(dias_atual)]

    elif delta <= 90:
        # semanal
        resultado, cursor, cursor_ant, n = [], date_from, ant_from, 1
        while cursor <= date_to:
            fim = min(cursor + timedelta(days=6), date_to)
            fim_ant = cursor_ant + timedelta(days=6)
            atual = ContaAPagar.objects.filter(data_vencimento__gte=cursor, data_vencimento__lte=fim)\
                        .exclude(categoria_id__nome="Remessas Campo").aggregate(t=Sum("pago"))["t"] or 0
            ant   = ContaAPagar.objects.filter(data_vencimento__gte=cursor_ant, data_vencimento__lte=fim_ant)\
                        .exclude(categoria_id__nome="Remessas Campo").aggregate(t=Sum("pago"))["t"] or 0
            resultado.append({"label": f"Sem {n}", "atual": _f(atual), "anterior": _f(ant)})
            cursor = fim + timedelta(days=1); cursor_ant = fim_ant + timedelta(days=1); n += 1
        return resultado

    else:
        # mensal
        qs_a = (ContaAPagar.objects.filter(data_vencimento__gte=date_from, data_vencimento__lte=date_to)
                .exclude(categoria_id__nome="Remessas Campo")
                .values("data_vencimento__year","data_vencimento__month").annotate(t=Sum("pago")))
        qs_b = (ContaAPagar.objects.filter(data_vencimento__gte=ant_from, data_vencimento__lte=ant_to)
                .exclude(categoria_id__nome="Remessas Campo")
                .values("data_vencimento__year","data_vencimento__month").annotate(t=Sum("pago")))
        map_a = {(r["data_vencimento__year"],r["data_vencimento__month"]): _f(r["t"]) for r in qs_a}
        map_b = {(r["data_vencimento__year"],r["data_vencimento__month"]): _f(r["t"]) for r in qs_b}
        resultado, cursor, cursor_ant = [], date_from.replace(day=1), ant_from.replace(day=1)
        while cursor <= date_to:
            k = (cursor.year, cursor.month); kb = (cursor_ant.year, cursor_ant.month)
            resultado.append({"label": f"{MESES_PT[cursor.month]}/{str(cursor.year)[2:]}",
                               "atual": map_a.get(k,0.0), "anterior": map_b.get(kb,0.0)})
            m = cursor.month % 12 + 1; cursor = cursor.replace(month=m, year=cursor.year+(cursor.month//12))
            mb = cursor_ant.month % 12 + 1; cursor_ant = cursor_ant.replace(month=mb, year=cursor_ant.year+(cursor_ant.month//12))
        return resultado


def _vg_top_categorias(date_from: date, date_to: date, categoria_id: int = None, centro_custo_id: int = None) -> list:
    qs = ContaAPagar.objects.filter(data_vencimento__gte=date_from, data_vencimento__lte=date_to,
                                     categoria_id__isnull=False)\
          .exclude(categoria_id__nome="Remessas Campo")
    if categoria_id:    qs = qs.filter(categoria_id=categoria_id)
    if centro_custo_id: qs = qs.filter(centro_custo_id=centro_custo_id)
    qs = qs.values("categoria_id__nome").annotate(v=Sum("pago")).order_by("-v")[:10]
    totais = {r["categoria_id__nome"]: _f(r["v"]) for r in qs}

    vex = Expense.objects.filter(date__date__gte=date_from, date__date__lte=date_to,
                                  report_status="APROVADO").aggregate(v=Sum("value"))["v"] or 0
    if vex:
        totais["Vexpenses"] = totais.get("Vexpenses", 0.0) + _f(vex)

    ordenado = sorted(totais.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"name": n, "value": v, "color": PIE_COLORS[i % len(PIE_COLORS)]}
            for i, (n, v) in enumerate(ordenado)]


def _vg_top_projetos(date_from: date, date_to: date, categoria_id: int = None, centro_custo_id: int = None) -> list:
    qs_ca = ContaAPagar.objects.filter(data_vencimento__gte=date_from, data_vencimento__lte=date_to,
                                        centro_custo_id__isnull=False)\
             .exclude(categoria_id__nome="Remessas Campo")
    if categoria_id:    qs_ca = qs_ca.filter(categoria_id=categoria_id)
    if centro_custo_id: qs_ca = qs_ca.filter(centro_custo_id=centro_custo_id)
    qs_ca = qs_ca.values("centro_custo_id__nome").annotate(v=Sum("pago"))
    totais = {r["centro_custo_id__nome"]: _f(r["v"]) for r in qs_ca}

    centros = set(CentroCusto.objects.values_list("nome", flat=True))
    qs_vex = (Expense.objects.filter(date__date__gte=date_from, date__date__lte=date_to,
                                      report_status="APROVADO", apportionment_description__isnull=False)
              .values("apportionment_description").annotate(v=Sum("value")))
    for r in qs_vex:
        nome = r["apportionment_description"]; valor = _f(r["v"])
        totais[nome if nome in centros else "Vexpenses"] = totais.get(nome if nome in centros else "Vexpenses", 0.0) + valor

    sem = Expense.objects.filter(date__date__gte=date_from, date__date__lte=date_to,
                                  report_status="APROVADO", apportionment_description__isnull=True
                                  ).aggregate(v=Sum("value"))["v"] or 0
    if sem:
        totais["Vexpenses"] = totais.get("Vexpenses", 0.0) + _f(sem)

    ordenado = sorted(totais.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{"name": n, "value": v} for n, v in ordenado]


def get_visao_geral(date_from: date, date_to: date, categoria_id: int = None, centro_custo_id: int = None) -> dict:
    return {
        "kpis":            _vg_kpis(date_from, date_to),
        "evolucao":        _vg_evolucao(date_from, date_to),
        "top5_categorias": _vg_top_categorias(date_from, date_to, categoria_id, centro_custo_id),
        "top5_projetos":   _vg_top_projetos(date_from, date_to, categoria_id, centro_custo_id),
    }


# ══════════════════════════════════════════════════════════════════════════════
# DETALHAMENTO (Contas a Pagar)
# ══════════════════════════════════════════════════════════════════════════════

def get_despesas(date_from: date, date_to: date,
                 categoria_id: int = None, centro_custo_id: int = None,
                 pessoa_id: int = None, status: str = None) -> dict:

    qs = ContaAPagar.objects.select_related("categoria_id","centro_custo_id","pessoa_id").filter(
        data_competencia__gte=date_from, data_competencia__lte=date_to)
    if categoria_id:   qs = qs.filter(categoria_id=categoria_id)
    if centro_custo_id: qs = qs.filter(centro_custo_id=centro_custo_id)
    if pessoa_id:      qs = qs.filter(pessoa_id=pessoa_id)
    if status:         qs = qs.filter(status_traduzido__iexact=status)
    qs = qs.order_by("-data_competencia")

    tabela = [{"id": i.id,
               "data_competencia": i.data_competencia.strftime("%d/%m/%Y") if i.data_competencia else "-",
               "descricao": i.descricao,
               "categoria": i.categoria_id.nome if i.categoria_id else "-",
               "projeto":   i.centro_custo_id.nome if i.centro_custo_id else "-",
               "pessoa":    i.pessoa_id.nome if i.pessoa_id else "-",
               "total":     _f(i.total),
               "status":    i.status_traduzido or "-"} for i in qs]

    return {"tabela": tabela}


# ══════════════════════════════════════════════════════════════════════════════
# COLABORADORES
# ══════════════════════════════════════════════════════════════════════════════

def get_colaboradores(date_from: date, date_to: date, funcionario_id: int = None) -> dict:
    base = Expense.objects.filter(date__date__gte=date_from, date__date__lte=date_to, user__isnull=False)
    if funcionario_id:
        base = base.filter(user_id=funcionario_id)

    total = _dec(base.aggregate(v=Sum("value"))["v"])
    n = base.values("user_id").distinct().count()
    media = total / n if n > 0 else Decimal("0.00")

    maior = base.values("user_id","user__name").annotate(t=Sum("value")).order_by("-t").first()

    nao_aprovado = _f(base.exclude(report_status="APROVADO").aggregate(v=Sum("value"))["v"])

    # Ranking
    qs_rank = (base.values("user_id","user__name","report_status").annotate(v=Sum("value")).order_by("user__name"))
    cols: dict = {}
    for r in qs_rank:
        uid = r["user_id"]
        if uid not in cols: cols[uid] = {"name": r["user__name"]}
        cols[uid][r["report_status"] or "SEM_STATUS"] = _f(r["v"])
    ranking = list(cols.values())

    # Heatmap
    map_dias = {r["date__date"]: _f(r["t"]) for r in base.values("date__date").annotate(t=Sum("value"))}
    heatmap, cursor = [], date_from
    while cursor <= date_to:
        heatmap.append({"day": cursor.strftime("%d/%m/%Y"), "value": map_dias.get(cursor, 0.0)})
        cursor += timedelta(days=1)

    return {
        "kpis": {
            "total_gasto":       _f(total),
            "media_por_pessoa":  _f(media),
            "maior_gasto_nome":  maior["user__name"] if maior else "-",
            "maior_gasto_valor": _f(maior["t"]) if maior else 0.0,
            "total_nao_aprovado": nao_aprovado,
        },
        "ranking": ranking,
        "heatmap": heatmap,
    }


# ══════════════════════════════════════════════════════════════════════════════
# FLUXO DE CAIXA
# ══════════════════════════════════════════════════════════════════════════════

def get_fluxo_caixa(date_from: date, date_to: date) -> dict:
    entradas = _dec(ContaAReceber.objects.filter(
        data_alteracao__gte=date_from, data_alteracao__lte=date_to,
        status_traduzido="RECEBIDO").aggregate(v=Sum("pago"))["v"])
    saidas = _dec(ContaAPagar.objects.filter(
        data_alteracao__gte=date_from, data_alteracao__lte=date_to,
        status_traduzido="RECEBIDO").aggregate(v=Sum("pago"))["v"])
    saldo = entradas - saidas

    qs_e = (ContaAReceber.objects.filter(data_alteracao__gte=date_from, data_alteracao__lte=date_to,
                                          status_traduzido="RECEBIDO")
            .values("data_alteracao__year","data_alteracao__month").annotate(t=Sum("pago"))
            .order_by("data_alteracao__year","data_alteracao__month"))
    qs_s = (ContaAPagar.objects.filter(data_alteracao__gte=date_from, data_alteracao__lte=date_to,
                                        status_traduzido="RECEBIDO")
            .values("data_alteracao__year","data_alteracao__month").annotate(t=Sum("pago"))
            .order_by("data_alteracao__year","data_alteracao__month"))

    map_e = {(r["data_alteracao__year"],r["data_alteracao__month"]): _f(r["t"]) for r in qs_e}
    map_s = {(r["data_alteracao__year"],r["data_alteracao__month"]): _f(r["t"]) for r in qs_s}
    todos_meses = sorted(set(map_e.keys()) | set(map_s.keys()))

    saldo_ac, evolucao = 0.0, []
    for ano, mes in todos_meses:
        e = map_e.get((ano,mes), 0.0); s = map_s.get((ano,mes), 0.0)
        saldo_ac += e - s
        evolucao.append({"month": f"{MESES_PT[mes]}/{str(ano)[2:]}",
                         "entradas": e, "saidas": s, "saldo": round(saldo_ac,2)})

    return {"kpis": {"entradas": _f(entradas), "saidas": _f(saidas), "saldo": _f(saldo)},
            "evolucao_mensal": evolucao}


# ══════════════════════════════════════════════════════════════════════════════
# FILTER OPTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_filter_options() -> dict:
    return {
        "projetos":      list(CentroCusto.objects.filter(ativo=True).values("id","nome").order_by("nome")),
        "categorias":    list(Categoria.objects.values("id","nome").order_by("nome")),
        "pessoas":       list(Pessoa.objects.filter(ativo=True).values("id","nome").order_by("nome")),
        "colaboradores": [{"id":c["id"],"nome":c["name"]}
                          for c in TeamMember.objects.filter(active=True).values("id","name").order_by("name")],
        "status": [
            {"id":"RECEBIDO",          "nome":"Recebido"},
            {"id":"ATRASADO",          "nome":"Atrasado"},
            {"id":"EM_ABERTO",         "nome":"Em aberto"},
            {"id":"PARCIALMENTE_PAGO", "nome":"Parcialmente pago"},
        ],
    }