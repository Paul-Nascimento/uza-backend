from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum

from contaazulinfos.models import ContaAPagar, ContaAReceber, CentroCusto, Categoria, Pessoa
from vexpensesinfos.models import Expense, TeamMember, ExpenseType


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

CARTAO_VEXPENSES = "Cartão Vexpenses"
LABEL_EM_BRANCO  = "Em branco"


# ══════════════════════════════════════════════════════════════════════════════
# RESOLUÇÃO DE FILTROS Conta Azul ↔ Vexpenses
# ══════════════════════════════════════════════════════════════════════════════
#
# Os filtros no front sempre carregam IDs do Conta Azul (Categoria.id, CentroCusto.id),
# pois é a fonte canônica. Para aplicar o mesmo filtro nas queries do Vexpenses,
# casa-se pelo NOME (Categoria.nome == ExpenseType.description e
# CentroCusto.nome == Expense.apportionment_description).
#
# IMPORTANTE: se o nome no Conta Azul não bater EXATAMENTE com o equivalente
# no Vexpenses, a linha do Vexpenses é perdida no filtro. É um trade-off
# conhecido pela ausência de chave estrangeira entre os dois sistemas.
# ══════════════════════════════════════════════════════════════════════════════

def _categoria_nome_por_id(categoria_id):
    if not categoria_id:
        return None
    return Categoria.objects.filter(id=categoria_id).values_list("nome", flat=True).first()

def _centro_custo_nome_por_id(centro_custo_id):
    if not centro_custo_id:
        return None
    return CentroCusto.objects.filter(id=centro_custo_id).values_list("nome", flat=True).first()


def _resolve_projeto_filtro(centro_custo_id):
    """
    Traduz o valor recebido do front para um dicionário de instruções.

    Convenção de IDs (string):
      - "ca-<int>" → CentroCusto do Conta Azul (id é a PK do model).
      - "vx-<nome>" → projeto que só existe no VExpenses (chave = nome).
      - "indef"     → bucket INDEFINIDO (apportionment_description vazio/nulo).
      - None/""     → sem filtro.

    Compatibilidade: aceita também inteiro puro (legado) tratando como "ca-<id>".

    Retorno:
      {
        "tipo": "ca" | "vx" | "indef" | None,
        "cc_pk":  int|None,   # PK do CentroCusto quando tipo=="ca"
        "nome":   str|None,   # nome do projeto para casar no VExpenses
      }
    """
    if centro_custo_id in (None, "", 0):
        return {"tipo": None, "cc_pk": None, "nome": None}

    valor = str(centro_custo_id)

    if valor == "indef":
        return {"tipo": "indef", "cc_pk": None, "nome": None}

    if valor.startswith("ca-"):
        try:
            pk = int(valor[3:])
        except ValueError:
            return {"tipo": None, "cc_pk": None, "nome": None}
        nome = CentroCusto.objects.filter(id=pk).values_list("nome", flat=True).first()
        return {"tipo": "ca", "cc_pk": pk, "nome": nome}

    if valor.startswith("vx-"):
        return {"tipo": "vx", "cc_pk": None, "nome": valor[3:]}

    # Legado: inteiro puro → trata como CentroCusto do CA.
    try:
        pk = int(valor)
        nome = CentroCusto.objects.filter(id=pk).values_list("nome", flat=True).first()
        return {"tipo": "ca", "cc_pk": pk, "nome": nome}
    except ValueError:
        return {"tipo": None, "cc_pk": None, "nome": None}


def _expense_types_map():
    """{id: description} de todos os ExpenseTypes (carregado uma vez por request)."""
    return dict(ExpenseType.objects.values_list("id", "description"))


# ══════════════════════════════════════════════════════════════════════════════
# QuerySets-base reutilizáveis (com filtros aplicados nas DUAS fontes)
# ══════════════════════════════════════════════════════════════════════════════

