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
DISCIPLINA = "Programação Orientada a Objetos II"  
INTERVALO_MINUTOS = 30  # de quanto em quanto tempo checar 
TIMEOUT = 15
TIMEOUT_LOGIN = 20
SELETOR_CAMPO_MATRICULA = (By.ID, "Matricula")
SELETOR_CAMPO_SENHA = (By.ID, "Password")
SELETOR_BOTAO_ENTRAR = (By.CSS_SELECTOR, "button.portal-login-submit") 
SELETOR_LOGADO = (By.CSS_SELECTOR, ".fa-sign-out")  # ícone de logout, que só aparece quando logado
SELETOR_ERRO_LOGIN = (By.CSS_SELECTOR, ".portal-login-feedback.portal-login-feedback-danger")  # mensagem de erro de login


def carregar_credenciais():
    """Confere se as variáveis do .env foram preenchidas. Para o script se faltar algo."""
    faltando = [] #guarda as variáveis que não foram preenchidas
    if not MATRICULA or MATRICULA.startswith("coloque_"):
        faltando.append("MATRICULA")
    if not SENHA or SENHA.startswith("coloque_"):
        faltando.append("SENHA")

    if faltando:
        print(f"Erro: preencha no arquivo .env -> {', '.join(faltando)}")
        sys.exit(1)

    
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
    driver.get(URL_PORTAL)

    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located(SELETOR_CAMPO_MATRICULA)
        )
    except TimeoutException:
        print(
            "Erro: o campo de matrícula não apareceu. Confira o seletor, "
            "se existe iframe ou se a página carregou."
        )
        raise
 
    print("Portal carregado com sucesso.")


def fazer_login(driver):
    """Preenche matrícula e senha, clica em Entrar e confere se o login deu certo."""
    campo_matricula = driver.find_element(*SELETOR_CAMPO_MATRICULA)
    campo_matricula.clear() #limpa o campo caso já tenha algo escrito
    campo_matricula.send_keys(MATRICULA) #digita a matrícula

    campo_senha = driver.find_element(*SELETOR_CAMPO_SENHA)
    campo_senha.clear()
    campo_senha.send_keys(SENHA) #digita a senha

    WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable(SELETOR_BOTAO_ENTRAR)
    ).click() #espera o botão poder ser clicado e clica

    # espera aparecer o ícone de logout (deu certo) OU a mensagem de erro (deu errado)
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

    erros = driver.find_elements(*SELETOR_ERRO_LOGIN)
    if erros and erros[0].is_displayed():
        print(f"Erro no login: {erros[0].text.strip()}")
        raise RuntimeError("Login recusado pelo portal.")

    print("Login realizado com sucesso.")


def main():
    carregar_credenciais()

    driver = iniciar_navegador()
    try:
        abrir_portal(driver)
        fazer_login(driver)
        input("Pressione Enter para fechar o navegador...") #segura o navegador aberto
    finally:
        driver.quit() #fecha o navegador mesmo se der erro


if __name__ == "__main__":
    main()
