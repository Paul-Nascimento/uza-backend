"""
Rode com: python manage.py shell < exportar_dados.py
Ou salve como exportar_dados.py e execute:
  python manage.py shell -c "exec(open('exportar_dados.py').read())"
"""

import pandas as pd
from vexpensesinfos.models import Expense
from contaazulinfos.models import ContaAPagar

# ── Expenses (VExpenses) ──────────────────────────────────────────────────────
expenses_qs = Expense.objects.select_related("user").values(
    "id",
    "user_id",
    "user__name",
    "date",
    "value",
    "title",
    "report_id",
    "report_status",
    "report_description",
    "expense_type_id",
    "payment_method_id",
    "reimbursable",
    "rejected",
    "observation",
    "on",
    "created_at",
    "updated_at",
)

df_expenses = pd.DataFrame(list(expenses_qs))
df_expenses.rename(columns={"user__name": "user_nome"}, inplace=True)

# ── Contas a Pagar (Conta Azul) ───────────────────────────────────────────────
contas_qs = ContaAPagar.objects.select_related(
    "categoria_id", "centro_custo_id", "pessoa_id"
).values(
    "id",
    "id_conta_azul",
    "descricao",
    "total",
    "pago",
    "nao_pago",
    "data_vencimento",
    "data_competencia",
    "data_criacao",
    "data_alteracao",
    "status",
    "status_traduzido",
    "categoria_id",
    "categoria_id__nome",
    "centro_custo_id",
    "centro_custo_id__nome",
    "pessoa_id",
    "pessoa_id__nome",
)

df_contas = pd.DataFrame(list(contas_qs))
df_contas.rename(columns={
    "categoria_id__nome":    "categoria_nome",
    "centro_custo_id__nome": "centro_custo_nome",
    "pessoa_id__nome":       "pessoa_nome",
}, inplace=True)

# ── Remove timezone de colunas datetime ──────────────────────────────────────
for col in df_expenses.select_dtypes(include=["datetimetz"]).columns:
    df_expenses[col] = df_expenses[col].dt.tz_localize(None)

for col in df_contas.select_dtypes(include=["datetimetz"]).columns:
    df_contas[col] = df_contas[col].dt.tz_localize(None)

# ── Exporta ───────────────────────────────────────────────────────────────────
output = "dados_uza.xlsx"

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_expenses.to_excel(writer, sheet_name="Expenses_VExpenses", index=False)
    df_contas.to_excel(writer,   sheet_name="ContasAPagar_ContaAzul", index=False)

print(f"\nArquivo gerado: {output}")
print(f"  Expenses:      {len(df_expenses)} registros")
print(f"  ContasAPagar:  {len(df_contas)} registros")