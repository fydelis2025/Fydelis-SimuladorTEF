import sys
import threading
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QComboBox,
                               QGroupBox, QTextEdit)
from PySide6.QtCore import Qt, QTimer, Signal, QObject

# ==================== CONFIGURAÇÕES ====================
HOST = "127.0.0.1"
PORTA = 8080

# ==================== MODELO DE DADOS ====================
class Transacao(BaseModel):
    valor: float
    tipo_pagamento: str  # credito, debito, pix
    bandeira: str | None = None

class RespostaTransacao(BaseModel):
    status: str
    nsu: str
    codigo_autorizacao: str
    bandeira: str
    valor: float
    data_hora: str
    mensagem: str

# ==================== SERVIDOR API FASTAPI ====================
app = FastAPI(title="Simulador TEF Universal")

# Estado compartilhado entre API e Interface
estado_simulador = {
    "transacao_ativa": None,
    "resposta_pronta": None,
    "bandeiras": ["Visa", "Mastercard", "Elo", "Amex", "Hipercard", "Pix"]
}

# Sinal para avisar a interface que chegou uma transação
class SinalTransacao(QObject):
    nova = Signal(object)

sinal_transacao = SinalTransacao()

@app.post("/tef/pagar", response_model=RespostaTransacao)
async def pagar(dados: Transacao):
    """Recebe a solicitação do PDV e aguarda a ação do operador na janela"""
    if estado_simulador["transacao_ativa"]:
        raise HTTPException(409, "Já existe transação em andamento")

    # Prepara transação
    transacao = {
        "id": str(uuid.uuid4())[:8],
        "valor": dados.valor,
        "tipo": dados.tipo_pagamento,
        "bandeira": dados.bandeira or "Não informada",
        "nsu": str(uuid.uuid4().int)[:10],
        "cod_autorizacao": "A" + str(uuid.uuid4().int)[:6],
        "hora_recebimento": datetime.now().strftime("%H:%M:%S")
    }

    estado_simulador["transacao_ativa"] = transacao
    estado_simulador["resposta_pronta"] = None

    # Avisa a interface para mostrar a transação
    sinal_transacao.nova.emit(transacao)

    # Aguarda até que o operador clique em Aprovar/Negar/Cancelar
    from time import sleep
    for _ in range(120):  # 2 minutos de timeout
        if estado_simulador["resposta_pronta"]:
            resp = estado_simulador["resposta_pronta"]
            estado_simulador["transacao_ativa"] = None
            estado_simulador["resposta_pronta"] = None
            return resp
        sleep(1)

    # Timeout
    estado_simulador["transacao_ativa"] = None
    raise HTTPException(408, "Tempo esgotado — operação cancelada")


@app.get("/tef/status")
async def status():
    """Verificar se o simulador está online"""
    return {"status": "online", "transacao_ativa": bool(estado_simulador["transacao_ativa"])}


