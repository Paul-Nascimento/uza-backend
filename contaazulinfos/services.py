import math
import time
import logging
import requests

from .models import CentroCusto, Categoria, Pessoa, ContaAReceber, ContaAPagar

logger = logging.getLogger(__name__)

# ── Configurações globais ─────────────────────────────────────────────────────

TAMANHO_PAGINA = 1000
TIMEOUT_ENTRE_PAGINAS = 1   # segundos entre páginas — respeita rate limit
TIMEOUT_REQUISICAO = 15     # segundos de timeout por requisição HTTP


# ── Helper de requisição ──────────────────────────────────────────────────────

def _parse_date(valor):
    if not valor:
        return None
    return str(valor)[:10]  # pega só "2026-04-01" de "2026-04-01T13:42:36.539853"

def _get(url: str, headers: dict, pagina: int, tamanho: int = TAMANHO_PAGINA, extra_params: dict = None) -> dict:
    """
    Realiza GET paginado com validação de status HTTP.
    Lança requests.HTTPError para status 4xx/5xx.
    """
    params = {
        "pagina": str(pagina),
        "tamanho_pagina": str(tamanho),
    }
    if extra_params:
        params.update(extra_params)


    print(params)
    response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT_REQUISICAO)
    response.raise_for_status()
    return response.json()


def _iterar_paginas(url: str, headers: dict, chave_itens: str = "itens", chave_total: str = "itens_totais", extra_params: dict = None):
    """
    Generator que itera automaticamente por todas as páginas de um endpoint paginado.
    Yield: cada item individualmente.
    """
    primeira = _get(url, headers, pagina=1, extra_params=extra_params)
    total = primeira.get(chave_total, 0)
    logger.info(f"[{url}] Total de itens: {total}")

    if total == 0:
        return

    for item in primeira.get(chave_itens, []):
        yield item

    total_paginas = math.ceil(total / TAMANHO_PAGINA)

    for pagina in range(2, total_paginas + 1):
        logger.info(f"[{url}] Buscando página {pagina}/{total_paginas}...")
        time.sleep(TIMEOUT_ENTRE_PAGINAS)

        try:
            data = _get(url, headers, pagina=pagina, extra_params=extra_params)
            for item in data.get(chave_itens, []):
                yield item
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar página {pagina}: {e}")
            continue


def _resultado(criados, ignorados, erros) -> dict:
    return {"criados": criados, "ignorados": ignorados, "erros": erros}


# ── Centro de Custo ───────────────────────────────────────────────────────────

def cadastrar_centro_de_custo_via_api(token: str) -> dict:
    """
    Sincroniza todos os centros de custo da API com o banco local.
    Ignora registros já existentes (verifica por id_conta_azul).
    """
    url = "https://api-v2.contaazul.com/v1/centro-de-custo"
    headers = {"Authorization": f"Bearer {token}"}

    criados = ignorados = erros = 0

    for item in _iterar_paginas(url, headers):
        id_ca = item.get("id")
        if not id_ca:
            logger.warning(f"Centro de custo sem 'id', pulando: {item}")
            erros += 1
            continue

        try:
            if CentroCusto.objects.filter(id_conta_azul=id_ca).exists():
                ignorados += 1
                continue

            CentroCusto.objects.create(
                id_conta_azul=id_ca,
                codigo=item.get("codigo", ""),
                nome=item.get("nome", ""),
                ativo=str(item.get("ativo", "")).upper() == "TRUE"
            )
            criados += 1

        except Exception as e:
            print(e)
            logger.error(f"Erro ao salvar centro de custo {id_ca}: {e}")
            erros += 1

    logger.info(f"[CentroCusto] criados={criados} ignorados={ignorados} erros={erros}")
    return _resultado(criados, ignorados, erros)


# ── Categoria ─────────────────────────────────────────────────────────────────