def _qs_conta_azul_base(date_from, date_to, categoria_id=None, centro_custo_id=None):
    """
    QS base do Conta Azul para uso em KPIs/gráficos da Visão Geral.
    Regras fixas: data_vencimento no período, status='ACQUITTED',
    exclui 'Remessas Campo'.

    Filtro de projeto (centro_custo_id pode ser str "ca-<id>", "vx-<nome>",
    "indef" ou int legado — ver _resolve_projeto_filtro):
      - tipo "ca"     → filtra pelo CentroCusto.id.
      - tipo "vx"     → não há correspondência no CA → .none().
      - tipo "indef"  → não há correspondência no CA → .none().
    """
    qs = ContaAPagar.objects.filter(
        data_vencimento__gte=date_from,
        data_vencimento__lte=date_to,
        status="ACQUITTED",
    ).exclude(categoria_id__nome="Remessas Campo")
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    proj = _resolve_projeto_filtro(centro_custo_id)
    if proj["tipo"] == "ca":
        qs = qs.filter(centro_custo_id=proj["cc_pk"])
    elif proj["tipo"] in ("vx", "indef"):
        # Projeto sem correspondência no CA → não há linhas do CA pra esse filtro.
        return qs.none()
    return qs


def _qs_vexpenses_base(date_from, date_to, categoria_id=None, centro_custo_id=None,
                      only_report_status=None, exclude_report_status=None):
    """
    QS base do Vexpenses para uso em KPIs/gráficos da Visão Geral.

    Filtro de projeto (centro_custo_id pode ser str "ca-<id>", "vx-<nome>",
    "indef" ou int legado — ver _resolve_projeto_filtro):
      - tipo "ca"     → traduz o id para nome do CentroCusto e filtra
                        apportionment_description pelo nome. Se o nome não
                        existir no CA, retorna .none().
      - tipo "vx"     → filtra apportionment_description pelo nome direto.
      - tipo "indef"  → filtra apportionment_description nulo ou vazio.

    Se categoria_id foi pedido mas o nome correspondente não existe no
    ExpenseType, retorna .none().
    """
    qs = Expense.objects.filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
    )
    if categoria_id:
        cat_nome = _categoria_nome_por_id(categoria_id)
        if not cat_nome:
            return qs.none()
        type_ids = [tid for tid, desc in _expense_types_map().items() if desc == cat_nome]
        if not type_ids:
            return qs.none()
        qs = qs.filter(expense_type_id__in=type_ids)

    proj = _resolve_projeto_filtro(centro_custo_id)
    if proj["tipo"] == "ca":
        if not proj["nome"]:
            return qs.none()
        qs = qs.filter(apportionment_description=proj["nome"])
    elif proj["tipo"] == "vx":
        qs = qs.filter(apportionment_description=proj["nome"])
    elif proj["tipo"] == "indef":
        # Nulo OU string vazia.
        from django.db.models import Q
        qs = qs.filter(Q(apportionment_description__isnull=True) |
                       Q(apportionment_description__exact=""))

    if only_report_status is not None:
        qs = qs.filter(report_status=only_report_status)
    if exclude_report_status is not None:
        qs = qs.exclude(report_status=exclude_report_status)
    return qs


# ══════════════════════════════════════════════════════════════════════════════
# VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════

def _vg_kpis(date_from: date, date_to: date,
             categoria_id: int = None, centro_custo_id: int = None) -> dict:
    """
    KPIs agregados Conta Azul + Vexpenses. Respeita filtros de
    categoria e centro de custo (cross-filter da Visão Geral).
    """
    ca = _qs_conta_azul_base(date_from, date_to, categoria_id, centro_custo_id)

    # Vexpenses: "tudo" para o total, e "não APROVADO" para o card específico.
    vex_total = _qs_vexpenses_base(date_from, date_to, categoria_id, centro_custo_id)
    vex_nao_aprov = _qs_vexpenses_base(date_from, date_to, categoria_id, centro_custo_id,
                                       exclude_report_status="APROVADO")

    total_ca  = _f(ca.aggregate(v=Sum("pago"))["v"])
    total_vex = _f(vex_total.aggregate(v=Sum("value"))["v"])
    nao_aprov = _f(vex_nao_aprov.aggregate(v=Sum("value"))["v"])

    return {
        "despesas_agregadas":     total_ca + total_vex,
        "despesas_conta_azul":    total_ca,
        "despesas_vexpenses":     total_vex,
        "despesas_nao_aprovadas": nao_aprov,
    }


