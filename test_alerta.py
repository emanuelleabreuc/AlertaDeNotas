"""Testes das funções que não precisam do navegador.

Para rodar: python test_alerta.py
Se nada der errado, aparece "Todos os testes passaram."
"""

import contextlib
import io
import os
import tempfile
 
import requests

import alerta
from alerta import comparar_notas, formatar_mensagem


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


# ---- formatar_mensagem ----

def test_mensagem_nota_nova():
    mensagem = formatar_mensagem([("Redes", "AV1", None, "8,50")])
    assert "Redes — AV1: 8,50" in mensagem


def test_mensagem_nota_corrigida():
    mensagem = formatar_mensagem([("POO II", "AV1", "7,0", "7,5")])
    assert "7,0 → 7,5 (corrigida)" in mensagem


def test_mensagem_varias_mudancas():
    mensagem = formatar_mensagem([("Redes", "AV1", None, "8,50"), ("POO II", "TF1", None, "10")])
    assert "Redes" in mensagem and "POO II" in mensagem


def test_mensagem_abaixo_da_media_so_em_prova():
    mensagem = formatar_mensagem([("POO II", "AV1", None, "1,90"), ("POO II", "TF2", None, "2")])
    linha_av1, linha_tf2 = mensagem.splitlines()[-2:]
    assert "abaixo da média" in linha_av1
    assert "abaixo da média" not in linha_tf2


def test_mensagem_so_colunas_ignoradas():
    assert formatar_mensagem([("Mobile", "Turma", None, "EO4M")]) is None


# ---- estado ----

def test_estado_salva_e_carrega():
    with tempfile.TemporaryDirectory() as pasta:
        alerta.ARQUIVO_ESTADO = os.path.join(pasta, "estado.json")
        notas = {"Programação": {"AV1": None, "TF1": "10"}}
        alerta.salvar_estado(notas)
        assert alerta.carregar_estado() == notas


def test_estado_inexistente_ou_corrompido():
    with tempfile.TemporaryDirectory() as pasta:
        alerta.ARQUIVO_ESTADO = os.path.join(pasta, "estado.json")
        assert alerta.carregar_estado() is None
        with open(alerta.ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
            f.write('{"Redes": ')
        assert alerta.carregar_estado() is None


# ---- enviar_notificacao (Telegram simulado, sem internet) ----

class RespostaFalsa:
    def __init__(self, status_code):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} for url: .../bot{alerta.TELEGRAM_TOKEN}/sendMessage")


def com_telegram(token, chat_id, post):
    """Troca o token, o chat_id e o requests.post por versões de teste."""
    alerta.TELEGRAM_TOKEN, alerta.TELEGRAM_CHAT_ID = token, chat_id
    alerta.requests.post = post


def test_envio_sem_telegram_so_mostra_no_terminal():
    com_telegram(None, None, post=None)  # se tentasse enviar, daria erro
    assert alerta.enviar_notificacao("oi") is True


def test_envio_telegram_ok():
    enviados = []
    com_telegram("123:abc", "999", lambda url, data, timeout: enviados.append(data) or RespostaFalsa(200))
    assert alerta.enviar_notificacao("oi") is True
    assert enviados == [{"chat_id": "999", "text": "oi"}]


def test_envio_telegram_falha():
    com_telegram("123:abc", "999", lambda url, data, timeout: RespostaFalsa(401))
    assert alerta.enviar_notificacao("oi") is False

    def sem_internet(url, data, timeout):
        raise requests.ConnectionError("sem internet")

    com_telegram("123:abc", "999", sem_internet)
    assert alerta.enviar_notificacao("oi") is False


def test_envio_no_github_actions_nao_mostra_notas_no_log():
    com_telegram("123:abc", "999", lambda url, data, timeout: RespostaFalsa(200))
    alerta.NO_GITHUB_ACTIONS = True
    saida = io.StringIO()
    try:
        with contextlib.redirect_stdout(saida):
            assert alerta.enviar_notificacao("Redes — AV1: 8,50") is True
    finally:
        alerta.NO_GITHUB_ACTIONS = False
    assert "8,50" not in saida.getvalue()


# ---- verificar_notas (navegador simulado) ----

def simular_ciclo(pasta, notas_do_portal, envio_funciona=True):
    """Roda verificar_notas trocando o navegador por funções falsas. Devolve as mensagens enviadas."""
    alerta.ARQUIVO_ESTADO = os.path.join(pasta, "estado.json")
    enviadas = []

    class NavegadorFalso:
        def quit(self):
            pass

    alerta.iniciar_navegador = NavegadorFalso
    alerta.abrir_portal = alerta.fazer_login = alerta.abrir_boletim = lambda driver: None
    alerta.extrair_notas = lambda driver: notas_do_portal
    alerta.enviar_notificacao = lambda mensagem: enviadas.append(mensagem) or envio_funciona
    alerta.verificar_notas()
    return enviadas


def test_ciclo_completo():
    with tempfile.TemporaryDirectory() as pasta:
        antes = {"POO II": {"AV1": None, "TF1": "10"}}
        depois = {"POO II": {"AV1": "5,60", "TF1": "10"}}

        # 1ª execução: só avisa que começou e salva
        enviadas = simular_ciclo(pasta, antes)
        assert len(enviadas) == 1 and "ativado" in enviadas[0]

        # nada mudou: não envia nada
        assert simular_ciclo(pasta, antes) == []

        # saiu a AV1, mas o envio falha: não salva...
        assert len(simular_ciclo(pasta, depois, envio_funciona=False)) == 1
        # ...então na próxima a novidade é enviada de novo
        enviadas = simular_ciclo(pasta, depois)
        assert len(enviadas) == 1 and "AV1: 5,60" in enviadas[0]

        # já foi avisada e salva: não envia de novo
        assert simular_ciclo(pasta, depois) == []


if __name__ == "__main__":
    # roda todas as funções deste arquivo que começam com "test_"
    for nome, funcao in list(globals().items()):
        if nome.startswith("test_"):
            funcao()
            print(f"ok  {nome}")
    print("Todos os testes passaram.")
