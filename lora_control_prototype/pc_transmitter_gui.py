import sys
import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QLabel, QMessageBox, QTextEdit)
from PyQt5.QtCore import QTimer
import serial
import serial.tools.list_ports

class LoraControllerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.equipamentoLigado = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Controlador Remoto OAS - LoRa')
        self.setGeometry(300, 300, 450, 400)

        self.layout = QVBoxLayout()

        # --- Parte Superior (Controles) ---
        top_layout = QVBoxLayout()
        self.label = QLabel('Selecione a Porta Serial (COM) do Módulo LoRa:')
        top_layout.addWidget(self.label)

        port_layout = QHBoxLayout()
        self.port_combo = QComboBox(self)
        self.refresh_button = QPushButton('Atualizar Portas')
        self.refresh_button.clicked.connect(self.populate_ports)
        port_layout.addWidget(self.port_combo, 1)
        port_layout.addWidget(self.refresh_button)
        top_layout.addLayout(port_layout)

        button_layout = QHBoxLayout()
        self.on_button = QPushButton('Ligar Equipamento')
        self.on_button.setStyleSheet("background-color: lightgreen")
        self.on_button.clicked.connect(lambda: self.send_command("liga"))
        button_layout.addWidget(self.on_button)

        self.off_button = QPushButton('Desligar Equipamento')
        self.off_button.setStyleSheet("background-color: #ff7f7f")
        self.off_button.clicked.connect(lambda: self.send_command("desliga"))
        button_layout.addWidget(self.off_button)
        top_layout.addLayout(button_layout)
        
        self.layout.addLayout(top_layout)

        # --- Console de Log ---
        log_label = QLabel("Log de Comunicação:")
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.layout.addWidget(log_label)
        self.layout.addWidget(self.log_console)

        self.setLayout(self.layout)
        self.populate_ports()
        self.log("Interface iniciada. Aguardando comando.")

    def log(self, message):
        """Adiciona uma mensagem com timestamp ao console de log."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_console.append(f"[{timestamp}] {message}")

    def populate_ports(self):
        """Busca e atualiza a lista de portas seriais disponíveis."""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.addItem("Nenhuma porta encontrada")
        else:
            for port in sorted(ports):
                self.port_combo.addItem(port.device)
        self.log("Lista de portas seriais atualizada.")

    def send_command(self, command_name):
        port_name = self.port_combo.currentText()
        if not port_name or "Nenhuma" in port_name:
            self.show_error("Nenhuma porta serial selecionada.")
            self.log("Erro: Nenhuma porta serial selecionada.")
            return

        command_char = 'L' if command_name == 'liga' else 'D'
        expected_ack = "ACK_LIGA" if command_name == 'liga' else "ACK_DESLIGA"

        self.log(f"Enviando (modo NORMAL): '{command_char}'")

        try:
            with serial.Serial(port_name, 9600, timeout=3) as ser:
                self.log(f"Porta {port_name} aberta com sucesso.")
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                self.log("Buffers da serial limpos.")

                ser.write(command_char.encode('utf-8'))
                self.log(f"Comando enviado: {repr(command_char.encode('utf-8'))}")

                self.log("Aguardando resposta do receptor (timeout=3s)...")
                response = ser.readline().decode('utf-8', errors='ignore').strip()

                if response:
                    self.log(f"Resposta recebida: '{response}'")
                    if response == expected_ack:
                        self.log("SUCESSO: Resposta ACK correta recebida!")
                        if command_name == 'liga':
                            self.equipamentoLigado = True
                        else:
                            self.equipamentoLigado = False
                    else:
                        self.log(f"FALHA: Resposta inesperada. Esperado: '{expected_ack}'.")
                else:
                    self.log("FALHA: Timeout! Nenhuma resposta recebida do receptor.")

        except serial.SerialException as e:
            error_msg = f"Erro ao comunicar com a porta {port_name}:\n{e}"
            self.show_error(error_msg)
            self.log(f"ERRO CRÍTICO de Serial: {e}")
        except Exception as e:
            error_msg = f"Ocorreu um erro inesperado:\n{e}"
            self.show_error(error_msg)
            self.log(f"ERRO INESPERADO: {e}")

    def show_error(self, message):
        """Exibe uma caixa de diálogo de erro."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Erro")
        msg.setInformativeText(message)
        msg.setWindowTitle("Erro de Comunicação")
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LoraControllerGUI()
    ex.show()
    sys.exit(app.exec_()) 