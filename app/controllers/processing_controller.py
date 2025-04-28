"""
Módulo controlador para processamento de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import numpy as np

from app.models.processing import SignalProcessor
from app.models.data_store import DataStore
from app.utils.debug_log import log_debug, log_info, log_warning, log_error
from typing import Dict, List, Tuple, Any, Optional

class ProcessingController(QObject):
    """Controlador para processamento de dados"""
    
    # Sinais
    demodulationStarted = pyqtSignal()
    demodulationFinished = pyqtSignal(dict)
    demodulationError = pyqtSignal(str)
    processingProgress = pyqtSignal(str)
    movingAverageApplied = pyqtSignal(dict)  # Novo sinal específico para média móvel
    
    def __init__(self, parent=None):
        """
        Inicializa o controlador de processamento
        
        Args:
            parent: Objeto pai
        """
        super().__init__(parent)
        self.data = None
        self.demodulated_data = None
        self.use_moving_average = False
        self.moving_average_window = 11
        self.processed_waveforms = None
        
    def set_data(self, data: Dict[str, Any]):
        """
        Define os dados a serem processados
        
        Args:
            data: Dicionário com os dados a processar
        """
        self.data = data
        self.processed_waveforms = None
        
        # Se já existirem dados demodulados, usar eles
        if 'demodulated' in data:
            self.demodulated_data = data
        else:
            self.demodulated_data = None
        
        # Processar os dados de acordo com as configurações atuais
        if self.use_moving_average and 'waveforms' in self.data:
            self.apply_moving_average()
    
    def set_moving_average(self, enabled: bool, window_size: int):
        """
        Define as configurações de média móvel
        
        Args:
            enabled: Se a média móvel deve ser aplicada
            window_size: Tamanho da janela de média móvel
        """
        # Verificar se houve alteração na configuração
        if self.use_moving_average == enabled and self.moving_average_window == window_size:
            log_debug(f"set_moving_average: Configuração não alterada, ignorando...")
            return
            
        log_info(f"set_moving_average: {'Aplicando' if enabled else 'Desativando'} média móvel (janela={window_size})")
        self.processingProgress.emit(f"{'Aplicando' if enabled else 'Desativando'} média móvel...")
        
        # Atualizar configurações
        self.use_moving_average = enabled
        self.moving_average_window = window_size
        
        # Processar os dados de acordo com as novas configurações
        if self.data is not None and 'waveforms' in self.data:
            log_debug(f"Aplicando média móvel aos dados (shape={self.data['waveforms'].shape})")
            self.apply_moving_average()
            
            # Emitir sinal com os dados atualizados
            if self.processed_waveforms is not None:
                # Criar um dicionário com os dados processados
                processed_data = self.data.copy()
                processed_data['waveforms'] = self.processed_waveforms
                
                # Emitir o sinal específico para média móvel
                log_debug(f"Emitindo sinal movingAverageApplied (shape={processed_data['waveforms'].shape})")
                self.movingAverageApplied.emit(processed_data)
                
                # Se também temos dados demodulados, precisamos reprocessar
                if self.demodulated_data is not None:
                    log_debug("Reprocessando dados demodulados com a nova média móvel")
                    self.demodulate_data()
    
    def apply_moving_average(self):
        """
        Aplica média móvel nos dados brutos
        
        Returns:
            Array com as formas de onda processadas
        """
        if not self.data or 'waveforms' not in self.data:
            log_warning("apply_moving_average: Sem dados para processar")
            return None
            
        waveforms = self.data['waveforms']
        
        if self.use_moving_average:
            log_info(f"Aplicando média móvel (janela={self.moving_average_window})...")
            self.processingProgress.emit(f"Aplicando média móvel (janela={self.moving_average_window})...")
            try:
                self.processed_waveforms = SignalProcessor.apply_moving_average(
                    waveforms, 
                    self.moving_average_window
                )
                log_info("Média móvel aplicada com sucesso")
                self.processingProgress.emit("Média móvel aplicada com sucesso")
            except Exception as e:
                log_error(f"Erro ao aplicar média móvel: {str(e)}")
                self.processingProgress.emit(f"Erro ao aplicar média móvel: {str(e)}")
                self.processed_waveforms = waveforms
        else:
            # Se a média móvel não está ativada, usar os dados originais
            log_debug("Usando dados originais (média móvel desativada)")
            self.processed_waveforms = waveforms
        
        return self.processed_waveforms
    
    def get_waveforms_for_processing(self):
        """
        Retorna as formas de onda a serem usadas para processamento
        
        Returns:
            Array de formas de onda processadas ou originais
        """
        if self.processed_waveforms is not None:
            return self.processed_waveforms
            
        if not self.data or 'waveforms' not in self.data:
            log_warning("get_waveforms_for_processing: Sem dados disponíveis")
            return None
            
        if self.use_moving_average:
            return self.apply_moving_average()
        
        return self.data['waveforms']
    
    @pyqtSlot()
    def demodulate_data(self):
        """Demodula os dados carregados"""
        if not self.data or 'waveforms' not in self.data:
            log_warning("demodulate_data: Nenhum dado carregado para demodular")
            self.demodulationError.emit("Nenhum dado carregado para demodular")
            return
            
        # Verificar se o processamento está disponível
        if not SignalProcessor.is_available():
            log_error("demodulate_data: Módulos de processamento não disponíveis")
            self.demodulationError.emit("Módulos de processamento não disponíveis")
            return
            
        try:
            self.demodulationStarted.emit()
            log_info("Iniciando demodulação...")
            self.processingProgress.emit("Iniciando demodulação...")
            
            # Obter as formas de onda processadas
            waveforms = self.get_waveforms_for_processing()
            log_debug(f"Demodulando forma de onda com shape={waveforms.shape}")
            
            # Verificar se temos dois canais
            if waveforms.shape[0] < 2:
                log_error("demodulate_data: Necessários dois canais para demodulação")
                self.demodulationError.emit("Necessários dois canais para demodulação")
                return
                
            # Realizar ajuste da elipse
            log_info("Ajustando elipse...")
            self.processingProgress.emit("Ajustando elipse...")
            ellipse_params = SignalProcessor.fit_ellipse(waveforms)
            log_debug(f"Elipse ajustada com parâmetros: {ellipse_params}")
            
            # Demodular o sinal
            log_info("Demodulando sinal...")
            self.processingProgress.emit("Demodulando sinal...")
            demodulated = SignalProcessor.demodulate(waveforms, ellipse_params)
            log_debug(f"Sinal demodulado (length={len(demodulated)})")
            
            # Adicionar dados demodulados aos dados existentes
            self.demodulated_data = self.data.copy()
            self.demodulated_data['waveforms'] = waveforms  # Usar as formas de onda processadas
            self.demodulated_data['demodulated'] = demodulated
            self.demodulated_data['ellipse_params'] = ellipse_params
            
            log_info("Demodulação concluída")
            self.processingProgress.emit("Demodulação concluída")
            self.demodulationFinished.emit(self.demodulated_data)
            
        except Exception as e:
            log_error(f"Erro na demodulação: {str(e)}")
            self.demodulationError.emit(f"Erro na demodulação: {str(e)}")
            
    def save_demodulated_data(self) -> str:
        """
        Salva os dados demodulados
        
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        if not self.demodulated_data:
            log_error("save_demodulated_data: Nenhum dado demodulado disponível para salvar")
            raise ValueError("Nenhum dado demodulado disponível para salvar")
            
        log_info("Salvando dados demodulados...")
        filename = DataStore.save_demodulated_data(self.demodulated_data)
        log_info(f"Dados demodulados salvos em: {filename}")
        return filename
    
    def calculate_spectrum(self) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]]]:
        """
        Calcula o espectro do sinal demodulado
        
        Returns:
            Tupla (frequências, magnitudes_dB, picos detectados)
        """
        if not self.demodulated_data or 'demodulated' not in self.demodulated_data:
            log_error("calculate_spectrum: Nenhum dado demodulado disponível para análise espectral")
            raise ValueError("Nenhum dado demodulado disponível para análise espectral")
            
        # Obter sinal demodulado e taxa de amostragem
        demodulated = self.demodulated_data['demodulated']
        
        # Determinar taxa de amostragem
        if 'sample_frequency' in self.demodulated_data and 'decimation' in self.demodulated_data:
            fs = self.demodulated_data['sample_frequency'] / self.demodulated_data['decimation']
        elif 'sample_frequency_effective' in self.demodulated_data:
            fs = self.demodulated_data['sample_frequency_effective']
        elif 't' in self.demodulated_data and len(self.demodulated_data['t']) >= 2:
            t = self.demodulated_data['t']
            fs = 1 / (t[1] - t[0])
        else:
            fs = 1.953125e6  # valor padrão (125MHz/64)
            
        log_debug(f"Calculando espectro (fs={fs} Hz, length={len(demodulated)})")
        
        # Calcular espectro
        freq_axis, magnitudes_db = SignalProcessor.calculate_spectrum(demodulated, fs)
        
        # Encontrar picos principais
        peaks = SignalProcessor.find_peaks(magnitudes_db, freq_axis)
        log_debug(f"Encontrados {len(peaks)} picos principais no espectro")
        
        return freq_axis, magnitudes_db, peaks
        
    def auto_demodulate(self, data: Dict[str, Any]) -> bool:
        """
        Realiza demodulação automática após a aquisição
        
        Args:
            data: Dados adquiridos
            
        Returns:
            True se a demodulação foi bem-sucedida, False caso contrário
        """
        log_info("Iniciando demodulação automática")
        self.set_data(data)
        
        try:
            self.demodulate_data()
            return True
        except Exception as e:
            log_error(f"Erro na demodulação automática: {str(e)}")
            self.demodulationError.emit(f"Erro na demodulação automática: {str(e)}")
            return False 