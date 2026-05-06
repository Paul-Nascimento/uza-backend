from rest_framework import serializers
from .models import CentroCusto, Pessoa, Categoria, ContaAReceber, ContaAPagar


class CentroCustoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCusto
        fields = "__all__"


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = "__all__"


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class ContaAReceberSerializer(serializers.ModelSerializer):
    pessoa = PessoaSerializer(source="pessoa_id", read_only=True)

    class Meta:
        model = ContaAReceber
        fields = "__all__"


class ContaAPagarSerializer(serializers.ModelSerializer):
    pessoa = PessoaSerializer(source="pessoa_id", read_only=True)
    categoria = CategoriaSerializer(source="categoria_id", read_only=True)
    centro_custo = CentroCustoSerializer(source="centro_custo_id", read_only=True)

    class Meta:
        model = ContaAPagar
        fields = "__all__"