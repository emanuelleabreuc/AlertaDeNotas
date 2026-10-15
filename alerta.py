import json
import os
import sys
import time
from datetime import datetime, timedelta

import requests  # faz requisições HTTP (usado para mandar mensagem no Telegram)
from dotenv import load_dotenv
from selenium import webdriver  # selenium automatiza ações em navegadores
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

 

# pasta onde está este arquivo. Os outros arquivos (.env, estado.json, prints de erro) ficam nela,
# mesmo quando o script é chamado de outra pasta (ex.: pelo Agendador de Tarefas do Windows)
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(PASTA_PROJETO, ".env")) #le o arq .env


MATRICULA = os.getenv("MATRICULA")
SENHA = os.getenv("SENHA")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # token do bot, dado pelo @BotFather
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # para quem o bot manda a mensagem (você)

# o GitHub Actions define GITHUB_ACTIONS=true. Lá o repositório é público e os logs também,
# então as notas não podem aparecer no terminal: só vão pelo Telegram
NO_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


URL_PORTAL = "https://aluno.uvv.br/"
INTERVALO_MINUTOS = 30  # de quanto em quanto tempo checar 
HEADLESS = True  # True: o Chrome roda sem abrir janela. Mude para False para ver o navegador ao depurar
TIMEOUT = 15
TIMEOUT_TELEGRAM = 10  # segundos esperando o Telegram responder
TIMEOUT_LOGIN = 20
SELETOR_CAMPO_MATRICULA = (By.ID, "Matricula")
SELETOR_CAMPO_SENHA = (By.ID, "Password")
SELETOR_BOTAO_ENTRAR = (By.CSS_SELECTOR, "button.portal-login-submit") 
SELETOR_LOGADO = (By.CSS_SELECTOR, ".fa-sign-out")  # ícone de logout, que só aparece quando logado
SELETOR_ERRO_LOGIN = (By.CSS_SELECTOR, ".portal-login-feedback.portal-login-feedback-danger")  # mensagem de erro de login
SELETOR_BOLETIM = (By.CSS_SELECTOR,".fa-list-alt" )
SELETOR_TABELA_NOTAS = (By.CSS_SELECTOR, ".conteudo-body table" )
SELETOR_LINHAS_NOTAS = (By.CSS_SELECTOR, ".conteudo-body tbody tr" )
SELETOR_CABECALHO = (By.CSS_SELECTOR, "thead th")
SELETOR_CELULAS = (By.CSS_SELECTOR, "td")
SELETOR_DISCIPLINA = (By.CSS_SELECTOR, "td.texto" )
ARQUIVO_ESTADO = os.path.join(PASTA_PROJETO, "estado.json")
COLUNAS_IGNORADAS = ["Período", "Turma", "Disciplina"]  # colunas que não importam para o alerta
MEDIA = 7.0  # nota mínima para aprovação
COLUNAS_PROVA = ["AV1", "AV2", "MP", "PF", "Final"]


