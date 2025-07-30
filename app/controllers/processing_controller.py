"""
Módulo controlador para processamento de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import numpy as np
from scipy import signal

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
    bandpassFilterApplied = pyqtSignal(dict)  # Novo sinal para filtro passa-banda
    spectrogramGenerated = pyqtSignal(dict, object, object, object)  # Sinal emitido quando o espectrograma é gerado
    audioGenerated = pyqtSignal(str)  # Sinal emitido quando o arquivo de áudio é gerado
    plotCalibrationDataRequested = pyqtSignal(dict)  # Sinal para plotar dados de calibração
    
    def __init__(self, parent=None):
        """
        Inicializa o controlador de processamento
        
        Args:
            parent: Objeto pai
        """
        super().__init__(parent)
        self.data = None
        self.demodulated_data = None
        self.filtered_data = None
        self.calibration_data = None
        
        # Configuração da média móvel
        self.use_moving_average = False
        self.moving_average_window = 11
        self.processed_waveforms = None
        
        # Configuração do filtro passa-banda
        self.use_bandpass_filter = False
        self.bandpass_low_freq = 50.0    # Hz
        self.bandpass_high_freq = 5000.0  # Hz
        self.bandpass_order = 4
        self.filtered_demodulated = None
        
    def set_data(self, data: Dict[str, Any]):
        """
        Define os dados a serem processados
        
        Args:
            data: Dicionário com os dados a processar
        """
        log_debug(f"set_data: Recebendo novos dados para processamento")
        log_debug(f"set_data: Chaves disponíveis nos dados: {list(data.keys())}")
        
        self.data = data
        self.processed_waveforms = None
        self.filtered_demodulated = None
        
        # Resetar configurações de filtro para novos dados
        if not data.get('bandpass_params', {}).get('enabled', False):
            log_debug("set_data: Resetando configurações de filtro passa-banda para novos dados")
            self.use_bandpass_filter = False
            
        # Se já existirem dados demodulados, usar eles
        if 'demodulated' in data:
            log_info(f"set_data: Dados demodulados encontrados! Configurando self.demodulated_data")
            self.demodulated_data = data
            
            # Se o arquivo carregado contém parâmetros de filtro, usar eles
            if 'bandpass_params' in data and isinstance(data['bandpass_params'], dict):
                log_debug(f"set_data: Usando parâmetros de filtro do arquivo: {data['bandpass_params']}")
                params = data['bandpass_params']
                self.use_bandpass_filter = params.get('enabled', False)
                self.bandpass_low_freq = params.get('low_freq', self.bandpass_low_freq)
                self.bandpass_high_freq = params.get('high_freq', self.bandpass_high_freq)
                self.bandpass_order = params.get('order', self.bandpass_order)
        else:
            log_warning("set_data: Nenhum dado demodulado encontrado nos dados carregados")
            self.demodulated_data = None
        
        # Processar os dados de acordo com as configurações atuais
        if self.use_moving_average and 'waveforms' in self.data:
            self.apply_moving_average()
            
        # Aplicar filtro passa-banda se os dados demodulados existirem
        if self.use_bandpass_filter and self.demodulated_data is not None and 'demodulated' in self.demodulated_data:
            self.apply_bandpass_filter()
    
    def set_calibration_data(self, calibration_data: Optional[Dict[str, Any]]):
        """
        Define os dados de calibração para uso no processamento
        
        Args:
            calibration_data: Dicionário com os dados de calibração
        """
        log_debug(f"set_calibration_data: {'Definindo' if calibration_data else 'Limpando'} dados de calibração")
        self.calibration_data = calibration_data
        self.process_calibration_data()
        self.plotCalibrationDataRequested.emit(self.calibration_data)
        self.demodulate_data()

    def set_loaded_data_as_calibration(self):
        """
        Define os dados carregados como calibração atual
        """
        if self.data is None:
            log_warning("set_loaded_data_as_calibration: Nenhum dado carregado para definir como calibração")
            return
            
        log_info("set_loaded_data_as_calibration: Definindo dados carregados como calibração")
        self.set_calibration_data(self.data)
        
    def has_calibration_data(self) -> bool:
        """
        Verifica se há dados de calibração disponíveis
        
        Returns:
            True se há dados de calibração, False caso contrário
        """
        return (self.calibration_data is not None and 
                'ellipse_params' in self.calibration_data and 
                self.calibration_data['ellipse_params'] is not None)
    
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
    
    def set_bandpass_filter(self, enabled: bool, low_freq: float, high_freq: float, order: int):
        """
        Define as configurações do filtro passa-banda
        
        Args:
            enabled: Se o filtro deve ser aplicado
            low_freq: Frequência de corte inferior em Hz
            high_freq: Frequência de corte superior em Hz
            order: Ordem do filtro
        """
        log_debug(f"set_bandpass_filter: enabled={enabled}, low_freq={low_freq}, high_freq={high_freq}, order={order}")
        
        # Força aplicação mesmo sem mudanças nos parâmetros se estamos desabilitando o filtro
        force_update = (self.use_bandpass_filter == True and enabled == False)
        
        # Verificar se houve alteração na configuração
        if not force_update and (self.use_bandpass_filter == enabled and 
            self.bandpass_low_freq == low_freq and 
            self.bandpass_high_freq == high_freq and 
            self.bandpass_order == order):
            log_debug("set_bandpass_filter: Configuração não alterada, ignorando...")
            return
            
        log_info(f"set_bandpass_filter: {'Aplicando' if enabled else 'Desativando'} filtro passa-banda "
                f"({low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order})")
        
        self.processingProgress.emit(f"{'Aplicando' if enabled else 'Desativando'} filtro passa-banda...")
        
        # Atualizar configurações
        self.use_bandpass_filter = enabled
        self.bandpass_low_freq = low_freq
        self.bandpass_high_freq = high_freq
        self.bandpass_order = order
        
        # Aplicar filtro se temos dados demodulados
        if self.demodulated_data is not None and 'demodulated' in self.demodulated_data:
            log_debug("set_bandpass_filter: Aplicando filtro aos dados demodulados")
            self.apply_bandpass_filter()
        else:
            log_warning("set_bandpass_filter: Sem dados demodulados para aplicar o filtro")
            self.filtered_demodulated = None
            self.processingProgress.emit("Demodule os dados primeiro antes de aplicar o filtro passa-banda")
    
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
    
    def apply_bandpass_filter(self):
        """
        Aplica o filtro passa-banda ao sinal demodulado
        
        Returns:
            Array com o sinal demodulado filtrado
        """
        if not self.demodulated_data or 'demodulated' not in self.demodulated_data:
            log_warning("apply_bandpass_filter: Sem dados demodulados para filtrar")
            self.processingProgress.emit("Sem dados demodulados para filtrar")
            return None
            
        demodulated = self.demodulated_data['demodulated']
        log_debug(f"apply_bandpass_filter: Processando sinal demodulado com {len(demodulated)} pontos (enabled={self.use_bandpass_filter})")
        
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
    
        
        if self.use_bandpass_filter:
            log_info(f"Aplicando filtro passa-banda ({self.bandpass_low_freq:.1f}Hz-{self.bandpass_high_freq:.1f}Hz, ordem {self.bandpass_order})...")
            self.processingProgress.emit(f"Aplicando filtro passa-banda...")
            
            try:
                self.filtered_demodulated = SignalProcessor.apply_bandpass_filter(
                    demodulated,
                    fs,
                    self.bandpass_low_freq,
                    self.bandpass_high_freq,
                    self.bandpass_order
                )
                               
                log_info("Filtro passa-banda aplicado com sucesso")
                self.processingProgress.emit("Filtro passa-banda aplicado com sucesso")
                
                # Atualizar o dicionário com os dados filtrados
                self.demodulated_data['filtered_demodulated'] = self.filtered_demodulated
                self.demodulated_data['bandpass_params'] = {
                    'enabled': self.use_bandpass_filter,
                    'low_freq': self.bandpass_low_freq,
                    'high_freq': self.bandpass_high_freq,
                    'order': self.bandpass_order
                }
                
                self.bandpassFilterApplied.emit(self.demodulated_data)
                
            except Exception as e:
                log_error(f"Erro ao aplicar filtro passa-banda: {str(e)}")
                self.processingProgress.emit(f"Erro ao aplicar filtro passa-banda: {str(e)}")
                self.filtered_demodulated = None
        else:
            # Se o filtro está desativado, criar estrutura de dados consistente
            self.filtered_demodulated = None
            
            if 'filtered_demodulated' in self.demodulated_data:
                # Manter o sinal filtrado nos dados, mas marcar como desativado
                self.demodulated_data['bandpass_params'] = {
                    'enabled': False,
                    'low_freq': self.bandpass_low_freq,
                    'high_freq': self.bandpass_high_freq,
                    'order': self.bandpass_order
                }
            else:
                # Se não tinha filtro antes, adicionar parâmetros básicos
                self.demodulated_data['bandpass_params'] = {
                    'enabled': False,
                    'low_freq': self.bandpass_low_freq,
                    'high_freq': self.bandpass_high_freq,
                    'order': self.bandpass_order
                }
                
            # Emitir sinal para atualizar a interface
            log_debug("Emitindo sinal bandpassFilterApplied (filtro desativado)")
            self.bandpassFilterApplied.emit(self.demodulated_data)
            
        return self.filtered_demodulated
    
    def get_waveforms_for_processing(self):
        """
        Obtém as formas de onda processadas para análise
        
        Returns:
            Array com as formas de onda processadas (com média móvel se ativada)
        """
        if self.processed_waveforms is not None:
            return self.processed_waveforms
            
        if self.data is not None and 'waveforms' in self.data:
            # Se a média móvel está ativada, aplicá-la
            if self.use_moving_average:
                return self.apply_moving_average()
            # Caso contrário, usar os dados originais
            return self.data['waveforms']
            
        return None
    
    def get_demodulated_for_processing(self):
        """
        Obtém o sinal demodulado processado para análise
        
        Returns:
            Array com o sinal demodulado (filtrado se o filtro estiver ativado)
        """
        if self.demodulated_data is None or 'demodulated' not in self.demodulated_data:
            return None
            
        # Se o filtro passa-banda está ativado, usar o sinal filtrado
        if self.use_bandpass_filter and 'filtered_demodulated' in self.demodulated_data:
            return self.demodulated_data['filtered_demodulated']
            
        # Caso contrário, usar o sinal demodulado original
        return self.demodulated_data['demodulated']
        
    @pyqtSlot()
    def demodulate_data(self):
        """Demodula os dados atuais, usando calibração se disponível"""
        if self.data is None:
            log_warning("demodulate_data: Sem dados para demodular")
            self.demodulationError.emit("Sem dados para demodular")
            return
            
        # Verificar se temos os dados necessários
        if 'waveforms' not in self.data or self.data['waveforms'] is None:
            log_warning("demodulate_data: Sem formas de onda para demodular")
            self.demodulationError.emit("Sem formas de onda para demodular")
            return
            
        log_info("Iniciando demodulação...")
        self.demodulationStarted.emit()
        self.processingProgress.emit("Iniciando demodulação...")
        
        try:
            # Obter as formas de onda processadas
            waveforms = self.get_waveforms_for_processing()
            
            # Verificar se temos dados suficientes para demodulação
            if waveforms is None or waveforms.shape[0] < 2:
                log_warning("demodulate_data: Dados insuficientes para demodulação (precisamos de 2 canais)")
                self.demodulationError.emit("Dados insuficientes para demodulação (precisamos de 2 canais)")
                return
                
            # Determinar taxa de amostragem
            if 'sample_frequency' in self.data and 'decimation' in self.data:
                fs = self.data['sample_frequency'] / self.data['decimation']
            elif 'sample_frequency_effective' in self.data:
                fs = self.data['sample_frequency_effective']
            else:
                fs = 1.953125e6  # valor padrão (125MHz/64)
                
            log_debug(f"demodulate_data: Taxa de amostragem: {fs} Hz")
            
            # Determinar se usamos parâmetros de elipse da calibração ou calculamos novos
            ellipse_params = None
            
            # Verificar se temos dados de calibração disponíveis
            if self.has_calibration_data():
                log_debug("demodulate_data: Usando parâmetros de elipse da calibração")
                ellipse_params = self.calibration_data['ellipse_params']
            elif 'ellipse_params' in self.data and self.data['ellipse_params'] is not None:
                log_debug("demodulate_data: Usando parâmetros de elipse existentes nos dados")
                ellipse_params = self.data['ellipse_params']
            else:
                log_debug("demodulate_data: Calculando novos parâmetros de elipse")
                # Calcular parâmetros da elipse a partir dos dados
                ellipse_params = SignalProcessor.fit_ellipse(waveforms)
            
            # Demodular os dados usando os parâmetros da elipse
            log_debug("demodulate_data: Demodulando o sinal usando os parâmetros da elipse")
            demodulated = SignalProcessor.demodulate(waveforms, ellipse_params)
            
            # Criar um dicionário com os dados demodulados
            if self.data.get('t') is not None:
                t = self.data['t']
            else:
                # Criar vetor de tempo baseado na taxa de amostragem
                num_samples = waveforms.shape[1]
                t = np.arange(num_samples) / fs
                
            # Criar estrutura de dados demodulados
            self.demodulated_data = {
                'demodulated': demodulated,
                't': t,
                'waveforms': waveforms,
                'sample_frequency': self.data.get('sample_frequency'),
                'decimation': self.data.get('decimation'),
                'sample_frequency_effective': fs,
                'channels': self.data.get('channels', [1, 2]),
                'ellipse_params': ellipse_params,
                'metadata': self.data.get('metadata', {}),
                'bandpass_params': {
                    'enabled': False,
                    'low_freq': self.bandpass_low_freq,
                    'high_freq': self.bandpass_high_freq,
                    'order': self.bandpass_order
                }
            }
            
            # Aplicar filtro passa-banda se ativado
            if self.use_bandpass_filter:
                log_debug("demodulate_data: Aplicando filtro passa-banda após demodulação")
                self.apply_bandpass_filter()
                
            # Emitir sinal com os dados demodulados
            self.demodulationFinished.emit(self.demodulated_data)
            self.processingProgress.emit("Demodulação concluída com sucesso")
            
        except Exception as e:
            log_error(f"Erro na demodulação: {str(e)}")
            self.demodulationError.emit(f"Erro na demodulação: {str(e)}")
    
    def save_demodulated_data(self) -> str:
        """
        Salva os dados demodulados em arquivo
        
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        if self.demodulated_data is None:
            raise ValueError("Sem dados demodulados para salvar")
            
        return DataStore.save_demodulated_data(self.demodulated_data)
    
    def calculate_spectrum(self, use_filtered: bool = False) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]]]:
        """
        Calcula o espectro do sinal demodulado
        
        Args:
            use_filtered: Se deve usar o sinal filtrado para o cálculo
            
        Returns:
            Tupla com eixo de frequências, amplitudes e lista de picos
        """
        if self.demodulated_data is None:
            log_warning("calculate_spectrum: Sem dados demodulados")
            return np.array([]), np.array([]), []
            
        if use_filtered and 'filtered_demodulated' in self.demodulated_data:
            signal = self.demodulated_data['filtered_demodulated']
        elif 'demodulated' in self.demodulated_data:
            signal = self.demodulated_data['demodulated']
        else:
            log_warning("calculate_spectrum: Sem sinal demodulado")
            return np.array([]), np.array([]), []
            
        if 'sample_frequency_effective' in self.demodulated_data:
            fs = self.demodulated_data['sample_frequency_effective']
        elif 't' in self.demodulated_data and len(self.demodulated_data['t']) >= 2:
            t = self.demodulated_data['t']
            fs = 1 / (t[1] - t[0])
        else:
            fs = 1.953125e6  # valor padrão (125MHz/64)
            
        # Calcular espectro
        log_debug(f"calculate_spectrum: Calculando espectro (fs={fs} Hz, {'filtrado' if use_filtered else 'original'})")
        try:
            freq_axis, magnitudes_db = SignalProcessor.calculate_spectrum(signal, fs)
            
            # Encontrar picos principais
            peaks = SignalProcessor.find_peaks(magnitudes_db, freq_axis)
            
            return freq_axis, magnitudes_db, peaks
        except Exception as e:
            log_error(f"Erro ao calcular espectro: {str(e)}")
            return np.array([]), np.array([]), []
    
    def process_calibration_data(self) -> bool:
        """
        Processa dados de calibração e salva os parâmetros da elipse
        
        Args:
            data: Dados de calibração a serem processados
            
        Returns:
            True se a calibração foi bem-sucedida, False caso contrário
        """
        data = self.calibration_data
        if data is None or 'waveforms' not in data or data['waveforms'] is None:
            log_warning("process_calibration_data: Dados de calibração inválidos")
            return False
        waveforms = data['waveforms']

            
        try:
            log_info("Processando dados de calibração...")
            
            # Determinar taxa de amostragem
            if 'sample_frequency' in data and 'decimation' in data:
                fs = data['sample_frequency'] / data['decimation']
            elif 'sample_frequency_effective' in data:
                fs = data['sample_frequency_effective']
            else:
                fs = 1.953125e6  # valor padrão (125MHz/64)
            
            # Aplicar média móvel se configurada
            if self.use_moving_average:
                log_debug("process_calibration_data: Aplicando média móvel aos dados de calibração")
                processed_waveforms = SignalProcessor.apply_moving_average(
                    waveforms, 
                    self.moving_average_window
                )
            else:
                processed_waveforms = waveforms
                
            # Calcular parâmetros da elipse
            log_debug("process_calibration_data: Calculando parâmetros da elipse")
            ellipse_params = SignalProcessor.fit_ellipse(processed_waveforms)
            
            if ellipse_params is None:
                log_warning("process_calibration_data: Não foi possível calcular os parâmetros da elipse")
                return False
                
            # Criar dados de calibração
            calibration_data = {
                'ellipse_params': ellipse_params,
                'sample_frequency_effective': fs,
                'moving_average': {
                    'enabled': self.use_moving_average,
                    'window_size': self.moving_average_window
                },
            }
            
            # Armazenar dados de calibração para uso futuro
            self.calibration_data.update(calibration_data)
            
            log_info("Calibração concluída com sucesso")
            return True
            
        except Exception as e:
            log_error(f"Erro ao processar calibração: {str(e)}")
            return False
    
    def auto_demodulate(self, data: Dict[str, Any]) -> bool:
        """
        Realiza demodulação automática em dados recém-adquiridos
        
        Args:
            data: Dados a serem demodulados
            
        Returns:
            True se a demodulação foi bem-sucedida, False caso contrário
        """
        try:
            # Verificar se é um conjunto de dados de calibração
            if data.get('is_calibration', False):
                log_info("auto_demodulate: Processando como dados de calibração")
                return self.process_calibration_data(data)
                
            # Configurar os dados para processamento
            self.set_data(data)
            
            # Executar a demodulação
            self.demodulate_data()
            
            return self.demodulated_data is not None
        except Exception as e:
            log_error(f"Erro na demodulação automática: {str(e)}")
            return False
    
    @pyqtSlot(bool, int, float, float)
    def generate_spectrogram(self, enabled, window_size, overlap, max_freq):
        """
        Gera o espectrograma do sinal
        
        Args:
            enabled: Se o espectrograma está habilitado
            window_size: Tamanho da janela para o STFT (Short-Time Fourier Transform)
            overlap: Porcentagem de sobreposição entre janelas consecutivas (0.0 a 0.99)
            max_freq: Frequência máxima a ser exibida no espectrograma
            
        Returns:
            Um dicionário com os parâmetros e o resultado do espectrograma
        """
        log_debug(f"generate_spectrogram: window_size={window_size}, overlap={overlap:.2f}, max_freq={max_freq}")
        
        if not enabled:
            log_info("Espectrograma desabilitado")
            return
            
        # Verificar se temos dados válidos
        if not self.data or 't' not in self.data:
            log_warning("generate_spectrogram: Sem dados para gerar espectrograma")
            self.processingProgress.emit("Sem dados para gerar espectrograma")
            return
            
        # Determinar taxa de amostragem
        if 'sample_frequency' in self.data and 'decimation' in self.data:
            fs = self.data['sample_frequency'] / self.data['decimation']
        elif 'sample_frequency_effective' in self.data:
            fs = self.data['sample_frequency_effective']
        elif len(self.data['t']) >= 2:
            fs = 1 / (self.data['t'][1] - self.data['t'][0])
        else:
            fs = 1.953125e6  # valor padrão (125MHz/64)
            
        log_debug(f"generate_spectrogram: Taxa de amostragem: {fs} Hz")
        
        # Selecionar o sinal a ser usado para o espectrograma
        if self.use_bandpass_filter and 'filtered_demodulated' in self.data:
            log_debug("generate_spectrogram: Usando sinal filtrado para o espectrograma")
            signal_data = self.data['filtered_demodulated']
        elif 'demodulated' in self.data:
            log_debug("generate_spectrogram: Usando sinal demodulado para o espectrograma")
            signal_data = self.data['demodulated']
        elif 'waveforms' in self.data and self.data['waveforms'].shape[0] > 0:
            log_debug("generate_spectrogram: Usando primeiro canal de dados brutos para o espectrograma")
            signal_data = self.data['waveforms'][0]
        else:
            log_warning("generate_spectrogram: Não há sinal adequado para gerar o espectrograma")
            self.processingProgress.emit("Não há sinal adequado para gerar o espectrograma")
            return
            
        try:
            # Calcular o tamanho do passo (nperseg - noverlap)
            noverlap = int(window_size * overlap)
            
            # Calcular o espectrograma usando STFT
            log_debug(f"generate_spectrogram: Calculando espectrograma (fs={fs}, nperseg={window_size}, noverlap={noverlap})")
            self.processingProgress.emit("Calculando espectrograma...")
            
            # Limitar a frequência máxima, se especificado
            if max_freq > 0 and max_freq < fs/2:
                freqs_limit = int(max_freq * window_size / fs) + 1
            else:
                freqs_limit = None
            
            # Calcular o espectrograma
            f, t, Sxx = signal.spectrogram(
                signal_data, 
                fs=fs, 
                window='hann',
                nperseg=window_size, 
                noverlap=noverlap, 
                scaling='density'
            )
            
            # Limitar a frequência máxima para exibição
            if freqs_limit:
                f = f[:freqs_limit]
                Sxx = Sxx[:freqs_limit, :]
                
            log_debug(f"generate_spectrogram: Espectrograma calculado com sucesso (shape={Sxx.shape})")
            
            # Preparar parâmetros para retorno
            params = {
                'window_size': window_size,
                'overlap': overlap,
                'max_freq': max_freq,
                'fs': fs
            }
            
            # Salvar os resultados no objeto de dados
            self.data['spectrogram_t'] = t
            self.data['spectrogram_f'] = f
            self.data['spectrogram_Sxx'] = Sxx
            self.data['spectrogram_params'] = params
            
            # Emitir sinal com os resultados
            log_info("Espectrograma gerado com sucesso")
            self.processingProgress.emit("Espectrograma gerado com sucesso")
            # Emitir sinal com os arrays NumPy diretamente
            self.spectrogramGenerated.emit(self.data, t, f, Sxx)
            
            return self.data
            
        except Exception as e:
            log_error(f"Erro ao gerar espectrograma: {str(e)}")
            self.processingProgress.emit(f"Erro ao gerar espectrograma: {str(e)}")
            return None

    def diagnose_data_state(self):
        """
        Diagnostica o estado atual dos dados para debugging
        """
        log_info("=== DIAGNÓSTICO DO ESTADO DOS DADOS ===")
        
        # Verificar self.data
        if self.data:
            log_info(f"self.data presente com {len(self.data)} chaves")
            log_info(f"  Chaves em self.data: {list(self.data.keys())}")
            if 'demodulated' in self.data:
                log_info(f"  'demodulated' encontrado em self.data (tamanho: {len(self.data['demodulated'])})")
            else:
                log_warning("  'demodulated' NÃO encontrado em self.data")
        else:
            log_warning("self.data é None")
        
        # Verificar self.demodulated_data
        if self.demodulated_data:
            log_info(f"self.demodulated_data presente com {len(self.demodulated_data)} chaves")
            log_info(f"  Chaves em self.demodulated_data: {list(self.demodulated_data.keys())}")
            if 'demodulated' in self.demodulated_data:
                log_info(f"  'demodulated' encontrado em self.demodulated_data (tamanho: {len(self.demodulated_data['demodulated'])})")
            else:
                log_warning("  'demodulated' NÃO encontrado em self.demodulated_data")
        else:
            log_warning("self.demodulated_data é None")
        
        # Verificar se são o mesmo objeto
        if self.data and self.demodulated_data:
            log_info(f"self.data is self.demodulated_data: {self.data is self.demodulated_data}")
        
        log_info("=== FIM DO DIAGNÓSTICO ===")

    @pyqtSlot()
    def generate_audio_wav(self):
        """
        Gera arquivo de áudio WAV a partir do sinal demodulado
        
        Returns:
            str: Caminho do arquivo WAV gerado, ou None se houve erro
        """
        log_info("Iniciando geração de arquivo de áudio WAV")
        
        # Fazer diagnóstico completo do estado dos dados
        self.diagnose_data_state()
        
        # Debug: verificar estado atual dos dados
        log_debug(f"generate_audio_wav: self.demodulated_data={'presente' if self.demodulated_data else 'None'}")
        log_debug(f"generate_audio_wav: self.data={'presente' if self.data else 'None'}")
        
        if self.demodulated_data:
            log_debug(f"generate_audio_wav: Chaves em self.demodulated_data: {list(self.demodulated_data.keys())}")
        if self.data:
            log_debug(f"generate_audio_wav: Chaves em self.data: {list(self.data.keys())}")
        
        # Verificar se temos dados demodulados em qualquer um dos locais
        data_source = None
        if self.demodulated_data and 'demodulated' in self.demodulated_data:
            data_source = self.demodulated_data
            log_info("generate_audio_wav: Usando dados de self.demodulated_data")
        elif self.data and 'demodulated' in self.data:
            data_source = self.data
            log_info("generate_audio_wav: Usando dados de self.data")
        else:
            log_warning("generate_audio_wav: Sem dados demodulados para gerar áudio")
            log_warning(f"generate_audio_wav: DEBUG - self.demodulated_data has 'demodulated': {self.demodulated_data and 'demodulated' in self.demodulated_data if self.demodulated_data else 'N/A'}")
            log_warning(f"generate_audio_wav: DEBUG - self.data has 'demodulated': {self.data and 'demodulated' in self.data if self.data else 'N/A'}")
            self.processingProgress.emit("Sem dados demodulados para gerar áudio. Demodule os dados primeiro.")
            return None
            
        try:
            # Importar bibliotecas necessárias
            import os
            import math
            from scipy import signal
            from scipy.io import wavfile
            
            self.processingProgress.emit("Processando sinal para áudio...")
            
            # Obter dados do sinal demodulado
            signal_in = np.asarray(data_source['demodulated'], dtype=np.float64)
            
            # Determinar taxa de amostragem original
            if 'sample_frequency_effective' in data_source:
                fs_orig = float(data_source['sample_frequency_effective'])
            elif 'sample_frequency' in data_source and 'decimation' in data_source:
                fs_orig = float(data_source['sample_frequency']) / float(data_source['decimation'])
            else:
                log_warning("generate_audio_wav: Não foi possível determinar a taxa de amostragem original, usando padrão")
                fs_orig = 1.953125e6  # valor padrão (125MHz/64)
                
            log_debug(f"generate_audio_wav: Taxa de amostragem original: {fs_orig} Hz")
            
            # Parâmetros de conversão (baseados no convert_to_wav_gui.py)
            target_rate = 44100  # Hz
            hp_cutoff = 20.0     # Hz
            lp_cutoff = 20000.0  # Hz
            
            # Filtro passa-alta (20 Hz) – Butterworth de 4ª ordem
            log_debug("generate_audio_wav: Aplicando filtro passa-alta")
            sos = signal.butter(N=4, Wn=hp_cutoff, btype="highpass", fs=fs_orig, output="sos")
            signal_hp = signal.sosfiltfilt(sos, signal_in)
            
            # Filtro passa-baixa (20 kHz) – Butterworth de 4ª ordem
            log_debug("generate_audio_wav: Aplicando filtro passa-baixa")
            sos = signal.butter(N=4, Wn=lp_cutoff, btype="lowpass", fs=fs_orig, output="sos")
            signal_lp = signal.sosfiltfilt(sos, signal_hp)
            
            # Reamostragem para target_rate
            log_debug("generate_audio_wav: Reamostrando sinal")
            self.processingProgress.emit("Reamostrando sinal para taxa de áudio...")
            
            # Calcular fatores inteiros up/down para resample_poly
            fs_orig_int = int(round(fs_orig))  # garantir inteiro
            if fs_orig_int == 0:
                raise ValueError("Taxa de amostragem original inválida (0 Hz)")
                
            g = math.gcd(target_rate, fs_orig_int)
            up = target_rate // g
            down = fs_orig_int // g
            
            # Se ainda estiverem muito grandes, limitar valores mantendo a razão
            max_factor = 1000  # limite arbitrário para evitar coeficientes enormes
            while down > max_factor:
                up = (up + 1) // 2
                down = (down + 1) // 2
                
            log_debug(f"generate_audio_wav: Fatores de reamostragem: up={up}, down={down}")
            signal_resampled = signal.resample_poly(signal_lp, up, down)
            
            # Normalização para [-1, 1]
            log_debug("generate_audio_wav: Normalizando sinal")
            max_abs = np.max(np.abs(signal_resampled))
            if max_abs == 0:
                norm_signal = signal_resampled
            else:
                norm_signal = signal_resampled / max_abs
                
            # Converter para int16
            pcm16 = np.int16(norm_signal * 32767)
            
            # Determinar nome do arquivo
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Tentar usar metadados para nome do arquivo
            metadata = data_source.get('metadata', {})
            if metadata and 'timestamp' in metadata:
                timestamp = metadata['timestamp']
                base_name = f"demodulado_{timestamp}"
            else:
                # Usar timestamp atual se não tiver metadados
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"demodulado_{timestamp}"
                
            wav_name = f"{base_name}_audio.wav"
            wav_path = os.path.join(root_dir, wav_name)
            
            # Salvar arquivo WAV
            log_debug(f"generate_audio_wav: Salvando em {wav_path}")
            self.processingProgress.emit("Salvando arquivo WAV...")
            wavfile.write(wav_path, target_rate, pcm16)
            
            log_info(f"Arquivo de áudio WAV gerado com sucesso: {wav_path}")
            self.processingProgress.emit(f"Arquivo WAV salvo: {os.path.basename(wav_path)}")
            
            # Emitir sinal de conclusão
            self.audioGenerated.emit(wav_path)
            
            return wav_path
            
        except Exception as e:
            log_error(f"Erro ao gerar arquivo de áudio: {str(e)}")
            self.processingProgress.emit(f"Erro ao gerar áudio: {str(e)}")
            return None 