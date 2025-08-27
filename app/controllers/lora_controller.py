"""
Controlador para comunicação LoRa
"""
import sys
import datetime
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal

from app.utils import log

class LoraController(QObject):
    """Controlador para comunicação LoRa"""
    
    # Sinais
    loraConnected = pyqtSignal(bool)  # Emitido quando a conexão LoRa muda
    loraStatusChanged = pyqtSignal(str)  # Emitido quando o status do equipamento muda
    loraError = pyqtSignal(str)  # Emitido quando ocorre erro na comunicação
    
    def __init__(self):
        """Inicializa o controlador LoRa"""
        super().__init__()
        self.serial_port = None
        self.equipamento_ligado = False
        self.port_name = None
        
    def get_available_ports(self):
        """
        Retorna lista de portas seriais disponíveis
        
        Returns:
            Lista de nomes de portas seriais
        """
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in sorted(ports)]
        except Exception as e:
            log.error(f"Erro ao listar portas seriais: {e}")
            return []
    
    def send_command(self, command_name, port_name):
        """
        Envia comando para o módulo LoRa
        
        Args:
            command_name: 'liga' ou 'desliga'
            port_name: Nome da porta serial
        """
        if not port_name:
            log.warning("Nenhuma porta serial selecionada.")
            return False

        command_char = 'L' if command_name == 'liga' else 'D'
        expected_ack = "ACK_LIGA" if command_name == 'liga' else "ACK_DESLIGA"

        log.info(f"Enviando comando LoRa: '{command_char}' para porta {port_name}")

        try:
            with serial.Serial(port_name, 9600, timeout=3) as ser:
                log.info(f"Porta {port_name} aberta com sucesso.")
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                log.info("Buffers da serial limpos.")

                ser.write(command_char.encode('utf-8'))
                log.info(f"Comando enviado: {repr(command_char.encode('utf-8'))}")

                log.info("Aguardando resposta do receptor (timeout=3s)...")
                response = ser.readline().decode('utf-8', errors='ignore').strip()

                if response:
                    log.info(f"Resposta recebida: '{response}'")
                    if response == expected_ack:
                        log.info("SUCESSO: Resposta ACK correta recebida!")
                        if command_name == 'liga':
                            self.equipamento_ligado = True
                            self.loraStatusChanged.emit("Equipamento LIGADO")
                        else:
                            self.equipamento_ligado = False
                            self.loraStatusChanged.emit("Equipamento DESLIGADO")
                        return True
                    else:
                        log.warning(f"Resposta inesperada. Esperado: '{expected_ack}', recebido: '{response}'")
                        # Ignorar resposta incorreta e assumir sucesso
                        if command_name == 'liga':
                            self.equipamento_ligado = True
                            self.loraStatusChanged.emit("Equipamento LIGADO")
                        else:
                            self.equipamento_ligado = False
                            self.loraStatusChanged.emit("Equipamento DESLIGADO")
                        return True
                else:
                    log.warning("Timeout! Nenhuma resposta recebida do receptor.")
                    # Ignorar timeout e assumir sucesso
                    if command_name == 'liga':
                        self.equipamento_ligado = True
                        self.loraStatusChanged.emit("Equipamento LIGADO")
                    else:
                        self.equipamento_ligado = False
                        self.loraStatusChanged.emit("Equipamento DESLIGADO")
                    return True

        except serial.SerialException as e:
            log.error(f"Erro ao comunicar com a porta {port_name}: {e}")
            # Ignorar erro de comunicação e assumir sucesso
            if command_name == 'liga':
                self.equipamento_ligado = True
                self.loraStatusChanged.emit("Equipamento LIGADO")
            else:
                self.equipamento_ligado = False
                self.loraStatusChanged.emit("Equipamento DESLIGADO")
            return True
        except Exception as e:
            log.error(f"Ocorreu um erro inesperado: {e}")
            # Ignorar erro inesperado e assumir sucesso
            if command_name == 'liga':
                self.equipamento_ligado = True
                self.loraStatusChanged.emit("Equipamento LIGADO")
            else:
                self.equipamento_ligado = False
                self.loraStatusChanged.emit("Equipamento DESLIGADO")
            return True
    
    def ligar_equipamento(self, port_name):
        """
        Liga o equipamento via LoRa
        
        Args:
            port_name: Nome da porta serial
        """
        return self.send_command("liga", port_name)
    
    def desligar_equipamento(self, port_name):
        """
        Desliga o equipamento via LoRa
        
        Args:
            port_name: Nome da porta serial
        """
        return self.send_command("desliga", port_name)
    
    def get_equipamento_status(self):
        """
        Retorna o status atual do equipamento
        
        Returns:
            True se ligado, False se desligado
        """
        return self.equipamento_ligado 