def carregar_credenciais():
    """Confere se as variáveis do .env foram preenchidas. Para o script se faltar algo."""
    # lista que vai guardar o nome das variáveis que não foram preenchidas
    faltando = [] #guarda as variáveis que não foram preenchidas

    # confere se a matrícula está vazia ou ainda com o texto de exemplo ("coloque_...")
    if not MATRICULA or MATRICULA.startswith("coloque_"):
        faltando.append("MATRICULA")

    # mesma conferência para a senha
    if not SENHA or SENHA.startswith("coloque_"):
        faltando.append("SENHA")

    # o Telegram é opcional, mas se uma das duas variáveis foi preenchida, a outra também precisa ser
    if telegram_configurado() != bool(preenchida(TELEGRAM_TOKEN) or preenchida(TELEGRAM_CHAT_ID)):
        faltando.append("TELEGRAM_TOKEN e TELEGRAM_CHAT_ID (preencha os dois ou nenhum)")

    # no GitHub Actions ninguém olha o terminal: sem Telegram, as novidades se perderiam
    if NO_GITHUB_ACTIONS and not telegram_configurado():
        faltando.append("TELEGRAM_TOKEN e TELEGRAM_CHAT_ID (obrigatórios no GitHub Actions)")

    # se faltou alguma variável, mostra quais são e encerra o script com código de erro
    if faltando:
        onde = "nos Secrets do GitHub" if NO_GITHUB_ACTIONS else "no arquivo .env"
        print(f"Erro: preencha {onde} -> {', '.join(faltando)}")
        sys.exit(1)

    # tudo certo: confirma o carregamento (mostra só o tamanho da senha, nunca a senha em si)
    print("Variáveis carregadas com sucesso.")
    print(f"Matrícula: {MATRICULA}")
    print(f"Tamanho da senha: {len(SENHA)} caracteres")
    if telegram_configurado():
        print("Telegram configurado: as novidades vão chegar no celular.")
    else:
        print("Telegram não configurado: as novidades só vão aparecer no terminal.")


def preenchida(variavel):
    """Diz se uma variável do .env foi preenchida (não está vazia nem com o texto de exemplo)."""
    return bool(variavel) and not variavel.startswith("coloque_")


def telegram_configurado():
    """Diz se o token e o chat_id do Telegram foram preenchidos no .env."""
    return preenchida(TELEGRAM_TOKEN) and preenchida(TELEGRAM_CHAT_ID)


def iniciar_navegador(): 
    """Inicia o Chrome (sem janela se HEADLESS for True)."""
    opcoes = webdriver.ChromeOptions()
    if HEADLESS:
        opcoes.add_argument("--headless=new")  # roda o Chrome sem abrir janela
        # sem janela, o Chrome usa uma tela pequena; com ela o portal pode esconder o menu e o ícone do boletim
        opcoes.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=opcoes) #faz o driver do navegador abrir o chrome
    if not HEADLESS:
        driver.maximize_window() #maximiza a janela do navegador
    return driver #mostra o driver para ser usado em outras funções


def salvar_screenshot(driver, motivo):
    """Salva um print da tela do navegador, para entender o que deu errado (útil sem janela)."""
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # ex.: 2026-10-14_15-30-00
    caminho = os.path.join(PASTA_PROJETO, f"erro_{agora}_{motivo}.png")
    try:
        driver.save_screenshot(caminho)
        print(f"Print da tela salvo em {caminho}")
    except Exception:
        # se nem o print funcionar (navegador travado), só avisa: o erro original é o que importa
        print("Não foi possível salvar o print da tela.")

def abrir_portal(driver):
    """Abre o portal e espera o campo de matrícula ficar visível."""
    # navega até a página inicial do portal
    driver.get(URL_PORTAL)

    # espera até TIMEOUT segundos o campo de matrícula ficar visível (sinal de que a página carregou)
    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located(SELETOR_CAMPO_MATRICULA)
        )
    # se o campo não aparecer a tempo, avisa o motivo provável e repassa o erro para cima
    except TimeoutException:
        print(
            "Erro: o campo de matrícula não apareceu. Confira o seletor, "
            "se existe iframe ou se a página carregou."
        )
        raise

    # chegou aqui: a página do portal está pronta para o login
    print("Portal carregado com sucesso.")


