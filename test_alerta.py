"""Testes das funções que não precisam do navegador.

Para rodar: python test_alerta.py
Se nada der errado, aparece "Todos os testes passaram."
"""

from alerta import comparar_notas


def test_nada_mudou():
    antigas = {"Redes": {"AV1": "8,50", "TF1": "10"}}
    novas = {"Redes": {"AV1": "8,50", "TF1": "10"}}
    assert comparar_notas(antigas, novas) == []


def test_nota_saiu():
    antigas = {"Redes": {"AV1": None, "TF1": "10"}}
    novas = {"Redes": {"AV1": "8,50", "TF1": "10"}}
    assert comparar_notas(antigas, novas) == [("Redes", "AV1", None, "8,50")]


def test_nota_corrigida():
    antigas = {"Redes": {"AV1": "7,0"}}
    novas = {"Redes": {"AV1": "7,5"}}
    assert comparar_notas(antigas, novas) == [("Redes", "AV1", "7,0", "7,5")]


def test_nota_apagada():
    antigas = {"Redes": {"AV1": "8,50"}}
    novas = {"Redes": {"AV1": None}}
    assert comparar_notas(antigas, novas) == [("Redes", "AV1", "8,50", None)]


def test_duas_notas_mudaram():
    antigas = {"Redes": {"AV1": None, "TF1": None}}
    novas = {"Redes": {"AV1": "8,50", "TF1": "10"}}
    assert comparar_notas(antigas, novas) == [
        ("Redes", "AV1", None, "8,50"),
        ("Redes", "TF1", None, "10"),
    ]


def test_mudancas_em_disciplinas_diferentes():
    antigas = {"Redes": {"AV1": None}, "POO II": {"AV1": "1,90"}}
    novas = {"Redes": {"AV1": "8,50"}, "POO II": {"AV1": "2,50"}}
    assert comparar_notas(antigas, novas) == [
        ("Redes", "AV1", None, "8,50"),
        ("POO II", "AV1", "1,90", "2,50"),
    ]


def test_disciplina_nova():
    # a disciplina não existia antes: cada coluna com valor conta como mudança,
    # e as colunas ainda vazias (None) não contam
    antigas = {}
    novas = {"Redes": {"AV1": "8,50", "TF1": None}}
    assert comparar_notas(antigas, novas) == [("Redes", "AV1", None, "8,50")]


def test_resultado_mudou():
    antigas = {"Redes": {"Resultado": "Cursando"}}
    novas = {"Redes": {"Resultado": "Aprovado"}}
    assert comparar_notas(antigas, novas) == [("Redes", "Resultado", "Cursando", "Aprovado")]


if __name__ == "__main__":
    # roda todas as funções deste arquivo que começam com "test_"
    for nome, funcao in list(globals().items()):
        if nome.startswith("test_"):
            funcao()
            print(f"ok  {nome}")
    print("Todos os testes passaram.")
