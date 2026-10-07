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
SELETOR_CAMPO_MATRICULA = (By.ID, "Matricula")



def carregar_credenciais():
    """Confere se as variáveis do .env foram preenchidas. Para o script se faltar algo."""
    faltando = []
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
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver

def abrir_portal(driver):
    driver.get(URL_PORTAL)




def main():
    carregar_credenciais()
    


if __name__ == "__main__":
    main()


driver = webdriver.Chrome()
driver.get(URL_PORTAL)