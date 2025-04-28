"""
Módulo controlador para aquisição de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from app.models.hardware.redpitaya_client import RedPitayaClient
from app.models.data_store import DataStore
from typing import Dict, Any

class AcquisitionThread(QThread):
    """Thread para aquisição de dados sem congelar a interface"""
    finished = pyqtSignal(dict)  # Sinal emitido quando a aquisição termina
    progress = pyqtSignal(str)   # Sinal para atualizar o status
    error = pyqtSignal(str)      # Sinal para reportar erros

    def __init__(self, ip, duration, sample_rate, decimation, channels, metadata=None):
        """
        Inicializa a thread de aquisição
        
        Args:
            ip: Endereço IP do Red Pitaya
            duration: Duração da aquisição em segundos
            sample_rate: Taxa de amostragem em Hz
            decimation: Fator de decimação
            channels: Lista de canais para adquirir (1 ou 2)
            metadata: Metadados opcionais para incluir nos dados
        """
        super().__init__()
        self.ip = ip
        self.duration = duration
        self.sample_rate = sample_rate
        self.decimation = decimation
        self.channels = channels
        self.metadata = metadata or {}

    def run(self):
        """Executa a aquisição em thread separada"""
        try:
            self.progress.emit("Iniciando aquisição...")
            
            # Adquirir dados usando o cliente RedPitaya
            data = RedPitayaClient.acquire_data(
                self.ip, 
                duration=self.duration,
                sample_rate=self.sample_rate,
                decimation=self.decimation,
                channels=self.channels,
                metadata=self.metadata
            )
            
            self.progress.emit("Salvando dados...")
            
            # Salvar dados usando o DataStore
            filename = DataStore.save_data(data)
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
            
        # Criar e iniciar thread de aquisição
        self.acquisition_thread = AcquisitionThread(
            params['ip'], 
            params['duration'], 
            params['sample_rate'], 
            params['decimation'], 
            params['channels'],
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
        self.acquisitionFinished.emit(data) 