def fazer_login(driver):
    """Preenche matrícula e senha, clica em Entrar e confere se o login deu certo."""
    # localiza o campo de matrícula e preenche com o valor do .env
    campo_matricula = driver.find_element(*SELETOR_CAMPO_MATRICULA)
    campo_matricula.clear() #limpa o campo caso já tenha algo escrito
    campo_matricula.send_keys(MATRICULA) #digita a matrícula

    # localiza o campo de senha, limpa e preenche com o valor do .env
    campo_senha = driver.find_element(*SELETOR_CAMPO_SENHA)
    campo_senha.clear()
    campo_senha.send_keys(SENHA) #digita a senha

    # envia o formulário de login
    WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable(SELETOR_BOTAO_ENTRAR)
    ).click() #espera o botão poder ser clicado e clica

    # espera aparecer o ícone de logout (deu certo) ou a mensagem de erro (deu errado)
    try:
        WebDriverWait(driver, TIMEOUT_LOGIN).until(
            EC.any_of(
                EC.visibility_of_element_located(SELETOR_LOGADO),
                EC.visibility_of_element_located(SELETOR_ERRO_LOGIN),
            )
        )
    except TimeoutException:
        print("Erro: o login não respondeu a tempo. Confira os seletores do botão e da página logada.")
        raise

    # se o que apareceu foi a mensagem de erro, mostra o texto dela e interrompe com erro
    erros = driver.find_elements(*SELETOR_ERRO_LOGIN)
    if erros and erros[0].is_displayed():
        print(f"Erro no login: {erros[0].text.strip()}")
        raise RuntimeError("Login recusado pelo portal.")

    # nenhum erro visível: o ícone de logout apareceu, então o login funcionou
    print("Login realizado com sucesso.")



def abrir_boletim(driver):
    """Clica no link do boletim e espera ele abrir (na mesma aba ou em uma nova)."""
    # guarda a URL atual e a quantidade de abas antes do clique,
    # para depois saber se a página mudou ou se uma nova aba foi aberta
    url_antes = driver.current_url
    abas_antes = len(driver.window_handles)

    # espera o ícone do boletim poder ser clicado e clica nele
    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable(SELETOR_BOLETIM)
        ).click()
    except TimeoutException:
        print("Erro: o link do boletim não apareceu. Confira o seletor.")
        raise

    # espera acontecer uma de duas coisas: abrir uma aba nova OU a URL da aba atual mudar
    try:
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: len(d.window_handles) > abas_antes or d.current_url != url_antes
        )
    except TimeoutException:
        print("Erro: o boletim não abriu em nova aba ou mudou de página. Confira o seletor.")
        raise

    # se o boletim abriu em outra aba, passa o controle do selenium para essa aba (a última da lista)
    if len(driver.window_handles) > abas_antes:
        driver.switch_to.window(driver.window_handles[-1])  # muda para a nova aba

    # espera a página do boletim terminar de carregar por completo
    WebDriverWait(driver, TIMEOUT).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    print(f"Boletim aberto com sucesso: {driver.current_url}")

def limpar_valor(texto):
    """Limpa o valor do texto, removendo espaços em branco e quebras de linha."""
    texto = texto.strip()  # remove espaços em branco do início e do fim
    if texto in ("-", ""): #se n tem valor, retorna None
        return None 
    return texto

def extrair_notas(driver):
    """Lê as tabelas do boletim e devolve as notas de cada disciplina."""
    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located(SELETOR_LINHAS_NOTAS)
        )
    except TimeoutException:
        print(
            "Erro: as linhas de notas não apareceram. Confira o seletor "
            "ou se a página aberta é mesmo a do boletim.")
        raise

    print("Tabela de notas carregada.")

    primeira_tabela = driver.find_element(*SELETOR_TABELA_NOTAS)  # localiza a tabela de notas
    celulas_cabecalho = primeira_tabela.find_elements(*SELETOR_CABECALHO)  # localiza as células do cabeçalho da tabela
    colunas = [th.text.strip() for th in celulas_cabecalho]  # pega os nomes das colunas

    linhas = driver.find_elements(*SELETOR_LINHAS_NOTAS)  # localiza as linhas da tabela
    notas = {}  # vai guardar {disciplina: {coluna: valor}}
    for linha in linhas:
        disciplina = linha.find_element(*SELETOR_DISCIPLINA).text.strip()  # singular: cada linha tem uma só disciplina
        valores = [td.text for td in linha.find_elements(*SELETOR_CELULAS)]

        # o zip descarta sem avisar o que sobra quando as listas têm tamanhos diferentes,
        # então confere antes: se a linha não bate com o cabeçalho, avisa e pula essa disciplina
        if len(valores) != len(colunas):
            print(f"Aviso: '{disciplina}' tem {len(valores)} células, mas o cabeçalho tem {len(colunas)}. Linha ignorada.")
            continue

        # junta cada nome de coluna com o valor da célula na mesma posição, já limpo
        notas[disciplina] = {coluna: limpar_valor(valor) for coluna, valor in zip(colunas, valores)}

    print(f"Notas extraídas: {len(notas)} disciplinas.")
    return notas  # devolve o dicionário para quem chamou a função

