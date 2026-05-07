import requests
import ast
from datetime import datetime

from .models import Project, TeamMember, ExpenseType, Expense

VEXPENSES_BASE_URL = "https://api.vexpenses.com/v2"

def _extract_apportionment_fields(apportionment_raw) -> dict:
    """Pull reimbursable_company_id and description from the first apportionment item."""
    try:
        if isinstance(apportionment_raw, str):
            apportionment_raw = ast.literal_eval(apportionment_raw)
        items = apportionment_raw.get("data", []) if isinstance(apportionment_raw, dict) else []
        if items:
            return {
                "apportionment_company_id": _safe_int(items[0].get("reimbursable_company_id")),
                "apportionment_description": items[0].get("description") or None,
            }
    except Exception:
        pass
    return {"apportionment_company_id": None, "apportionment_description": None}

def _headers(token: str) -> dict:
    return {"Authorization": token}


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _safe_int(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


# ── Projects ──────────────────────────────────────────────────────────────────

def sync_projects(token: str) -> dict:
    resp = requests.get(
        f"{VEXPENSES_BASE_URL}/projects",
        headers=_headers(token),
        params={"paginate": True, "page": 1, "per_page": 500},
    )
    resp.raise_for_status()
    items = resp.json().get("data", [])

    created = updated = 0
    for item in items:
        obj, is_new = Project.objects.update_or_create(
            id=item["id"],
            defaults={
                "name": item.get("name", ""),
                "company_name": item.get("company_name") or None,
                "cnpj": item.get("cnpj") or None,
                "address": item.get("address") or None,
                "neighborhood": item.get("neighborhood") or None,
                "city": item.get("city") or None,
                "state": item.get("state") or None,
                "zip_code": item.get("zip_code") or None,
                "phone1": item.get("phone1") or None,
                "phone2": item.get("phone2") or None,
                "on": item.get("on", True),
                "integration_id": str(item["integration_id"]) if item.get("integration_id") else None,
            },
        )
        if is_new:
            created += 1
        else:
            updated += 1

    return {"created": created, "updated": updated, "total": len(items)}


# ── Team Members ───────────────────────────────────────────────────────────────

def _extract_project_ids(projects_raw) -> list:
    """Parse the nested projects data from the API response."""
    if not projects_raw:
        return []
    try:
        if isinstance(projects_raw, str):
            projects_raw = ast.literal_eval(projects_raw)
        data = projects_raw.get("data", []) if isinstance(projects_raw, dict) else []
        return [p["id"] for p in data if "id" in p]
    except Exception:
        return []


def sync_team_members(token: str) -> dict:
    resp = requests.get(
        f"{VEXPENSES_BASE_URL}/team-members",
        headers=_headers(token),
        params={"include": "costsCenters,projects", "paginate": True, "page": 1, "per_page": 500},
    )
    resp.raise_for_status()
    items = resp.json().get("data", [])

    created = updated = 0
    for item in items:
        projects_data = item.get("projects", {})
        project_ids = _extract_project_ids(projects_data)

        obj, is_new = TeamMember.objects.update_or_create(
            id=item["id"],
            defaults={
                "integration_id": str(item["integration_id"]) if item.get("integration_id") else None,
                "external_id": str(item["external_id"]) if item.get("external_id") else None,
                "company_id": item.get("company_id"),
                "role_id": _safe_int(item.get("role_id")),
                "approval_flow_id": _safe_int(item.get("approval_flow_id")),
                "expense_limit_policy_id": _safe_int(item.get("expense_limit_policy_id")),
                "user_type": item.get("user_type", ""),
                "name": item.get("name", ""),
                "email": item.get("email") or None,
                "cpf": str(item["cpf"]) if item.get("cpf") else None,
                "phone1": item.get("phone1") or None,
                "phone2": item.get("phone2") or None,
                "birth_date": _parse_date(item.get("birth_date")),
                "bank": item.get("bank") or None,
                "agency": item.get("agency") or None,
                "account": item.get("account") or None,
                "pix_key": str(item["pix_key"]) if item.get("pix_key") else None,
                "confirmed": item.get("confirmed", False),
                "active": item.get("active", True),
                "created_at": _parse_date(item.get("created_at")),
                "updated_at": _parse_date(item.get("updated_at")),
            },
        )

        # Sync M2M projects (only those already in DB)
        existing_project_ids = list(
            Project.objects.filter(id__in=project_ids).values_list("id", flat=True)
        )
        obj.projects.set(existing_project_ids)

        if is_new:
            created += 1
        else:
            updated += 1

    return {"created": created, "updated": updated, "total": len(items)}


# ── Expense Types ──────────────────────────────────────────────────────────────

def sync_expense_types(token: str) -> dict:
    resp = requests.get(f"{VEXPENSES_BASE_URL}/expenses-type", headers=_headers(token))
    resp.raise_for_status()
    items = resp.json().get("data", [])

    created = updated = 0
    for item in items:
        _, is_new = ExpenseType.objects.update_or_create(
            id=item["id"],
            defaults={
                "integration_id": str(item["integration_id"]) if item.get("integration_id") else None,
                "description": item.get("description", ""),
                "on": item.get("on", True),
            },
        )
        if is_new:
            created += 1
        else:
            updated += 1

    return {"created": created, "updated": updated, "total": len(items)}


# ── Expenses ───────────────────────────────────────────────────────────────────

def _extract_report_fields(report_raw) -> dict:
    """Pull id, status and description from the nested report object."""
    try:
        if isinstance(report_raw, str):
            report_raw = ast.literal_eval(report_raw)
        data = report_raw.get("data", {}) if isinstance(report_raw, dict) else {}
        return {
            "report_id": _safe_int(data.get("id")),
            "report_status": data.get("status") or None,
            "report_description": data.get("description") or None,
        }
    except Exception:
        return {"report_id": None, "report_status": None, "report_description": None}


def sync_expenses(token: str, date_from: str, date_to: str) -> dict:
    resp = requests.get(
        f"{VEXPENSES_BASE_URL}/expenses",
        headers=_headers(token),
        params={
            "include":      "user,report,payment_method,apportionment",
            "search":       f"date:{date_from},{date_to}",
            "searchFields": "date:between",
            "searchJoin":   "and",
        },
    )
    resp.raise_for_status()
    items = resp.json().get("data", [])

    # ── Lookups em memória — zero queries dentro do loop ──────────────────────
    members_map = {m.id: m for m in TeamMember.objects.all()}
    existentes  = set(Expense.objects.values_list("id", flat=True))

    para_criar     = []
    para_atualizar = []  # lista de (id, defaults)

    for item in items:
        report_fields        = _extract_report_fields(item.get("report"))
        apportionment_fields = _extract_apportionment_fields(item.get("apportionment"))

        user_id  = _safe_int(item.get("user_id"))

        defaults = {
            "user":                   members_map.get(user_id),
            "expense_id":             _safe_int(item.get("expense_id")),
            "device_id":              _safe_int(item.get("device_id")),
            "integration_id":         str(item["integration_id"]) if item.get("integration_id") else None,
            "external_id":            str(item["external_id"]) if item.get("external_id") else None,
            "mileage":                item.get("mileage"),
            "date":                   _parse_date(item.get("date")),
            "expense_type_id":        _safe_int(item.get("expense_type_id")),
            "payment_method_id":      _safe_int(item.get("payment_method_id")),
            "paying_company_id":      _safe_int(item.get("paying_company_id")),
            "course_id":              _safe_int(item.get("course_id")),
            "receipt_url":            item.get("reicept_url") or None,
            "value":                  item.get("value"),
            "title":                  item.get("title") or None,
            "validate":               item.get("validate") or None,
            "reimbursable":           item.get("reimbursable", False),
            "observation":            item.get("observation") or None,
            "rejected":               bool(item.get("rejected", 0)),
            "on":                     item.get("on", True),
            "mileage_value":          item.get("mileage_value"),
            "original_currency_iso":  item.get("original_currency_iso") or None,
            "exchange_rate":          item.get("exchange_rate"),
            "converted_value":        item.get("converted_value"),
            "converted_currency_iso": item.get("converted_currency_iso") or None,
            "created_at":             _parse_date(item.get("created_at")),
            "updated_at":             _parse_date(item.get("updated_at")),
            **report_fields,
            **apportionment_fields,
        }

        expense_id = item["id"]
        if expense_id not in existentes:
            para_criar.append(Expense(id=expense_id, **defaults))
        else:
            para_atualizar.append((expense_id, defaults))

    # ── bulk_create em lotes de 500 ───────────────────────────────────────────
    BATCH = 500
    created = 0
    for i in range(0, len(para_criar), BATCH):
        Expense.objects.bulk_create(para_criar[i:i + BATCH], ignore_conflicts=True)
        created += len(para_criar[i:i + BATCH])

    # ── bulk_update em lotes de 500 ───────────────────────────────────────────
    updated = 0
    if para_atualizar:
        ids_map = {x[0]: x[1] for x in para_atualizar}
        campos  = list(next(iter(ids_map.values())).keys())
        objs    = []

        for obj in Expense.objects.filter(id__in=ids_map.keys()):
            for campo, valor in ids_map[obj.id].items():
                setattr(obj, campo, valor)
            objs.append(obj)

        for i in range(0, len(objs), BATCH):
            Expense.objects.bulk_update(objs[i:i + BATCH], campos)
            updated += len(objs[i:i + BATCH])

    return {"created": created, "updated": updated, "total": len(items)}


# ── Full sync ──────────────────────────────────────────────────────────────────

def sync_all(token: str, date_from: str, date_to: str) -> dict:
    """
    Sync in dependency order:
      1. Projects (no deps)
      2. TeamMembers (depend on Projects for M2M)
      3. ExpenseTypes (no deps)
      4. Expenses (depend on TeamMembers)
    """
    return {
        "projects": sync_projects(token),
        "team_members": sync_team_members(token),
        "expense_types": sync_expense_types(token),
        "expenses": sync_expenses(token, date_from, date_to),
    }