"""
Módulo para processamento de sinais e transformações
"""
import numpy as np
from scipy import signal, optimize
from app.utils import log
from typing import Dict, List, Tuple, Optional, Union, Any

# Importar funções para processamento
try:
    import mkf
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False
    log.warning("Módulo de processamento MKF não encontrado. Funcionalidade de demodulação avançada indisponível.")

class SignalProcessor:
    """Classe para processamento de sinais"""
    
    @staticmethod
    def is_available() -> bool:
        """Verifica se o processamento avançado está disponível"""
        return PROCESSING_AVAILABLE
    
    @staticmethod
    def apply_bandpass_filter(signal_data: np.ndarray, fs: float, low_freq: float, high_freq: float, order: int) -> np.ndarray:
        """
        Aplica um filtro passa-banda ao sinal
        
        Args:
            signal_data: Sinal a ser filtrado
            fs: Frequência de amostragem em Hz
            low_freq: Frequência de corte inferior em Hz
            high_freq: Frequência de corte superior em Hz
            order: Ordem do filtro
            
        Returns:
            Sinal filtrado
        """
            
        # Limitar ordem do filtro (valores muito altos podem causar instabilidade)
        order = max(1, min(10, order))
        
        log.debug(f"Aplicando filtro passa-banda: {low_freq:.1f} Hz - {high_freq:.1f} Hz, ordem {order}, fs={fs:.1f} Hz")
        
        try:
            # Projetar o filtro Butterworth passa-banda
            sos = signal.butter(order, [low_freq, high_freq], btype='band', analog=False, output='sos', fs=fs)

            # Aplicar o filtro usando sosfilt (filtro de fase zero)
            zi = signal.sosfilt_zi(sos)
            filtered_signal, zo = signal.sosfilt(sos, signal_data, zi=zi*signal_data[0])
            
            return filtered_signal
            
        except Exception as e:
            log.error(f"Erro ao aplicar filtro passa-banda: {str(e)}")
            return signal_data  # Retornar sinal original em caso de erro
    
    @staticmethod
    def apply_moving_average(signal_data: np.ndarray, window_size: int) -> np.ndarray:
        """
        Aplica média móvel no sinal para remover ruídos de alta frequência
        
        Args:
            signal_data: Sinal a ser filtrado. Pode ser um array 1D ou 2D [canais, amostras]
            window_size: Tamanho da janela de média móvel (deve ser ímpar)
            
        Returns:
            Sinal filtrado com a mesma forma do sinal original
        """
        # Garantir que o tamanho da janela seja ímpar
        if window_size % 2 == 0:
            window_size += 1
            log.debug(f"apply_moving_average: Ajustando janela para {window_size} (valor ímpar)")
        else:
            log.debug(f"apply_moving_average: Usando janela de tamanho {window_size}")
            
        # Verificar formato do array de entrada
        if signal_data.ndim == 1:
            log.debug(f"Aplicando média móvel em array 1D (length={len(signal_data)})")
            # Criar kernel da média móvel
            kernel = np.ones(window_size) / window_size
            # Aplicar a convolução para calcular a média móvel
            smoothed = signal.convolve(signal_data, kernel, mode='same')
            return smoothed
        elif signal_data.ndim == 2:
            # Array 2D [canais, amostras]
            num_channels, num_samples = signal_data.shape
            log.debug(f"Aplicando média móvel em array 2D ({num_channels} canais, {num_samples} amostras)")
            
            smoothed = np.zeros_like(signal_data)
            for i in range(signal_data.shape[0]):
                kernel = np.ones(window_size) / window_size
                # Verificar por valores NaN ou infinitos
                if np.isnan(signal_data[i]).any() or np.isinf(signal_data[i]).any():
                    log.warning(f"AVISO: Canal {i} contém valores NaN ou infinitos")
                    # Substituir valores problemáticos
                    channel_data = np.copy(signal_data[i])
                    channel_data[np.isnan(channel_data)] = 0
                    channel_data[np.isinf(channel_data)] = 0
                    smoothed[i] = signal.convolve(channel_data, kernel, mode='same')
                else:
                    smoothed[i] = signal.convolve(signal_data[i], kernel, mode='same')
                
                # Verificar diferença para confirmar que a média foi aplicada
                diff = np.abs(signal_data[i] - smoothed[i]).mean()
                log.debug(f"Canal {i}: Diferença média após aplicação da média: {diff}")
                
            return smoothed
        else:
            error_msg = f"Formato de sinal não suportado para média móvel: {signal_data.ndim}D"
            log.error(error_msg)
            raise ValueError(error_msg)
    
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
            
        # Verificar se temos dois canais
        if waveforms.shape[0] < 2:
            error_msg = "Necessários dois canais para fit da elipse"
            log.error(error_msg)
            raise ValueError(error_msg)
            
        # Limitar o número de pontos para o fit, se necessário
        if waveforms.shape[1] > max_points:
            step = waveforms.shape[1] // max_points
            waveforms_fit = waveforms[:, ::step]
            log.debug(f"Reduzindo pontos para fit de elipse: {waveforms.shape[1]} -> {waveforms_fit.shape[1]}")
        else:
            waveforms_fit = waveforms
            
        # Realizar o fit
        log.debug(f"Iniciando fit de elipse com {waveforms_fit.shape[1]} pontos")
        ellipse_params = mkf.fit_ellipse(*waveforms_fit)
        log.debug(f"Fit de elipse concluído: {ellipse_params}")
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
            error_msg = "Processamento avançado não disponível"
            log.error(error_msg)
            raise RuntimeError(error_msg)
            
        try:
            # Tentar demodulação direta
            log.debug("Tentando demodulação direta com mkf.demodulate")
            demodulated = mkf.demodulate(waveforms, ellipse_params)
        except (AttributeError, Exception) as e:
            # Implementação manual alternativa
            log.warning(f"Erro na demodulação direta: {str(e)}. Tentando implementação alternativa.")
            log.debug("Usando implementação alternativa com rescale + arctan2")
            x, y = mkf.rescale(*waveforms, ellipse_params)
            demodulated = np.unwrap(np.arctan2(y, x))
            
        log.debug(f"Demodulação concluída: resultado com {len(demodulated)} pontos")
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
        log.debug(f"Calculando espectro: fs={fs} Hz, {len(signal_data)} pontos, janela={window_type}")
        
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
        
        log.debug(f"Espectro calculado: {len(freq_axis)} pontos, freq_max={freq_axis[-1]:.1f} Hz")
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
        
        log.debug(f"Procurando picos: min_freq={min_freq} Hz, prominence={prominence}, distance={distance}")
        
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
        log.debug(f"Encontrados {len(result)} picos: {result}")
        
        return result 