def _vg_evolucao(date_from: date, date_to: date,
                 categoria_id: int = None, centro_custo_id: int = None) -> list:
    """
    Série temporal das despesas. Granularidade muda conforme o tamanho do
    período: <=31 dias diária, <=90 dias semanal, >90 dias mensal.

    Aplica filtros de categoria/centro nas duas fontes e SOMA Conta Azul +
    Vexpenses ponto a ponto. A série 'anterior' compara o mesmo intervalo
    deslocado no Conta Azul (sem Vexpenses, mantendo o comportamento prévio).
    """
    delta = (date_to - date_from).days
    ant_from, ant_to = _periodo_anterior(date_from, date_to)

    ca_atual = _qs_conta_azul_base(date_from, date_to, categoria_id, centro_custo_id)
    ca_ant   = _qs_conta_azul_base(ant_from, ant_to,   categoria_id, centro_custo_id)
    vex_atual = _qs_vexpenses_base(date_from, date_to, categoria_id, centro_custo_id)

    if delta <= 31:
        # ── Diário ────────────────────────────────────────────────────────────
        dias_atual = _dias(date_from, date_to)
        dias_ant   = _dias(ant_from, ant_to)

        map_ca  = {r["data_vencimento"]: _f(r["t"]) for r in
                   ca_atual.values("data_vencimento").annotate(t=Sum("pago"))}
        map_ant = {r["data_vencimento"]: _f(r["t"]) for r in
                   ca_ant.values("data_vencimento").annotate(t=Sum("pago"))}
        # Vexpenses usa date (datetime) — group by date__date.
        map_vex = {r["date__date"]: _f(r["t"]) for r in
                   vex_atual.values("date__date").annotate(t=Sum("value"))}

        return [{
            "label":    d.strftime("%d/%m"),
            "atual":    map_ca.get(d, 0.0) + map_vex.get(d, 0.0),
            "anterior": map_ant.get(dias_ant[i], 0.0) if i < len(dias_ant) else 0.0,
        } for i, d in enumerate(dias_atual)]

    elif delta <= 90:
        # ── Semanal ───────────────────────────────────────────────────────────
        resultado, cursor, cursor_ant, n = [], date_from, ant_from, 1
        while cursor <= date_to:
            fim = min(cursor + timedelta(days=6), date_to)
            fim_ant = cursor_ant + timedelta(days=6)
            atual_ca  = _f(ca_atual.filter(data_vencimento__gte=cursor,
                                            data_vencimento__lte=fim).aggregate(t=Sum("pago"))["t"])
            atual_vex = _f(vex_atual.filter(date__date__gte=cursor,
                                             date__date__lte=fim).aggregate(t=Sum("value"))["t"])
            ant = _f(ca_ant.filter(data_vencimento__gte=cursor_ant,
                                    data_vencimento__lte=fim_ant).aggregate(t=Sum("pago"))["t"])
            resultado.append({"label": f"Sem {n}",
                              "atual": atual_ca + atual_vex,
                              "anterior": ant})
            cursor = fim + timedelta(days=1)
            cursor_ant = fim_ant + timedelta(days=1)
            n += 1
        return resultado

    else:
        # ── Mensal ────────────────────────────────────────────────────────────
        map_ca  = {(r["data_vencimento__year"], r["data_vencimento__month"]): _f(r["t"])
                   for r in ca_atual.values("data_vencimento__year","data_vencimento__month").annotate(t=Sum("pago"))}
        map_ant = {(r["data_vencimento__year"], r["data_vencimento__month"]): _f(r["t"])
                   for r in ca_ant.values("data_vencimento__year","data_vencimento__month").annotate(t=Sum("pago"))}
        map_vex = {(r["date__year"], r["date__month"]): _f(r["t"])
                   for r in vex_atual.values("date__year","date__month").annotate(t=Sum("value"))}

        resultado, cursor, cursor_ant = [], date_from.replace(day=1), ant_from.replace(day=1)
        while cursor <= date_to:
            k  = (cursor.year, cursor.month)
            kb = (cursor_ant.year, cursor_ant.month)
            resultado.append({
                "label":    f"{MESES_PT[cursor.month]}/{str(cursor.year)[2:]}",
                "atual":    map_ca.get(k, 0.0) + map_vex.get(k, 0.0),
                "anterior": map_ant.get(kb, 0.0),
            })
            m = cursor.month % 12 + 1
            cursor = cursor.replace(month=m, year=cursor.year + (cursor.month // 12))
            mb = cursor_ant.month % 12 + 1
            cursor_ant = cursor_ant.replace(month=mb, year=cursor_ant.year + (cursor_ant.month // 12))
        return resultado


def _vg_top_categorias(date_from: date, date_to: date,
                       categoria_id: int = None, centro_custo_id: int = None) -> list:
    """
    Top categorias (Conta Azul + Vexpenses) agregadas pelo nome da categoria.

    Retorna ID da Categoria do Conta Azul quando há match — isso permite
    o cross-filter no front: clique no slice → setFilters({categoryId: id}).
    Buckets sem match no CA viram 'Em branco' com id=null.

    Filtro agressivo: tanto 'categoria_id' quanto 'centro_custo_id' são
    aplicados. Quando há filtro de categoria ativo, o gráfico mostra apenas
    a categoria selecionada (1 fatia). 'Em branco' some naturalmente do
    resultado quando há filtro de categoria (id=null não casa com nenhum
    filtro).
    """
    # ── Conta Azul ──────────────────────────────────────────────────────────────
    qs_ca = (_qs_conta_azul_base(date_from, date_to, categoria_id, centro_custo_id)
             .filter(categoria_id__isnull=False)
             .values("categoria_id", "categoria_id__nome")
             .annotate(v=Sum("pago")))
    # Bucket: {nome: {"value": float, "id": int|None}}
    bucket: dict = {}
    for r in qs_ca:
        nome = r["categoria_id__nome"]
        bucket[nome] = {"id": r["categoria_id"], "value": _f(r["v"])}

    # ── Vexpenses ───────────────────────────────────────────────────────────────
    # Agrupa pelo expense_type_id, traduz para descrição, e tenta casar com
    # uma Categoria do Conta Azul pelo nome (para reaproveitar o ID).
    et_map = _expense_types_map()
    cat_id_por_nome = {c["nome"]: c["id"] for c in Categoria.objects.values("id", "nome")}

    qs_vex = (_qs_vexpenses_base(date_from, date_to, categoria_id, centro_custo_id)
              .values("expense_type_id")
              .annotate(v=Sum("value")))
    for r in qs_vex:
        descricao = et_map.get(r["expense_type_id"])
        valor = _f(r["v"])
        if not descricao:
            # Sem expense_type ou expense_type que não existe no dicionário → Em branco.
            entry = bucket.setdefault(LABEL_EM_BRANCO, {"id": None, "value": 0.0})
            entry["value"] += valor
            continue
        if descricao in bucket:
            bucket[descricao]["value"] += valor
        else:
            # Existe no Vexpenses mas não no Conta Azul → cria entrada.
            # Tenta achar uma Categoria com o mesmo nome para popular o id (raro).
            bucket[descricao] = {
                "id": cat_id_por_nome.get(descricao),
                "value": valor,
            }

    # Top 10, ordenados desc.
    ordenado = sorted(bucket.items(), key=lambda x: x[1]["value"], reverse=True)[:10]
    return [{"id": v["id"], "name": n, "value": v["value"],
             "color": PIE_COLORS[i % len(PIE_COLORS)]}
            for i, (n, v) in enumerate(ordenado)]


def _vg_top_projetos(date_from: date, date_to: date,
                     categoria_id: int = None, centro_custo_id: int = None) -> list:
    """
    Top projetos agregados (Conta Azul + Vexpenses).

    Regra de agregação:
      1) Base: centros de custo do Conta Azul (com 'pago' somado).
      2) Para cada despesa do Vexpenses (apportionment_description):
         - se o nome bate com um projeto já no bucket → SOMA o valor;
         - se NÃO bate → adiciona como projeto novo (id "vx-<nome>");
         - se vier nulo/vazio → vai para o projeto 'INDEFINIDO' (id "indef").

    Os 'id' retornados seguem a convenção _resolve_projeto_filtro:
      - "ca-<pk>" para CentroCusto do Conta Azul,
      - "vx-<nome>" para projeto exclusivo do VExpenses,
      - "indef" para o bucket INDEFINIDO.
    Isso permite que o front envie esse mesmo id de volta no filtro.
    """
    LABEL_INDEFINIDO = "INDEFINIDO"

    # ── 1. Base: Conta Azul ────────────────────────────────────────────────────
    qs_ca = (_qs_conta_azul_base(date_from, date_to, categoria_id, centro_custo_id)
             .filter(centro_custo_id__isnull=False)
             .values("centro_custo_id", "centro_custo_id__nome")
             .annotate(v=Sum("pago")))
    # bucket: {nome: {"id": "<token>", "value": float}}
    bucket: dict = {}
    for r in qs_ca:
        nome = r["centro_custo_id__nome"]
        bucket[nome] = {"id": f"ca-{r['centro_custo_id']}", "value": _f(r["v"])}

    # Lookup auxiliar: nome → pk do CentroCusto (cobre CCs sem movimento no período).
    cc_id_por_nome = {c["nome"]: c["id"] for c in CentroCusto.objects.values("id", "nome")}

    # ── 2. Vexpenses ───────────────────────────────────────────────────────────
    # 2a) Despesas COM apportionment_description preenchido.
    qs_vex_com = (_qs_vexpenses_base(date_from, date_to, categoria_id, centro_custo_id)
                  .exclude(apportionment_description__isnull=True)
                  .exclude(apportionment_description__exact="")
                  .values("apportionment_description")
                  .annotate(v=Sum("value")))
    for r in qs_vex_com:
        nome  = r["apportionment_description"]
        valor = _f(r["v"])
        if nome in bucket:
            bucket[nome]["value"] += valor
        else:
            # Sem correspondência no bucket: pode existir como CC no CA
            # (sem movimento no período) ou ser exclusivo do VEx.
            cc_pk = cc_id_por_nome.get(nome)
            token = f"ca-{cc_pk}" if cc_pk else f"vx-{nome}"
            bucket[nome] = {"id": token, "value": valor}

    # 2b) Despesas SEM apportionment_description → INDEFINIDO.
    from django.db.models import Q
    sem = (_qs_vexpenses_base(date_from, date_to, categoria_id, centro_custo_id)
           .filter(Q(apportionment_description__isnull=True) |
                   Q(apportionment_description__exact=""))
           .aggregate(v=Sum("value"))["v"])
    if sem:
        entry = bucket.setdefault(LABEL_INDEFINIDO, {"id": "indef", "value": 0.0})
        entry["value"] += _f(sem)

    # ── 3. Ordena e retorna top 10 ─────────────────────────────────────────────
    ordenado = sorted(bucket.items(), key=lambda x: x[1]["value"], reverse=True)[:10]
    return [{"id": v["id"], "name": n, "value": v["value"]} for n, v in ordenado]


def get_visao_geral(date_from: date, date_to: date,
                    categoria_id: int = None, centro_custo_id: int = None) -> dict:
    return {
        "kpis":            _vg_kpis(date_from, date_to, categoria_id, centro_custo_id),
        "evolucao":        _vg_evolucao(date_from, date_to, categoria_id, centro_custo_id),
        "top5_categorias": _vg_top_categorias(date_from, date_to, categoria_id, centro_custo_id),
        "top5_projetos":   _vg_top_projetos(date_from, date_to, categoria_id, centro_custo_id),
    }


# ══════════════════════════════════════════════════════════════════════════════
# DETALHAMENTO / DESPESAS (Agregação Conta Azul + Vexpenses)
# ══════════════════════════════════════════════════════════════════════════════
#
# Regras de agregação:
#   1) Conta Azul: apenas registros com status = 'ACQUITTED'
#                  e categoria diferente de 'Remessas Campo'
#   2) Vexpenses : todas as despesas do período
#                  - projeto    ← apportionment_description (PROJECT do Vexpenses)
#                  - categoria  ← descrição do ExpenseType (via expense_type_id)
#                  - pessoa     ← user.name (TeamMember)
#                  - cartao     ← 'Cartão Vexpenses'
#   3) Para Conta Azul, o campo 'cartao' é deixado como None (null).
#   4) Categoria/projeto vazios no Vexpenses → 'Em branco'.
#   5) As duas tabelas são unificadas em uma única lista, ordenada
#      decrescentemente por data de competência.
# ══════════════════════════════════════════════════════════════════════════════

def _tabela_conta_azul(date_from: date, date_to: date,
                       categoria_id: int = None, centro_custo_id: int = None,
                       pessoa_id: int = None, cartao: str = None) -> list:
    if cartao and cartao != "CONTA_AZUL":
        return []

    qs = ContaAPagar.objects.select_related(
        "categoria_id", "centro_custo_id", "pessoa_id"
    ).filter(
        data_competencia__gte=date_from,
        data_competencia__lte=date_to,
        status="ACQUITTED",
    ).exclude(categoria_id__nome="Remessas Campo")

    if categoria_id: qs = qs.filter(categoria_id=categoria_id)
    if pessoa_id:    qs = qs.filter(pessoa_id=pessoa_id)

    proj = _resolve_projeto_filtro(centro_custo_id)
    if proj["tipo"] == "ca":
        qs = qs.filter(centro_custo_id=proj["cc_pk"])
    elif proj["tipo"] in ("vx", "indef"):
        # Sem correspondência possível no CA.
        return []

    return [
        {
            "id":               f"ca-{i.id}",
            "origem":           "CONTA_AZUL",
            "data_competencia": i.data_competencia.strftime("%d/%m/%Y") if i.data_competencia else "-",
            "data_iso":         i.data_competencia.isoformat() if i.data_competencia else "",
            "descricao":        i.descricao,
            "categoria":        i.categoria_id.nome if i.categoria_id else LABEL_EM_BRANCO,
            "projeto":          i.centro_custo_id.nome if i.centro_custo_id else LABEL_EM_BRANCO,
            "pessoa":           i.pessoa_id.nome if i.pessoa_id else "-",
            "total":            _f(i.total),
            "status":           i.status_traduzido or "-",
            "cartao":           None,
        }
        for i in qs
    ]


def _tabela_vexpenses(date_from: date, date_to: date,
                      categoria_id: int = None, centro_custo_id: int = None,
                      pessoa_id: int = None, cartao: str = None) -> list:
    if cartao and cartao != "VEXPENSES":
        return []

    qs = Expense.objects.select_related("user").filter(
        date__date__gte=date_from,
        date__date__lte=date_to,
    )

    et_map = _expense_types_map()

    if categoria_id:
        cat_nome = _categoria_nome_por_id(categoria_id)
        if not cat_nome:
            return []
        type_ids = [tid for tid, desc in et_map.items() if desc == cat_nome]
        qs = qs.filter(expense_type_id__in=type_ids) if type_ids else qs.none()

    proj = _resolve_projeto_filtro(centro_custo_id)
    if proj["tipo"] == "ca":
        if not proj["nome"]:
            return []
        qs = qs.filter(apportionment_description=proj["nome"])
    elif proj["tipo"] == "vx":
        qs = qs.filter(apportionment_description=proj["nome"])
    elif proj["tipo"] == "indef":
        from django.db.models import Q
        qs = qs.filter(Q(apportionment_description__isnull=True) |
                       Q(apportionment_description__exact=""))

    # pessoa_id é ID do Conta Azul — não tem correspondente direto no Vexpenses,
    # então é ignorado para essas linhas (decisão preservada da v anterior).

    return [
        {
            "id":               f"vx-{e.id}",
            "origem":           "VEXPENSES",
            "data_competencia": e.date.strftime("%d/%m/%Y") if e.date else "-",
            "data_iso":         e.date.date().isoformat() if e.date else "",
            "descricao":        e.title or e.observation or "-",
            "categoria":        et_map.get(e.expense_type_id) or LABEL_EM_BRANCO,
            "projeto":          e.apportionment_description or LABEL_EM_BRANCO,
            "pessoa":           e.user.name if e.user else "-",
            "total":            _f(e.value),
            "status":           e.report_status or "-",
            "cartao":           CARTAO_VEXPENSES,
        }
        for e in qs
    ]


def get_despesas(date_from: date, date_to: date,
                 categoria_id: int = None, centro_custo_id: int = None,
                 pessoa_id: int = None, status: str = None) -> dict:
    """
    Retorna a tabela unificada de despesas (Conta Azul + Vexpenses).

    O parâmetro 'status', mantido por compatibilidade com a assinatura
    anterior, passa a ser interpretado como filtro de CARTÃO:
        - "CONTA_AZUL" → somente linhas do Conta Azul
        - "VEXPENSES"  → somente linhas do Vexpenses
        - None / vazio → ambos
    """
    cartao = status

    linhas_ca  = _tabela_conta_azul(date_from, date_to,
                                    categoria_id, centro_custo_id, pessoa_id, cartao)
    linhas_vex = _tabela_vexpenses(date_from, date_to,
                                   categoria_id, centro_custo_id, pessoa_id, cartao)

    tabela = linhas_ca + linhas_vex
    tabela.sort(key=lambda r: r.get("data_iso") or "", reverse=True)

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
    # ── Projetos: CentroCusto ativo do CA + projetos só do VExpenses + INDEFINIDO ──
    cc_ativos = list(CentroCusto.objects.filter(ativo=True)
                                        .values("id", "nome")
                                        .order_by("nome"))
    projetos = [{"id": f"ca-{c['id']}", "nome": c["nome"]} for c in cc_ativos]

    # Nomes que existem no CA (qualquer status) — usado pra detectar
    # projetos VEx que NÃO têm correspondência no CA.
    nomes_no_ca = set(CentroCusto.objects.values_list("nome", flat=True))

    # Nomes distintos vindos do VExpenses (não nulos, não vazios).
    nomes_vex = (Expense.objects
                 .exclude(apportionment_description__isnull=True)
                 .exclude(apportionment_description__exact="")
                 .values_list("apportionment_description", flat=True)
                 .distinct())

    # Adiciona ao filtro só os projetos que existem APENAS no VExpenses.
    exclusivos_vex = sorted({n for n in nomes_vex if n not in nomes_no_ca})
    projetos.extend([{"id": f"vx-{nome}", "nome": nome} for nome in exclusivos_vex])

    # INDEFINIDO aparece se houver despesa VEx com apportionment vazio/nulo.
    from django.db.models import Q
    tem_indefinido = Expense.objects.filter(
        Q(apportionment_description__isnull=True) |
        Q(apportionment_description__exact="")
    ).exists()
    if tem_indefinido:
        projetos.append({"id": "indef", "nome": "INDEFINIDO"})

    return {
        "projetos":      projetos,
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
        # Opções de Cartão para o filtro da tela de Despesas.
        # NOTA: os IDs ('CONTA_AZUL', 'VEXPENSES') permanecem como tokens
        # internos por questão de compatibilidade; apenas o 'nome' exibido
        # no front foi renomeado para 'Contas bancárias'.
        "cartoes": [
            {"id": "CONTA_AZUL", "nome": "Contas bancárias"},
            {"id": "VEXPENSES",  "nome": "Cartão Vexpenses"},
        ],
    }