def cadastrar_categoria_via_api(token: str) -> dict:
    """
    Sincroniza todas as categorias da API com o banco local.
    """
    url = "https://api-v2.contaazul.com/v1/categorias"
    headers = {"Authorization": f"Bearer {token}"}

    criados = ignorados = erros = 0

    for item in _iterar_paginas(url, headers):
        id_ca = item.get("id")
        if not id_ca:
            logger.warning(f"Categoria sem 'id', pulando: {item}")
            erros += 1
            continue

        try:
            if Categoria.objects.filter(id_conta_azul=id_ca).exists():
                ignorados += 1
                continue

            Categoria.objects.create(
                id_conta_azul=id_ca,
                versao=item.get("versao", 0),
                nome=item.get("nome", ""),
                categoria_pai=item.get("categoria_pai") or None,
                tipo=item.get("tipo", ""),           # RECEITA | DESPESA
                entrada_dre=item.get("entrada_dre", ""),
                considera_custo_dre=str(item.get("considera_custo_dre", "FALSE")).upper() == "TRUE"
            )
            criados += 1

        except Exception as e:
            logger.error(f"Erro ao salvar categoria {id_ca}: {e}")
            erros += 1

    logger.info(f"[Categoria] criados={criados} ignorados={ignorados} erros={erros}")
    return _resultado(criados, ignorados, erros)


# ── Pessoa ────────────────────────────────────────────────────────────────────

def cadastrar_pessoa_via_api(token: str) -> dict:
    """
    Sincroniza todas as pessoas (clientes, fornecedores, transportadores) com o banco local.
    Nota: a API de pessoas usa 'totalItems' e 'items' (sem acento) — diferente dos demais endpoints.
    """
    url = "https://api-v2.contaazul.com/v1/pessoas"
    headers = {"Authorization": f"Bearer {token}"}

    # Endpoint de pessoas usa chaves diferentes dos demais
    criados = ignorados = erros = 0

    for item in _iterar_paginas(url, headers, chave_itens="items", chave_total="totalItems"):
        id_ca = item.get("id")
        if not id_ca:
            logger.warning(f"Pessoa sem 'id', pulando: {item}")
            erros += 1
            continue

        try:
            if Pessoa.objects.filter(id_conta_azul=id_ca).exists():
                ignorados += 1
                continue

            # perfil pode vir como lista ou string dependendo da API
            perfil_raw = item.get("perfil") or item.get("tipo_pessoa") or ""
            perfil = perfil_raw if isinstance(perfil_raw, str) else perfil_raw[0] if perfil_raw else ""
            tipo_map = {"Jurídica": "JURIDICA", "Física": "FISICA"}
            Pessoa.objects.create(
                id_conta_azul=id_ca,
                nome=item.get("nome", ""),
                documento=item.get("documento") or None,
                ativo=str(item.get("ativo", "")).upper() == "TRUE",
                perfil=perfil,
                tipo = tipo_map.get(item.get("tipo_pessoa", ""), "")
            )
            criados += 1

        except Exception as e:
            logger.error(f"Erro ao salvar pessoa {id_ca}: {e}")
            erros += 1

    logger.info(f"[Pessoa] criados={criados} ignorados={ignorados} erros={erros}")
    return _resultado(criados, ignorados, erros)


# ── Conta a Receber ───────────────────────────────────────────────────────────

def cadastrar_conta_a_receber_via_api(token: str, data_de: str, data_ate: str) -> dict:
    """
    Sincroniza contas a receber do período informado.

    Args:
        data_de:  data de vencimento inicial no formato 'YYYY-MM-DD'
        data_ate: data de vencimento final  no formato 'YYYY-MM-DD'
    """
    url = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"
    headers = {"Authorization": f"Bearer {token}"}

    extra_params = {
        "data_vencimento_de": data_de,
        "data_vencimento_ate": data_ate,
    }

    print(extra_params)
    criados = ignorados = erros = 0

    for item in _iterar_paginas(url, headers, extra_params=extra_params):
        id_ca = item.get("id")
        if not id_ca:
            logger.warning(f"Conta a receber sem 'id', pulando: {item}")
            erros += 1
            continue

        try:
            if ContaAReceber.objects.filter(id_conta_azul=id_ca).exists():
                ignorados += 1
                continue

            # Resolve o FK de pessoa (cliente) — pode não existir ainda no banco
            cliente_raw = item.get("cliente") or {}
            cliente_id = cliente_raw.get("id")
            pessoa = None
            if cliente_id:
                pessoa = Pessoa.objects.filter(id_conta_azul=cliente_id).first()
                if not pessoa:
                    logger.warning(
                        f"Pessoa com id_conta_azul={cliente_id} não encontrada para "
                        f"conta a receber {id_ca}. Salvando sem vínculo."
                    )

            ContaAReceber.objects.create(
                id_conta_azul=id_ca,
                descricao=item.get("descricao", ""),
                total=item.get("total", 0),
                data_vencimento=_parse_date(item.get("data_vencimento")),
                data_competencia=_parse_date(item.get("data_competencia")),
                data_criacao=_parse_date(item.get("data_criacao")),
                data_alteracao=_parse_date(item.get("data_alteracao")),
                status=item.get("status", ""),
                status_traduzido=item.get("status_traduzido", ""),
                pago=item.get("pago", 0),
                nao_pago=item.get("nao_pago", 0),
                pessoa_id=pessoa,
            )
            criados += 1

        except Exception as e:
            logger.error(f"Erro ao salvar conta a receber {id_ca}: {e}")
            erros += 1

    logger.info(f"[ContaAReceber] criados={criados} ignorados={ignorados} erros={erros}")
    return _resultado(criados, ignorados, erros)


