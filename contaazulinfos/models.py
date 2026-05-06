from django.db import models



class CentroCusto(models.Model):
    id_conta_azul = models.CharField(max_length=36)
    codigo = models.CharField(max_length=30,null=True)
    nome = models.CharField(max_length=120)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Pessoa(models.Model):
    PERFIL_CHOICES = (
        ('CLIENTE', 'Cliente'),
        ('FORNECEDOR', 'Fornecedor'),
        ('TRANSPORTADOR', 'Transportador'),
    )

    TIPO_CHOICES = (
        ('FISICA', 'Física'),
        ('JURIDICA', 'Jurídica'),
    )

    id_conta_azul = models.CharField(max_length=36)
    nome = models.CharField(max_length=120)
    ativo = models.BooleanField(default=True)
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    documento = models.CharField(max_length=14, blank=True, null=True)

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    TIPO_CHOICES = (
        ('RECEITA', 'Receita'),
        ('DESPESA', 'Despesa'),
    )


    id_conta_azul = models.CharField(max_length=36)
    nome = models.CharField(max_length=80)
    versao = models.IntegerField()
    categoria_pai = models.CharField(max_length=36, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    entrada_dre = models.CharField(max_length=50,null=True)
    considera_custo_dre = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class ContaAReceber(models.Model):

    id_conta_azul = models.CharField(max_length=36)
    descricao = models.TextField(max_length=100)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    data_vencimento = models.DateField()
    data_competencia = models.DateField(blank=True, null=True)
    data_criacao = models.DateField(blank=True,null=True)
    data_alteracao = models.DateField(blank=True)

    status = models.CharField(max_length=30)
    status_traduzido = models.CharField(max_length=30)

    pago = models.DecimalField(max_digits=15, decimal_places=2)
    nao_pago = models.DecimalField(max_digits=15, decimal_places=2)

    #categoria_id = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    #centro_custo_id = models.ForeignKey(CentroCusto, on_delete=models.PROTECT)
    pessoa_id = models.ForeignKey(Pessoa, on_delete=models.PROTECT,null=True)

    def __str__(self):
        return self.descricao


class ContaAPagar(models.Model):
    id_conta_azul = models.CharField(max_length=36)
    descricao = models.TextField(max_length=100)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    data_vencimento = models.DateField()
    data_competencia = models.DateField(blank=True, null=True)
    data_criacao = models.DateField(blank=True,null=True)
    data_alteracao = models.DateField(blank=True)

    status = models.CharField(max_length=30)
    status_traduzido = models.CharField(max_length=30)

    pago = models.DecimalField(max_digits=15, decimal_places=2)
    nao_pago = models.DecimalField(max_digits=15, decimal_places=2)

    categoria_id = models.ForeignKey(Categoria, on_delete=models.PROTECT,null=True)
    centro_custo_id = models.ForeignKey(CentroCusto, on_delete=models.PROTECT,null=True)
    pessoa_id = models.ForeignKey(Pessoa, on_delete=models.PROTECT,null=True)

    def __str__(self):
        return self.descricao
    

class ContaAzulToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()

    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token atualizado em {self.atualizado_em}"