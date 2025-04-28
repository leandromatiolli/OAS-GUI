"""
Módulo para processamento de sinais e transformações
"""
import numpy as np
from scipy import signal
from typing import Dict, List, Tuple, Optional, Union, Any

# Importar funções para processamento
try:
    import mkf
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False
    print("Módulo de processamento MKF não encontrado. Funcionalidade de demodulação avançada indisponível.")

class SignalProcessor:
    """Classe para processamento de sinais"""
    
    @staticmethod
    def is_available() -> bool:
        """Verifica se o processamento avançado está disponível"""
        return PROCESSING_AVAILABLE
    
    @staticmethod
    def fit_ellipse(waveforms: np.ndarray, max_points: int = 100000) -> np.ndarray:
        """
        Realiza o ajuste de elipse para os dados
        
        Args:
            waveforms: Array de formas de onda [canais, amostras]
            max_points: Número máximo de pontos a usar no fit
            
        Returns:
            Parâmetros da elipse ajustada
        """
        if not PROCESSING_AVAILABLE:
            raise RuntimeError("Processamento avançado não disponível")
            
        # Verificar se temos dois canais
        if waveforms.shape[0] < 2:
            raise ValueError("Necessários dois canais para fit da elipse")
            
        # Limitar o número de pontos para o fit, se necessário
        if waveforms.shape[1] > max_points:
            step = waveforms.shape[1] // max_points
            waveforms_fit = waveforms[:, ::step]
        else:
            waveforms_fit = waveforms
            
        # Realizar o fit
        ellipse_params = mkf.fit_ellipse(*waveforms_fit)
        return ellipse_params
    
    @staticmethod
    def demodulate(waveforms: np.ndarray, ellipse_params: np.ndarray) -> np.ndarray:
        """
        Demodula o sinal usando os parâmetros da elipse
        
        Args:
            waveforms: Array de formas de onda [canais, amostras]
            ellipse_params: Parâmetros da elipse ajustada
            
        Returns:
            Sinal demodulado
        """
        if not PROCESSING_AVAILABLE:
            raise RuntimeError("Processamento avançado não disponível")
            
        try:
            # Tentar demodulação direta
            demodulated = mkf.demodulate(waveforms, ellipse_params)
        except (AttributeError, Exception):
            # Implementação manual alternativa
            x, y = mkf.rescale(*waveforms, ellipse_params)
            demodulated = np.unwrap(np.arctan2(y, x))
            
        return demodulated
    
    @staticmethod
    def calculate_spectrum(signal_data: np.ndarray, fs: float, window_type: str = 'blackman') -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula o espectro de frequência de um sinal
        
        Args:
            signal_data: Sinal no domínio do tempo
            fs: Frequência de amostragem em Hz
            window_type: Tipo de janela a aplicar
            
        Returns:
            Tupla (frequências, magnitudes_dB)
        """
        # Aplicar janela
        from scipy.signal import get_window
        window = get_window(window_type, len(signal_data))
        signal_windowed = signal_data * window
        
        # Calcular FFT
        N = len(signal_windowed)
        fft_result = np.fft.fft(signal_windowed)
        fft_result = fft_result / N  # Normalização
        
        # Calcular magnitudes apenas para a primeira metade (frequências positivas)
        magnitudes = np.abs(fft_result[:N//2])
        
        # Calcular eixo de frequência
        freq_axis = np.arange(N//2) * fs / N
        
        # Converter para dB
        magnitudes_db = 20 * np.log10(magnitudes + 1e-10)  # Evitar log(0)
        
        return freq_axis, magnitudes_db
    
    @staticmethod
    def find_peaks(spectrum: np.ndarray, frequencies: np.ndarray, min_freq: float = 10000, 
                 max_peaks: int = 5, prominence: float = 5, distance: int = 20) -> List[Tuple[float, float]]:
        """
        Encontra os picos principais no espectro
        
        Args:
            spectrum: Espectro de magnitude em dB
            frequencies: Array de frequências correspondentes
            min_freq: Frequência mínima para considerar picos (Hz)
            max_peaks: Número máximo de picos a retornar
            prominence: Proeminência mínima dos picos
            distance: Distância mínima entre picos
            
        Returns:
            Lista de tuplas (frequência, amplitude) dos picos encontrados
        """
        from scipy.signal import find_peaks
        
        # Encontrar o índice no eixo de frequência que corresponde à frequência mínima
        min_freq_idx = np.argmin(np.abs(frequencies - min_freq))
        
        # Procurar picos apenas na região acima da frequência mínima
        high_freq_indices = np.arange(min_freq_idx, len(spectrum))
        high_freq_spectrum = spectrum[high_freq_indices]
        high_freq_axis = frequencies[high_freq_indices]
        
        # Encontrar picos na região de alta frequência
        rel_peaks, _ = find_peaks(high_freq_spectrum, prominence=prominence, distance=distance)
        
        # Converter índices relativos para índices absolutos
        peaks = high_freq_indices[rel_peaks]
        
        # Ordenar picos por amplitude (do maior para o menor)
        peak_heights = spectrum[peaks]
        sorted_indices = np.argsort(peak_heights)[::-1]  # Inverter para ter maior primeiro
        sorted_peaks = peaks[sorted_indices]
        
        # Pegar os maiores picos (limitado por max_peaks)
        top_peaks = sorted_peaks[:max_peaks]
        
        # Criar lista de tuplas (frequência, amplitude)
        result = [(frequencies[peak], spectrum[peak]) for peak in top_peaks]
        
        return result 