#--- estado ---

def salvar_estado(notas):
    """Salva o dicionário de notas no arquivo JSON."""
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(notas, f, ensure_ascii=False, indent=2)
    print(f"Estado salvo em {ARQUIVO_ESTADO}.")

def carregar_estado():
    """Carrega o dicionário de notas do arquivo JSON. Se não existir ou estiver corrompido, devolve None."""
    try:
        with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
            notas = json.load(f)
        print(f"Estado carregado de {ARQUIVO_ESTADO}.")
        return notas
    except FileNotFoundError:
        print("Nenhum estado anterior encontrado. Começando do zero.")
        return None
    except json.JSONDecodeError:
        print(f"Aviso: {ARQUIVO_ESTADO} está corrompido. Começando do zero.")
        return None

#---lógica principal---

def comparar_notas(antigas, novas):
    mudancas = []
    for disciplina, notas_novas in novas.items():
        notas_antigas = antigas.get(disciplina, {})
        for coluna, valor_novo in notas_novas.items():
            valor_antigo = notas_antigas.get(coluna)
            if valor_novo != valor_antigo:
                mudancas.append((disciplina, coluna, valor_antigo, valor_novo))
    return mudancas

#--- notificação ---

def abaixo_da_media(valor):
    """Diz se o valor é uma nota menor que a MEDIA. Textos como "Cursando" devolvem False."""
    try:
        return float(valor.replace(",", ".")) < MEDIA  # "1,90" vira 1.9 para poder comparar
    except (ValueError, AttributeError):  # não é número ("Cursando") ou é None
        return False


def formatar_mensagem(mudancas):
    """Formata a lista de mudanças em uma mensagem legível."""
    linhas = []
    for disciplina, coluna, antigo, novo in mudancas:
        if coluna in COLUNAS_IGNORADAS:
            continue  # ignora colunas que não importam para o alerta
        if coluna == "Resultado":
            linha = f"• {disciplina} — Resultado: {novo}"  # ex.: Cursando → Aprovado
        elif antigo is None:
            linha = f"• {disciplina} — {coluna}: {novo}"  # nota que acabou de sair
        elif novo is None:
            linha = f"• {disciplina} — {coluna}: removida (era {antigo})"

        else:
            linha = f"• {disciplina} — {coluna}: {antigo} → {novo} (corrigida)"

        if coluna in COLUNAS_PROVA and abaixo_da_media(novo):
            linha += " ⚠️ abaixo da média"  # adiciona um aviso se a nota estiver abaixo da média
        linhas.append(linha)

    if not linhas:
        return None

    return "📢 Novidades no boletim!\n\n" + "\n".join(linhas)


