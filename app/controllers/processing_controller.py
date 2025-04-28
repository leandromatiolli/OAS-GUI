"""
Módulo controlador para processamento de dados
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import numpy as np

from app.models.processing import SignalProcessor
from app.models.data_store import DataStore
from typing import Dict, List, Tuple, Any, Optional

class ProcessingController(QObject):
    """Controlador para processamento de dados"""
    
    # Sinais
    demodulationStarted = pyqtSignal()
    demodulationFinished = pyqtSignal(dict)
    demodulationError = pyqtSignal(str)
    processingProgress = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Inicializa o controlador de processamento
        
        Args:
            parent: Objeto pai
        """
        super().__init__(parent)
        self.data = None
        self.demodulated_data = None
        
    def set_data(self, data: Dict[str, Any]):
        """
        Define os dados a serem processados
        
        Args:
            data: Dicionário com os dados a processar
        """
        self.data = data
        
        # Se já existirem dados demodulados, usar eles
        if 'demodulated' in data:
            self.demodulated_data = data
        else:
            self.demodulated_data = None
    
    @pyqtSlot()
    def demodulate_data(self):
        """Demodula os dados carregados"""
        if not self.data or 'waveforms' not in self.data:
            self.demodulationError.emit("Nenhum dado carregado para demodular")
            return
            
        # Verificar se o processamento está disponível
        if not SignalProcessor.is_available():
            self.demodulationError.emit("Módulos de processamento não disponíveis")
            return
            
        try:
            self.demodulationStarted.emit()
            self.processingProgress.emit("Iniciando demodulação...")
            
            # Verificar se temos dois canais
            waveforms = self.data['waveforms']
            if waveforms.shape[0] < 2:
                self.demodulationError.emit("Necessários dois canais para demodulação")
                return
                
            # Realizar ajuste da elipse
            self.processingProgress.emit("Ajustando elipse...")
            ellipse_params = SignalProcessor.fit_ellipse(waveforms)
            
            # Demodular o sinal
            self.processingProgress.emit("Demodulando sinal...")
            demodulated = SignalProcessor.demodulate(waveforms, ellipse_params)
            
            # Adicionar dados demodulados aos dados existentes
            self.demodulated_data = self.data.copy()
            self.demodulated_data['demodulated'] = demodulated
            self.demodulated_data['ellipse_params'] = ellipse_params
            
            self.processingProgress.emit("Demodulação concluída")
            self.demodulationFinished.emit(self.demodulated_data)
            
        except Exception as e:
            self.demodulationError.emit(f"Erro na demodulação: {str(e)}")
            
    def save_demodulated_data(self) -> str:
        """
        Salva os dados demodulados
        
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        if not self.demodulated_data:
            raise ValueError("Nenhum dado demodulado disponível para salvar")
            
        return DataStore.save_demodulated_data(self.demodulated_data)
    
    def calculate_spectrum(self) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]]]:
        """
        Calcula o espectro do sinal demodulado
        
        Returns:
            Tupla (frequências, magnitudes_dB, picos detectados)
        """
        if not self.demodulated_data or 'demodulated' not in self.demodulated_data:
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
            
        # Calcular espectro
        freq_axis, magnitudes_db = SignalProcessor.calculate_spectrum(demodulated, fs)
        
        # Encontrar picos principais
        peaks = SignalProcessor.find_peaks(magnitudes_db, freq_axis)
        
        return freq_axis, magnitudes_db, peaks
        
    def auto_demodulate(self, data: Dict[str, Any]) -> bool:
        """
        Realiza demodulação automática após a aquisição
        
        Args:
            data: Dados adquiridos
            
        Returns:
            True se a demodulação foi bem-sucedida, False caso contrário
        """
        self.set_data(data)
        
        try:
            self.demodulate_data()
            return True
        except Exception as e:
            self.demodulationError.emit(f"Erro na demodulação automática: {str(e)}")
            return False 