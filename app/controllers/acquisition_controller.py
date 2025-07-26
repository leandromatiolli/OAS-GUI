"""
Módulo controlador para aquisição de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import os
from app.models.data_store import DataStore
from typing import Dict, Any, Optional
from OAS_Acquire_Continuous import SCPI_Server, connect_scpi, bring_up_scpi_server, acquire_data, ping_scpi_server, setup_continuous_acquisition, wait_acquisition, get_data_continuous, tear_down
import numpy as np
from datetime import datetime

import traceback

class AcquisitionThread(QThread):
    """Thread para aquisição de dados sem congelar a interface"""
    finished = pyqtSignal(str)  # Sinal emitido quando a aquisição termina
    progress = pyqtSignal(str)   # Sinal para atualizar o status
    data_acquired = pyqtSignal(dict)       # Sinal de dados adquiridos
    error = pyqtSignal(str)      # Sinal para reportar erros

    def __init__(self, 
                 ip, 
                 duration, 
                 sample_rate, 
                 decimation, 
                 channels, 
                 is_series=False
                 ):
        """
        Inicializa a thread de aquisição
        
        Args:
            ip: Endereço IP do Red Pitaya
            duration: Duração da aquisição em segundos
            sample_rate: Taxa de amostragem em Hz
            decimation: Fator de decimação
            channels: Lista de canais para adquirir (1 ou 2)
        """
        super().__init__()
        self.ip = ip
        self.duration = duration
        self.sample_rate = sample_rate
        self.decimation = decimation
        self.channels = channels
        self.is_series = is_series  # Flag para indicar se é uma série de aquisições
        self.timedout = False  # Flag para indicar se houve timeout na aquisição
        self.scpi_server = SCPI_Server(ip)
        self.dig = connect_scpi(ip)

    def run(self):
        """Executa a aquisição em thread separada"""
        self.progress.emit("Iniciando aquisição...")
        i = 0
        while True:
            # Verifica se a thread foi interrompida
            if self.isInterruptionRequested():
                self.finished.emit("interrupted")
                tear_down(self.dig)
                return

            if self.timedout:
                print("Checando conexão...")
                self.error.emit("Timeout na aquisição. Tentando reconectar...")
                try:
                    response = self.scpi_server.status()
                    if response == "active":
                        print("servidor HTTP respondeu")
                        print("Flushing the dig buffer")
                        #dig.check_error()
                        self.dig.tx_txt('SYST:ERR:COUN?') 
                        n = self.dig.flush()
                        print(f"Flushed {n} bytes do buffer")
                        
                        #print(self.dig._socket.recv(1024))
                        # n = int(self.dig.err_c())
                        # print(f"Numero Erro encontrado: {n}")
                        # for i in range(n):
                        #     print(f"Erro {i}: {self.dig.err_n()}")
                        self.timedout = False
                    else:
                        continue  # Se o servidor não está ativo, continua tentando
                except Exception as e:
                    # if isinstance(e, TimeoutError):
                    #     self.timedout = True
                    #print(f"Erro ao verificar status do servidor: {e}")
                    traceback.print_exc()
                    continue
                
            # Tenta adquirir os dados
            try:
                self.progress.emit(f"Adquirindo dados {i:4d}")
                i += 1

                # Adquirir dados usando o cliente RedPitaya
                # data = acquire_data(
                #     self.ip, 
                #     self.duration,
                #     self.sample_rate,
                #     self.decimation,
                #     self.channels,
                # )
                effective_sample_rate = self.sample_rate / self.decimation
                # Calcular tamanho total (ou próximo possível) baseado na memória do RedPitaya
                waveform_len = int(effective_sample_rate * self.duration)
                
                # Ajustar para potência de 2 (mais eficiente)
                power_of_2 = int(np.log2(waveform_len))
                waveform_len = 2 ** min(power_of_2, 25)  # Limite de 2^25 (33.5M pontos)
                
                # Recalcular a duração real
                actual_duration = waveform_len / effective_sample_rate
                
                print(f"Iniciando aquisição contínua:")
                print(f"- Duração solicitada: {self.duration}s")
                print(f"- Duração real: {actual_duration:.2f}s")
                print(f"- Tamanho da forma de onda: {waveform_len:_} pontos")
                print(f"- Taxa de amostragem efetiva: {effective_sample_rate/1e6:.2f} MHz")
                print(f"- Fator de decimação: {self.decimation}")

                # Configurar a aquisição
                setup_continuous_acquisition(self.dig, decimation=self.decimation,
                                                    waveform_len=waveform_len, ch=self.channels)

                # Criar um buffer para armazenar os dados
                n_ch = len(self.channels)
                waveforms = np.zeros((n_ch, waveform_len), dtype=np.int16)
                
                # Iniciar a aquisição
                print("Iniciando aquisição...")
                self.dig.tx_txt('ACQ:START')
                self.dig.tx_txt('ACQ:TRIG NOW')

                # Aguardar a conclusão da aquisição
                wait_acquisition(self.dig)

                # Obter os dados
                get_data_continuous(self.dig, waveforms, ch=self.channels)

                # Criar objeto de dados
                data = {
                    'waveforms': waveforms,
                    'sample_frequency': self.sample_rate,
                    'decimation': self.decimation,
                    'sample_frequency_effective': effective_sample_rate,
                    'acquisition_time': actual_duration,
                    'channels': self.channels,
                    't': np.arange(waveform_len) / effective_sample_rate,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }


                # Emitir sinal com os dados
                self.data_acquired.emit(data)

                
            except Exception as e:
                #print(traceback.format_exc())
                if isinstance(e, TimeoutError):
                    self.timedout = True
                    print(f"{str(e)}")
                # else:
                #     self.error.emit(f"AcquisitionThread:run: {str(e)}")

                

class AcquisitionController(QObject):
    """Controlador para aquisição de dados"""
    
    # Sinais
    acquisitionStarted = pyqtSignal()
    acquisitionFinished = pyqtSignal(str)
    acquisitionProgress = pyqtSignal(str)
    acquisitionDataAcquired = pyqtSignal(dict)
    acquisitionError = pyqtSignal(str)
    calibrationFinished = pyqtSignal(dict)  # Sinal específico para calibração concluída
    sensorConnected = pyqtSignal(bool, str, str)  # Sinal para status de conexão do sensor (connected, ip, error_message)
    
    def __init__(self, parent=None):
        """
        Inicializa o controlador de aquisição
        
        Args:
            parent: Objeto pai
        """
        super().__init__(parent)
        self.acquisition_thread = None
        self.scpi_server = SCPI_Server()
        
    @pyqtSlot(dict)
    def start_acquisition(self, params: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Inicia uma aquisição com os parâmetros especificados
        
        Args:
            params: Dicionário com os parâmetros de aquisição
            metadata: Metadados opcionais para incluir nos dados
        """
            
        # Verificar se já existe uma aquisição em andamento
        if self.acquisition_thread and self.acquisition_thread.isRunning():
            self.acquisitionError.emit("Uma aquisição já está em andamento")
            return
        
        # Verificar se é uma aquisição para calibração
        self.is_calibration = params.get('is_calibration', False)
        self.calibration_file = params.get('calibration_file')
        
        # Verificar se temos dois canais para calibração
        if self.is_calibration and len(params['channels']) < 2:
            self.acquisitionError.emit("A calibração requer ambos os canais (1 e 2)")
            return
            
        if self.scpi_server.status() != "active":
            self.acquisitionError.emit("Servidor SCPI não está ativo. Conecte ao sensor primeiro.")
            return
        # Criar e iniciar thread de aquisição
        self.acquisition_thread = AcquisitionThread(
            params['ip'], 
            params['duration'], 
            params['sample_rate'], 
            params['decimation'], 
            params['channels'],
            params['is_series']
        )
        
        # Conectar sinais
        self.acquisition_thread.progress.connect(self.handle_progress)
        self.acquisition_thread.data_acquired.connect(self.handle_data_acquired)
        self.acquisition_thread.error.connect(self.handle_error)
        self.acquisition_thread.finished.connect(self.handle_finished)
        
        # Iniciar a thread
        self.acquisition_thread.start()
        self.acquisitionStarted.emit()
        
    @pyqtSlot(str)
    def handle_progress(self, message):
        """
        Manipula as mensagens de progresso da aquisição
        
        Args:
            message: Mensagem de progresso (str) ou dados adquiridos (dict)
        """
        if isinstance(message, str):
            self.acquisitionProgress.emit(message)
        elif isinstance(message, dict):
            self.acquisitionNewData.emit(message)
        
    @pyqtSlot(str)
    def handle_error(self, message: str):
        """
        Manipula erros da aquisição
        
        Args:
            message: Mensagem de erro
        """
        self.acquisitionError.emit(message)
        
    @pyqtSlot(str)
    def handle_finished(self, message: str):
        """
        Manipula a conclusão da aquisição
        
        Args:
            data: Dados adquiridos
        """
        # # Verificar se é uma aquisição de calibração
        # if data.get('is_calibration', False):
        #     # Emitir sinal específico para calibração concluída
        #     self.calibrationFinished.emit(data)
        # else:
        #     # Emitir sinal normal para aquisição concluída
        self.acquisitionFinished.emit("finished")
    
    @pyqtSlot(dict)
    def handle_data_acquired(self, data: Dict[str, Any]):
        """
        Manipula a dados adquiridos
        
        Args:
            data: Dados adquiridos
        """
        data['is_calibration'] = self.is_calibration
        data['calibration_file'] = self.calibration_file
        self.acquisitionDataAcquired.emit(data)

    @pyqtSlot(str)
    def connect_to_sensor(self, ip: str):
        """
        Conecta ao sensor Red Pitaya
        
        Args:
            ip: Endereço IP do sensor
        """
        try:
            # Tentar estabelecer conexão com o servidor SCPI
            self.scpi_server.set_ip(ip)
            response = self.scpi_server.start()
            self.sensorConnected.emit(True, ip, response)
        except Exception as e:
            error_message = f"Falha na conexão: {str(e)}"
            self.sensorConnected.emit(False, ip, error_message)

    def stop_acquisition(self):
        """
        Para a aquisição em andamento solicitando interrupção da thread
        """
        if self.acquisition_thread and self.acquisition_thread.isRunning():
            self.acquisition_thread.requestInterruption()