def enviar_notificacao(mensagem):
    """Envia a mensagem para o Telegram. Se não tiver token ou chat_id, só mostra no terminal.
    Devolve True se a entrega deu certo e False se falhou."""
    if NO_GITHUB_ACTIONS:
        print("Enviando notificação (o conteúdo não aparece aqui porque o log do GitHub é público).")
    else:
        print(mensagem)  # mostra no terminal

    if not telegram_configurado():
        return True  # sem Telegram, mostrar no terminal já é a entrega

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resposta = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem},
            timeout=TIMEOUT_TELEGRAM,  # sem timeout, uma internet travada deixaria o script esperando para sempre
        )
        resposta.raise_for_status()  # transforma respostas de erro do Telegram (401, 400...) em exceção
    except requests.HTTPError:
        # não mostra o erro inteiro: a mensagem dele contém a URL, e a URL contém o token
        print(f"Erro do Telegram (código {resposta.status_code}). Confira TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no .env.")
        return False
    except requests.RequestException as erro:
        print(f"Erro de conexão com o Telegram ({type(erro).__name__}). Confira a internet.")
        return False

    print("Notificação enviada pelo Telegram.")
    return True


def verificar_notas():
    """Compara as notas atuais com as anteriores e envia notificação se houver mudanças."""
    notas_anteriores = carregar_estado()
    driver = iniciar_navegador()

    try:
        abrir_portal(driver)
        fazer_login(driver)
        abrir_boletim(driver)
        notas_atuais = extrair_notas(driver)
    except Exception:
        # tira o print antes do finally fechar o navegador, e repassa o erro para cima
        salvar_screenshot(driver, "verificacao")
        raise
    finally:
        driver.quit()

    # se nenhuma disciplina foi lida, não salva: um estado vazio faria tudo parecer novo na próxima vez
    if not notas_atuais:
        print("Aviso: nenhuma disciplina foi lida no boletim. O estado não foi alterado.")
        return

    if notas_anteriores is None:
        salvar_estado(notas_atuais)
        print(f"Primeira execução: monitorando {len(notas_atuais)} disciplinas.")
        # avisa que o monitoramento começou (serve também para testar o Telegram)
        enviar_notificacao(f"✅ AlertaDeNotas ativado! Monitorando {len(notas_atuais)} disciplinas.")
        return

    mudancas = comparar_notas(notas_anteriores, notas_atuais)
    if not mudancas:
        print("Nenhuma mudança nas notas.")
        return

    mensagem = formatar_mensagem(mudancas)
    if mensagem:
        enviou = enviar_notificacao(mensagem)
        if not enviou:
            print("Falha ao enviar a notificação. Vou tentar de novo na próxima verificação.")
            return  # não salva: a mudança continua "nova" na próxima vez

    salvar_estado(notas_atuais)  # atualiza o estado para a próxima verificação

def main():
    """Fluxo principal: valida o .env e verifica as notas a cada INTERVALO_MINUTOS.
    Com o argumento --uma-vez, verifica só uma vez e encerra (para o GitHub Actions ou o Agendador de Tarefas)."""
    carregar_credenciais()  # se faltar algo no .env, o script para aqui

    # modo "uma vez": quem repete a cada 30 minutos é o GitHub Actions (ou o Agendador de Tarefas)
    if "--uma-vez" in sys.argv:
        verificar_notas()
        return

    # modo contínuo: o próprio script repete até você apertar Ctrl+C
    try:
        while True:
            print(f"\n--- Verificação às {datetime.now().strftime('%H:%M')} ---")
            try:
                verificar_notas()  # abre o portal, compara com o estado e avisa se mudou
            except Exception as erro:
                # um erro em uma verificação (portal fora do ar, internet caiu) não derruba o script
                resumo = str(erro).strip().splitlines()[0] if str(erro).strip() else ""  # só a 1ª linha: erros do Selenium são longos
                print(f"Erro nesta verificação ({type(erro).__name__}: {resumo}) Tento de novo na próxima.")

            proxima = datetime.now() + timedelta(minutes=INTERVALO_MINUTOS)
            print(f"Próxima verificação às {proxima.strftime('%H:%M')}. (Ctrl+C para encerrar)")
            time.sleep(INTERVALO_MINUTOS * 60)  # sleep recebe segundos
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado.")


if __name__ == "__main__":
    main()
