"""
Módulo controlador para aquisição de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import os

from app.models.hardware.redpitaya_client import RedPitayaClient
from app.models.data_store import DataStore
from typing import Dict, Any, Optional
from OAS_Acquire_Continuous import bring_up_scpi_server

class AcquisitionThread(QThread):
    """Thread para aquisição de dados sem congelar a interface"""
    finished = pyqtSignal(dict)  # Sinal emitido quando a aquisição termina
    progress = pyqtSignal(str)   # Sinal para atualizar o status
    error = pyqtSignal(str)      # Sinal para reportar erros

    def __init__(self, ip, duration, sample_rate, decimation, channels, is_calibration=False, calibration_file=None, metadata=None):
        """
        Inicializa a thread de aquisição
        
        Args:
            ip: Endereço IP do Red Pitaya
            duration: Duração da aquisição em segundos
            sample_rate: Taxa de amostragem em Hz
            decimation: Fator de decimação
            channels: Lista de canais para adquirir (1 ou 2)
            is_calibration: Se é uma aquisição para calibração
            calibration_file: Nome do arquivo de calibração a ser usado ou salvo
            metadata: Metadados opcionais para incluir nos dados
        """
        super().__init__()
        self.ip = ip
        self.duration = duration
        self.sample_rate = sample_rate
        self.decimation = decimation
        self.channels = channels
        self.is_calibration = is_calibration
        self.calibration_file = calibration_file
        self.metadata = metadata or {}

    def run(self):
        """Executa a aquisição em thread separada"""
        try:
            self.progress.emit("Iniciando aquisição...")
            
            # Atualizar metadados com flag de calibração
            updated_metadata = self.metadata.copy()
            updated_metadata['is_calibration'] = self.is_calibration
            if self.calibration_file:
                updated_metadata['calibration_file'] = self.calibration_file
            
            # Adquirir dados usando o cliente RedPitaya
            data = RedPitayaClient.acquire_data(
                self.ip, 
                duration=self.duration,
                sample_rate=self.sample_rate,
                decimation=self.decimation,
                channels=self.channels,
                metadata=updated_metadata
            )
            
            # Adicionar flag de calibração aos dados
            data['is_calibration'] = self.is_calibration
            if self.calibration_file:
                data['calibration_file'] = self.calibration_file
            
            # Se for calibração, salvar com o nome específico fornecido
            if self.is_calibration:
                self.progress.emit(f"Salvando dados de calibração como {self.calibration_file}...")
                prefix = os.path.splitext(self.calibration_file)[0] if self.calibration_file else "calibracao"
            else:
                self.progress.emit("Salvando dados...")
                prefix = "vazamento_continuo"
                
            # Salvar dados usando o DataStore
            save_directory = None
            if 'metadata' in data and isinstance(data['metadata'], dict):
                save_directory = data['metadata'].get('save_directory')
            filename = DataStore.save_data(data, prefix=prefix, directory=save_directory)
            self.progress.emit(f"Dados salvos em {filename}")
            
            # Emitir sinal de conclusão com os dados
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(f"Erro na aquisição: {str(e)}")

class AcquisitionController(QObject):
    """Controlador para aquisição de dados"""
    
    # Sinais
    acquisitionStarted = pyqtSignal()
    acquisitionFinished = pyqtSignal(dict)
    acquisitionProgress = pyqtSignal(str)
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
        
    @pyqtSlot(dict)
    def start_acquisition(self, params: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Inicia uma aquisição com os parâmetros especificados
        
        Args:
            params: Dicionário com os parâmetros de aquisição
            metadata: Metadados opcionais para incluir nos dados
        """
        # Verificar se a aquisição está disponível
        if not RedPitayaClient.is_available():
            self.acquisitionError.emit("Hardware não disponível")
            return
            
        # Verificar se já existe uma aquisição em andamento
        if self.acquisition_thread and self.acquisition_thread.isRunning():
            self.acquisitionError.emit("Uma aquisição já está em andamento")
            return
        
        # Verificar se é uma aquisição para calibração
        is_calibration = params.get('is_calibration', False)
        calibration_file = params.get('calibration_file')
        
        # Verificar se temos dois canais para calibração
        if is_calibration and len(params['channels']) < 2:
            self.acquisitionError.emit("A calibração requer ambos os canais (1 e 2)")
            return
            
        # Criar e iniciar thread de aquisição
        self.acquisition_thread = AcquisitionThread(
            params['ip'], 
            params['duration'], 
            params['sample_rate'], 
            params['decimation'], 
            params['channels'],
            is_calibration,
            calibration_file,
            metadata
        )
        
        # Conectar sinais
        self.acquisition_thread.progress.connect(self.handle_progress)
        self.acquisition_thread.error.connect(self.handle_error)
        self.acquisition_thread.finished.connect(self.handle_finished)
        
        # Iniciar a thread
        self.acquisition_thread.start()
        self.acquisitionStarted.emit()
        
    @pyqtSlot(str)
    def handle_progress(self, message: str):
        """
        Manipula as mensagens de progresso da aquisição
        
        Args:
            message: Mensagem de progresso
        """
        self.acquisitionProgress.emit(message)
        
    @pyqtSlot(str)
    def handle_error(self, message: str):
        """
        Manipula erros da aquisição
        
        Args:
            message: Mensagem de erro
        """
        self.acquisitionError.emit(message)
        
    @pyqtSlot(dict)
    def handle_finished(self, data: Dict[str, Any]):
        """
        Manipula a conclusão da aquisição
        
        Args:
            data: Dados adquiridos
        """
        # Verificar se é uma aquisição de calibração
        if data.get('is_calibration', False):
            # Emitir sinal específico para calibração concluída
            self.calibrationFinished.emit(data)
        else:
            # Emitir sinal normal para aquisição concluída
            self.acquisitionFinished.emit(data)
    
    @pyqtSlot(str)
    def connect_to_sensor(self, ip: str):
        """
        Conecta ao sensor Red Pitaya
        
        Args:
            ip: Endereço IP do sensor
        """
        try:
            # Tentar estabelecer conexão com o servidor SCPI
            bring_up_scpi_server(ip)
            self.sensorConnected.emit(True, ip, "")
        except Exception as e:
            error_message = f"Falha na conexão: {str(e)}"
            self.sensorConnected.emit(False, ip, error_message)
        