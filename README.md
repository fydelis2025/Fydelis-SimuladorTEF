# 🚀 Simulador TEF Universal — Fydelis TEF

> Simulador de transações TEF multiplataforma via API Local HTTP/JSON. Funciona em Windows, Linux e macOS. Compatível com qualquer linguagem (Delphi, C#, Java, Python, VB, etc.).

---

## 📋 Sobre o Projeto

Em vez de usar DLLs específicas por sistema operacional, este simulador funciona como um **servidor HTTP local** que recebe requisições do PDV e exibe uma interface visual para você aprovar, negar ou cancelar transações em tempo real.

### ✅ Funcionalidades
- 🌐 API REST/JSON — funciona em qualquer SO e qualquer linguagem
- 🖥️ Interface gráfica simulando PinPad com botões visuais
- 💳 Suporte a Crédito, Débito e Pix
- 🏦 Seleção de bandeiras (Visa, Mastercard, Elo, Amex, Hipercard, Pix)
- ✅ Respostas com NSU, Código de Autorização, Status e Data/Hora
- ⏱️ Timeout de 2 minutos por transação

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Servidor API | FastAPI + Uvicorn |
| Interface Gráfica | PySide6 (Qt) |
| Comunicação | HTTP / JSON |
| Linguagem | Python 3.10+ |

---

## Exemplo de Requisição

Método: POST
URL: http://127.0.0.1:8080/tef/pagar
Content-Type: application/json
{
  "valor": 150.75,
  "tipo_pagamento": "credito",
  "bandeira": "Visa"
}

## Campos da Requisição

valor	Número-> Sim->Valor da transação (ex: 100.50)
tipo_pagamento->Texto-> Sim	credito, debito ou pix
bandeira	Texto	❌ Não	Visa, Mastercard, Elo, Amex, Hipercard, Pix

## Exemplo de Resposta — ✅ APROVADO
{
  "status": "APROVADO",
  "nsu": "5829471036",
  "codigo_autorizacao": "A728491",
  "bandeira": "Visa",
  "valor": 150.75,
  "data_hora": "16/08/2026 22:30:45",
  "mensagem": "Transação aprovada com sucesso"
}

## Exemplo de Resposta — NEGADO

{
  "status": "NEGADO",
  "nsu": "5829471037",
  "codigo_autorizacao": "000000",
  "bandeira": "Mastercard",
  "valor": 89.90,
  "data_hora": "16/08/2026 22:31:10",
  "mensagem": "Transação negada pelo operador"
}

## Exemplo de Resposta — CANCELADO

{
  "status": "CANCELADO",
  "nsu": "5829471038",
  "codigo_autorizacao": "000000",
  "bandeira": "Elo",
  "valor": 25.00,
  "data_hora": "16/08/2026 22:32:00",
  "mensagem": "Transação cancelada pelo operador"
}

## Exemplo de Resposta — TIMEOUT

{
  "detail": "Tempo esgotado — operação cancelada"
}

## Verificar Status — /tef/status

Método: GET
URL: http://127.0.0.1:8080/tef/status
Exemplo de Resposta
{
  "status": "online",
  "transacao_ativa": false
}

## 🚀 Instalação e Execução

### Linux / Debian / Ubuntu
```bash
# 1. Instala o suporte ao ambiente virtual
sudo apt install python3-venv -y

# 2. Cria e ativa o ambiente
python3 -m venv .venv
source .venv/bin/activate

# 3. Instala dependências
pip install -r requirements.txt

# 4. Executa
python simulador_tef.py
