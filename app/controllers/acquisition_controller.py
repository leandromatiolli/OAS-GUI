"""
Módulo controlador para aquisição de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import os

from app.models.hardware.redpitaya_client import RedPitayaClient
from app.models.data_store import DataStore
from app.utils.time_utils import get_formatted_internet_timestamp, get_brasilia_timestamp
from typing import Dict, Any, Optional

class AcquisitionThread(QThread):
    """Thread para aquisição de dados sem congelar a interface"""
    finished = pyqtSignal(dict)  # Sinal emitido quando a aquisição termina
    progress = pyqtSignal(str)   # Sinal para atualizar o status
    error = pyqtSignal(str)      # Sinal para reportar erros

    def __init__(self, ip, duration, sample_rate, decimation, channels, is_calibration=False, calibration_file=None, metadata=None, calibration_data=None):
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
        self.calibration_data = calibration_data

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
            
            # Se for calibração, calcular parâmetros da elipse e adicionar aos metadados
            if self.is_calibration:
                self.progress.emit("Calculando parâmetros da elipse...")
                try:
                    from app.models.processing import SignalProcessor
                    if 'waveforms' in data and data['waveforms'] is not None:
                        ellipse_params_raw = SignalProcessor.fit_ellipse(data['waveforms'])

                        # Converter para dicionário para melhor compatibilidade
                        ellipse_params_dict = {
                            'center_x': float(ellipse_params_raw[0]),
                            'center_y': float(ellipse_params_raw[1]),
                            'width': float(ellipse_params_raw[2]),
                            'height': float(ellipse_params_raw[3]),
                            'angle': float(ellipse_params_raw[4])
                        }

                        data['ellipse_params'] = ellipse_params_dict
                        # Adicionar aos metadados também
                        if 'metadata' not in data:
                            data['metadata'] = {}
                        data['metadata']['ellipse_params'] = ellipse_params_dict
                        data['metadata']['calibration_timestamp'] = get_brasilia_timestamp()
                        self.progress.emit("Parâmetros da elipse calculados com sucesso")
                except Exception as e:
                    self.progress.emit(f"Aviso: Erro ao calcular elipse: {str(e)}")
            
            # Se for calibração, salvar com o nome específico fornecido
            if self.is_calibration:
                self.progress.emit(f"Salvando dados de calibração como {self.calibration_file}...")
                prefix = os.path.splitext(self.calibration_file)[0] if self.calibration_file else "calibracao"
            else:
                self.progress.emit("Salvando dados...")
                # O prefixo será determinado automaticamente pelo tipo de teste nos metadados
                prefix = None
                
            # Salvar dados usando o DataStore
            save_directory = None
            if 'metadata' in data and isinstance(data['metadata'], dict):
                save_directory = data['metadata'].get('save_directory')
            
            filename = DataStore.save_data(data, prefix=prefix, directory=save_directory, calibration_data=self.calibration_data)
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
    automaticAcquisitionStarted = pyqtSignal(dict)  # Sinal para início de aquisições automáticas
    automaticAcquisitionFinished = pyqtSignal(dict)  # Sinal para fim de aquisições automáticas
    automaticAcquisitionProgress = pyqtSignal(int, int)  # Sinal para progresso (atual, total)
    
    def __init__(self, parent=None, processing_controller=None):
        """
        Inicializa o controlador de aquisição
        
        Args:
            parent: Objeto pai
            processing_controller: Referência ao controlador de processamento
        """
        super().__init__(parent)
        self.acquisition_thread = None
        self.processing_controller = processing_controller
        
        # Variáveis para aquisições automáticas
        self.is_automatic_acquisition_running = False
        self.automatic_acquisition_params = None
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = 0
        
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
        
        # Verificar se é uma aquisição automática
        is_automatic = params.get('is_automatic', False)
        if is_automatic:
            return self._start_automatic_acquisition(params, metadata)
        
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
            metadata,
            self.processing_controller.calibration_data if self.processing_controller else None
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
        # Verificar se é uma aquisição automática
        if self.is_automatic_acquisition_running:
            self._handle_automatic_acquisition_finished(data)
            return
        
        # Verificar se é uma aquisição de calibração
        if data.get('is_calibration', False):
            # Emitir sinal específico para calibração concluída
            self.calibrationFinished.emit(data)
        else:
            # Emitir sinal normal para aquisição concluída
            self.acquisitionFinished.emit(data)
    
    def _start_automatic_acquisition(self, params: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Inicia uma sequência de aquisições automáticas
        
        Args:
            params: Dicionário com os parâmetros de aquisição
            metadata: Metadados opcionais para incluir nos dados
        """
        if self.is_automatic_acquisition_running:
            self.acquisitionError.emit("Já existe uma sequência de aquisições automáticas em andamento")
            return
        
        # Configurar parâmetros das aquisições automáticas
        self.is_automatic_acquisition_running = True
        self.automatic_acquisition_params = params.copy()
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = params.get('num_acquisitions', 1)
        
        # Emitir sinal de início
        self.automaticAcquisitionStarted.emit(params)
        
        # Iniciar primeira aquisição
        self._execute_next_automatic_acquisition(metadata)
    
    def _execute_next_automatic_acquisition(self, metadata: Dict[str, Any] = None):
        """
        Executa a próxima aquisição na sequência automática
        
        Args:
            metadata: Metadados opcionais para incluir nos dados
        """
        if not self.is_automatic_acquisition_running:
            return
        
        # Incrementar contador
        self.automatic_acquisition_count += 1
        
        # Atualizar progresso
        self.automaticAcquisitionProgress.emit(self.automatic_acquisition_count, self.automatic_acquisition_total)
        
        # Criar parâmetros para aquisição individual (remover flags automáticas)
        individual_params = self.automatic_acquisition_params.copy()
        individual_params.pop('is_automatic', None)
        individual_params.pop('num_acquisitions', None)
        individual_params.pop('interval_seconds', None)
        
        # Criar e iniciar thread de aquisição
        self.acquisition_thread = AcquisitionThread(
            individual_params['ip'], 
            individual_params['duration'], 
            individual_params['sample_rate'], 
            individual_params['decimation'], 
            individual_params['channels'],
            individual_params.get('is_calibration', False),
            individual_params.get('calibration_file'),
            metadata,
            self.processing_controller.calibration_data if self.processing_controller else None
        )
        
        # Conectar sinais
        self.acquisition_thread.progress.connect(self.handle_progress)
        self.acquisition_thread.error.connect(self.handle_error)
        self.acquisition_thread.finished.connect(self.handle_finished)
        
        # Iniciar a thread
        self.acquisition_thread.start()
        self.acquisitionStarted.emit()
    
    def _handle_automatic_acquisition_finished(self, data: Dict[str, Any]):
        """
        Manipula a conclusão de uma aquisição individual na sequência automática
        
        Args:
            data: Dados adquiridos
        """
        # Emitir sinal de aquisição individual concluída
        self.acquisitionFinished.emit(data)
        
        # Verificar se é a última aquisição
        if self.automatic_acquisition_count >= self.automatic_acquisition_total:
            # Finalizar sequência automática
            self._finish_automatic_acquisition()
        else:
            # Programar próxima aquisição após o intervalo
            from PyQt5.QtCore import QTimer
            interval_ms = int(self.automatic_acquisition_params.get('interval_seconds', 10) * 1000)
            QTimer.singleShot(interval_ms, lambda: self._execute_next_automatic_acquisition(data.get('metadata')))
    
    def _finish_automatic_acquisition(self):
        """
        Finaliza a sequência de aquisições automáticas
        """
        self.is_automatic_acquisition_running = False
        self.automatic_acquisition_params = None
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = 0
        
        # Emitir sinal de conclusão
        self.automaticAcquisitionFinished.emit({'total_acquisitions': self.automatic_acquisition_total})
    
    def cancel_automatic_acquisition(self):
        """
        Cancela a sequência de aquisições automáticas em andamento
        """
        if not self.is_automatic_acquisition_running:
            return
        
        # Parar thread atual se estiver rodando
        if self.acquisition_thread and self.acquisition_thread.isRunning():
            self.acquisition_thread.terminate()
            self.acquisition_thread.wait()
        
        # Resetar estado
        self.is_automatic_acquisition_running = False
        self.automatic_acquisition_params = None
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = 0
        
        # Emitir sinal de cancelamento
        self.automaticAcquisitionFinished.emit({'cancelled': True}) 