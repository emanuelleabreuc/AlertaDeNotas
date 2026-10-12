import os
import sys
import time

from dotenv import load_dotenv
from selenium import webdriver  # selenium automatiza ações em navegadores
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



load_dotenv() #le o arq .env


MATRICULA = os.getenv("MATRICULA")
SENHA = os.getenv("SENHA")


URL_PORTAL = "https://aluno.uvv.br/"
INTERVALO_MINUTOS = 30  # de quanto em quanto tempo checar 
TIMEOUT = 15
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
URL_BOLETIM = "https://aluno.uvv.br/Boletim/Aluno/UhiEEfaaP7U="  # URL do boletim



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

    # se faltou alguma variável, mostra quais são e encerra o script com código de erro
    if faltando:
        print(f"Erro: preencha no arquivo .env -> {', '.join(faltando)}")
        sys.exit(1)

    # tudo certo: confirma o carregamento (mostra só o tamanho da senha, nunca a senha em si)
    print("Variáveis carregadas com sucesso.")
    print(f"Matrícula: {MATRICULA}")
    print(f"Tamanho da senha: {len(SENHA)} caracteres")


def iniciar_navegador(): 
    """Inicia o navegador e abre a página do portal."""
    driver = webdriver.Chrome() #faz o driver do navegador abrir o chrome
    driver.maximize_window() #maximiza a janela do navegador
    return driver #mostra o driver para ser usado em outras funções

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
    print(colunas)
    print(len(colunas)) # imprime o número de colunas

    linhas = driver.find_elements(*SELETOR_LINHAS_NOTAS)  # localiza as linhas da tabela
    for linha in linhas:
        disciplina = linha.find_element(*SELETOR_DISCIPLINA).text.strip()  # singular: cada linha tem uma só disciplina
        valores = [td.text for td in linha.find_elements(*SELETOR_CELULAS)]
        print(disciplina, len(valores))  # imprime a disciplina e os valores das notas
     
def main():
    """Fluxo principal: valida o .env, abre o navegador, faz login e abre o boletim."""
    carregar_credenciais()
    driver = iniciar_navegador()

    try:
        abrir_portal(driver)
        fazer_login(driver)
        abrir_boletim(driver)
        extrair_notas(driver)
        input("Pressione Enter para fechar o navegador...") #segura o navegador aberto
    finally:
        driver.quit() #fecha o navegador mesmo se der erro


if __name__ == "__main__":
    main()
