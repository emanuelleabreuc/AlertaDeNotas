# AlertaDeNotas

Automação em Python que entra no Portal do Aluno da UVV, lê o boletim e avisa (no terminal ou no Telegram) quando sai uma nota nova, quando uma nota é corrigida ou quando o resultado de uma disciplina muda.

## Como funciona

```
┌─→ login no portal → abre o boletim → lê as notas → fecha o navegador
│      → compara com as notas da última vez (estado.json)
│      → mudou algo? → avisa (terminal / Telegram)
│      → salva as notas atuais em estado.json
└──── espera 30 minutos ────┘
```

- Na **primeira execução** o script só guarda as notas atuais e avisa que o monitoramento começou.
- Se o envio para o Telegram falhar, o estado **não** é salvo, e a novidade é enviada de novo na próxima verificação.
- Se algo der errado no portal, um print da tela é salvo na pasta do projeto (`erro_<data>_<hora>_verificacao.png`).

## Instalação

Precisa do Python 3 e do Google Chrome instalados.

```
git clone https://github.com/emanuelleabreuc/AlertaDeNotas.git
cd AlertaDeNotas
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Depois abra o `.env` e preencha `MATRICULA` e `SENHA`.

## Telegram (opcional)

Sem o Telegram, as novidades aparecem só no terminal.

1. No Telegram, abra o **@BotFather**, mande `/newbot` e siga as instruções. Ele responde com o **token** do bot.
2. Abra a conversa com o seu bot e mande qualquer mensagem (por exemplo, "oi").
3. No navegador, abra `https://api.telegram.org/bot<TOKEN>/getUpdates` (troque `<TOKEN>` pelo token) e procure `"chat":{"id": ...}`. Esse número é o seu **chat_id**.
4. Preencha no `.env`:
   ```
   TELEGRAM_TOKEN=o_token_do_bot
   TELEGRAM_CHAT_ID=o_seu_chat_id
   ```

O token funciona como uma senha: deixe-o só no `.env`. Se ele vazar, mande `/revoke` para o @BotFather e gere outro.

## Como rodar

**Modo contínuo** (verifica a cada 30 minutos até você apertar Ctrl+C):
```
.\.venv\Scripts\python.exe alerta.py
```

**Uma verificação só** (para usar com o Agendador de Tarefas):
```
.\.venv\Scripts\python.exe alerta.py --uma-vez
```

### Rodando sozinho pelo Agendador de Tarefas do Windows

1. Abra o **Agendador de Tarefas** → **Criar Tarefa**.
2. **Disparadores** → Novo → Diariamente, e marque **Repetir a tarefa a cada: 30 minutos**, por **Indefinidamente**.
3. **Ações** → Novo → Iniciar um programa:
   - **Programa/script:** o caminho completo do `python.exe` do ambiente virtual, por exemplo `C:\Users\voce\Desktop\alertaDeNotas\.venv\Scripts\python.exe`
   - **Argumentos:** `alerta.py --uma-vez`
   - **Iniciar em:** a pasta do projeto, por exemplo `C:\Users\voce\Desktop\alertaDeNotas`
4. Em **Condições**, desmarque "Iniciar a tarefa somente se o computador estiver ligado na energia" se usar notebook.

## Configurações (no topo do `alerta.py`)

| Constante | Para que serve |
|---|---|
| `INTERVALO_MINUTOS` | de quanto em quanto tempo verificar no modo contínuo |
| `HEADLESS` | `True` roda o Chrome sem janela; `False` mostra o navegador (útil para depurar) |
| `MEDIA` | nota mínima; notas de prova abaixo dela ganham o aviso ⚠️ |
| `COLUNAS_PROVA` | colunas comparadas com a `MEDIA` |
| `COLUNAS_IGNORADAS` | colunas que não entram na mensagem |

## Testes

Os testes não abrem o navegador nem acessam a internet:
```
.\.venv\Scripts\python.exe test_alerta.py
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `alerta.py` | o script |
| `test_alerta.py` | testes das funções |
| `.env` | suas credenciais (não vai para o GitHub) |
| `.env.example` | modelo do `.env` |
| `estado.json` | notas da última verificação (criado sozinho, não vai para o GitHub) |
| `requirements.txt` | bibliotecas usadas |