# ==================== INTERFACE GRÁFICA (PySide6) ====================
class JanelaSimulador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador TEF Universal")
        self.setFixedSize(520, 420)

        # Conecta sinal da API
        sinal_transacao.nova.connect(self.mostrar_transacao)

        self._construir_interface()

    def _construir_interface(self):
        principal = QWidget()
        layout = QVBoxLayout(principal)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # --- Visor do Pinpad ---
        self.visor = QLabel("Aguardando transação...")
        self.visor.setStyleSheet("""
            QLabel {
                background-color: #001a00;
                color: #00ff00;
                font-family: Consolas, Monospace;
                font-size: 16px;
                padding: 20px;
                border-radius: 8px;
                min-height: 100px;
            }
        """)
        self.visor.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.visor)

        # --- Seletor de Bandeira ---
        grupo_bandeira = QGroupBox("Bandeira / Tipo")
        layout_bandeira = QHBoxLayout(grupo_bandeira)
        self.combo_bandeira = QComboBox()
        self.combo_bandeira.addItems(estado_simulador["bandeiras"])
        layout_bandeira.addWidget(self.combo_bandeira)
        layout.addWidget(grupo_bandeira)

        # --- Botões de Ação ---
        grupo_botoes = QGroupBox("Ações")
        layout_botoes = QHBoxLayout(grupo_botoes)

        self.btn_aprov = QPushButton("APROVAR")
        self.btn_aprov.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 6px;")
        self.btn_aprov.clicked.connect(lambda: self.responder("APROVADO"))

        self.btn_neg = QPushButton("NEGAR")
        self.btn_neg.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 6px;")
        self.btn_neg.clicked.connect(lambda: self.responder("NEGADO"))

        self.btn_canc = QPushButton("CANCELAR")
        self.btn_canc.setStyleSheet("background-color: #f1c40f; color: #222; font-weight: bold; padding: 15px; font-size: 14px; border-radius: 6px;")
        self.btn_canc.clicked.connect(lambda: self.responder("CANCELADO"))

        layout_botoes.addWidget(self.btn_aprov)
        layout_botoes.addWidget(self.btn_neg)
        layout_botoes.addWidget(self.btn_canc)
        layout.addWidget(grupo_botoes)

        # --- Log de Transações ---
        grupo_log = QGroupBox("Última Resposta")
        layout_log = QVBoxLayout(grupo_log)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        layout_log.addWidget(self.log)
        layout.addWidget(grupo_log)

        self.setCentralWidget(principal)
        self._botoes_habilitados(False)

    def _botoes_habilitados(self, sim: bool):
        self.btn_aprov.setEnabled(sim)
        self.btn_neg.setEnabled(sim)
        self.btn_canc.setEnabled(sim)

    def mostrar_transacao(self, trans):
        """Atualiza a interface quando chega uma transação do PDV"""
        self.transacao_atual = trans
        bandeira = trans["bandeira"]
        if bandeira != "Não informada":
            idx = self.combo_bandeira.findText(bandeira)
            if idx >= 0:
                self.combo_bandeira.setCurrentIndex(idx)

        self.visor.setText(
            f"VALOR: R$ {trans['valor']:.2f}\n"
            f"TIPO: {trans['tipo'].upper()}\n"
            f"BANDEIRA: {trans['bandeira']}\n"
            "CONFIRME A OPERAÇÃO"
        )
        self._botoes_habilitados(True)
        self.log.clear()

    def responder(self, status_final: str):
        """Envia a resposta de volta para a API → PDV"""
        if not hasattr(self, "transacao_atual") or not self.transacao_atual:
            return

        trans = self.transacao_atual
        bandeira_def = self.combo_bandeira.currentText()

        resposta = RespostaTransacao(
            status=status_final,
            nsu=trans["nsu"],
            codigo_autorizacao=trans["cod_autorizacao"] if status_final == "APROVADO" else "000000",
            bandeira=bandeira_def,
            valor=trans["valor"],
            data_hora=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            mensagem=f"Transação {status_final.lower()} com sucesso" if status_final == "APROVADO" else f"Transação {status_final.lower()} pelo operador"
        )

        # Devolve para a API
        estado_simulador["resposta_pronta"] = resposta

        # Atualiza tela
        cor = "#00ff00" if status_final == "APROVADO" else "#ff6666" if status_final == "NEGADO" else "#ffcc00"
        self.visor.setStyleSheet(f"QLabel {{ background-color: #001a00; color: {cor}; font-family: Consolas; font-size: 15px; padding: 20px; border-radius: 8px; min-height: 100px; }}")
        self.visor.setText(f"{status_final}!\nNSU: {trans['nsu']}\nAutorização: {resposta.codigo_autorizacao}")

        self.log.setText(
            f"Status: {resposta.status}\n"
            f"Valor: R$ {resposta.valor:.2f}\n"
            f"NSU: {resposta.nsu}\n"
            f"Autorização: {resposta.codigo_autorizacao}\n"
            f"Bandeira: {resposta.bandeira}\n"
            f"Data/Hora: {resposta.data_hora}"
        )

        self._botoes_habilitados(False)
        # Reseta visor depois de 5s
        QTimer.singleShot(5000, lambda: self.visor.setText("Aguardando transação..."))


# ==================== INICIAR TUDO ====================
def iniciar_servidor():
    uvicorn.run(app, host=HOST, port=PORTA, log_level="error")

if __name__ == "__main__":
    # Inicia servidor em segundo plano
    thread_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    thread_servidor.start()

    # Espera um pouquinho e abre interface
    QTimer.singleShot(800, lambda: print(f"Simulador TEF rodando em http://{HOST}:{PORTA}"))

    app = QApplication(sys.argv)
    janela = JanelaSimulador()
    janela.show()
    sys.exit(app.exec())
