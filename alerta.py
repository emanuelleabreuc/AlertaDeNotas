from selenium import webdriver #selenium automatiza ações em navegadores
from selenium.webdriver.common.by import By
import time

#id textbox matricula= "Matricula" e depois digitar a matricula
#id textbox senha= "Password" e depois digitar a senha
#class botao entrar= "btn col-lg-12 btn-primary input-block-level portal-login-submit"
#url da pagina= "https://aluno.uvv.br/"
#ao logar, url muda pra= "https://aluno.uvv.br/Aluno/MinhasTurmas"
#aba boletins <a href="/Boletim/Aluno/UhiEEfaaP7U=" title="Boletins"><i class="fa fa-list-alt"></i> Boletins</a>
#nao abre nova aba/janela, apenas muda a url da pagina atual
#nao aparece nenhum aviso/popup
#nao demora pra carregar
#elemento q só existe logado(sair)=" fa fa-sign-out"
#nao tem iframe na tela de login, ja com o partal aberto o iframe é: <iframe id="_hjSafeContext_8125640" title="_hjSafeContext" tabindex="-1" aria-hidden="true" src="about:blank" style="display: none !important; width: 1px !important; height: 1px !important; opacity: 0 !important; pointer-events: none !important;"></iframe>