# ── Conta a Pagar ─────────────────────────────────────────────────────────────

def cadastrar_conta_a_pagar_via_api(token: str, data_de: str, data_ate: str) -> dict:
    url = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    headers = {"Authorization": f"Bearer {token}"}
    extra_params = {"data_vencimento_de": data_de, "data_vencimento_ate": data_ate}

    # ── 1. Carrega lookups em memória — elimina queries dentro do loop ─────────
    pessoas_map      = {p.id_conta_azul: p for p in Pessoa.objects.all()}
    categorias_map   = {c.id_conta_azul: c for c in Categoria.objects.all()}
    centros_map      = {cc.id_conta_azul: cc for cc in CentroCusto.objects.all()}
    existentes       = set(ContaAPagar.objects.values_list("id_conta_azul", flat=True))

    # ── 2. Coleta todos os itens da API ────────────────────────────────────────
    todos_itens = list(_iterar_paginas(url, headers, extra_params=extra_params))

    # ── 3. Separa novos e existentes ───────────────────────────────────────────
    para_criar     = []
    ids_atualizar  = []
    dados_atualizar = {}
    erros = 0

    for item in todos_itens:
        id_ca = item.get("id")
        if not id_ca:
            erros += 1
            continue

        fornecedor_id  = (item.get("fornecedor") or {}).get("id")
        cat_id         = ((item.get("categorias") or [{}])[0]).get("id")
        cc_id          = ((item.get("centros_de_custo") or [{}])[0]).get("id")

        defaults = dict(
            descricao        = item.get("descricao", ""),
            total            = item.get("total", 0),
            data_vencimento  = _parse_date(item.get("data_vencimento")),
            data_competencia = _parse_date(item.get("data_competencia")),
            data_criacao     = _parse_date(item.get("data_criacao")),
            data_alteracao   = _parse_date(item.get("data_alteracao")),
            status           = item.get("status", ""),
            status_traduzido = item.get("status_traduzido", ""),
            pago             = item.get("pago", 0),
            nao_pago         = item.get("nao_pago", 0),
            pessoa_id        = pessoas_map.get(fornecedor_id),
            categoria_id     = categorias_map.get(cat_id),
            centro_custo_id  = centros_map.get(cc_id),
        )

        if id_ca not in existentes:
            para_criar.append(ContaAPagar(id_conta_azul=id_ca, **defaults))
        else:
            ids_atualizar.append(id_ca)
            dados_atualizar[id_ca] = defaults

    # ── 4. bulk_create — insere tudo de uma vez ────────────────────────────────
    criados = 0
    BATCH = 500
    for i in range(0, len(para_criar), BATCH):
        lote = para_criar[i:i + BATCH]
        ContaAPagar.objects.bulk_create(lote, ignore_conflicts=True)
        criados += len(lote)

    # ── 5. bulk_update — atualiza existentes em lote ──────────────────────────
    atualizados = 0
    if ids_atualizar:
        objs_para_atualizar = []
        campos = list(next(iter(dados_atualizar.values())).keys())

        for obj in ContaAPagar.objects.filter(id_conta_azul__in=ids_atualizar):
            d = dados_atualizar[obj.id_conta_azul]
            for campo, valor in d.items():
                setattr(obj, campo, valor)
            objs_para_atualizar.append(obj)

        for i in range(0, len(objs_para_atualizar), BATCH):
            ContaAPagar.objects.bulk_update(objs_para_atualizar[i:i + BATCH], campos)
            atualizados += len(objs_para_atualizar[i:i + BATCH])

    logger.info(f"[ContaAPagar] criados={criados} atualizados={atualizados} erros={erros}")
    return {"criados": criados, "atualizados": atualizados, "erros": erros}