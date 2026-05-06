from .models import ContaAPagar
from vexpensesinfos.models import Expense
from django.db.models import Sum


def retornar_contas_pagas(date_from,date_to):

    contas_a_pagar = ContaAPagar.objects.filter(
        data_vencimento__gte=date_from,
        data_vencimento__lte=date_to,
        status="ACQUITTED"
    )

    print(contas_a_pagar)

    ###eSSE VALOR AQUI VAI SER O DO CARD V2 DA PAGINA VISÃO GERAL
    total_despesas_conta_azul = contas_a_pagar.aggregate(
        total=Sum("pago")
    )['total']

    print(total_despesas_conta_azul)

    #Pegar despesas do vexpenses
    expenses = Expense.objects.filter(
        date__gte=date_from,
        date__lte=date_to,
        report_status="APROVADO"
    )

    despesas_nao_aprovadas_vexpenses = Expense.objects.filter(
        date__gte=date_from,
        date__lte=date_to
    ).exclude(report_status="APROVADO")

    total_de_despesas_vexpenses = expenses.aggregate(
        total=Sum('value')
    )['total']

    print(total_de_despesas_vexpenses)

    total_despesas_conta_azul = contas_a_pagar.aggregate(total=Sum("pago"))["total"] or 0
    total_de_despesas_vexpenses = expenses.aggregate(total=Sum("value"))["total"] or 0
    total_de_despesas_agregadas = total_de_despesas_vexpenses + total_despesas_conta_azul

    total_de_despesas_nao_aprovadas = despesas_nao_aprovadas_vexpenses.aggregate(
        total=Sum('value')
    )['total']


    data = {
        "despesas_conta_azul":total_despesas_conta_azul,
        "despesas_vexpenses":total_de_despesas_vexpenses,
        "despesas_agregadas":total_de_despesas_agregadas,
        "despesas_nao_aprovadas":total_de_despesas_nao_aprovadas
    }

    print(data)