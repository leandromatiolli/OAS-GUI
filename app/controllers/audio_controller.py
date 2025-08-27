"""
Controlador especializado para análise e processamento de áudio
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import numpy as np
import os
from scipy import signal
from scipy.io import wavfile
from app.utils import log

class AudioController(QObject):
    """Controlador para análise e processamento de áudio"""
    
    # Sinais
    audioLoaded = pyqtSignal(dict)  # Dados de áudio carregados
    audioGenerated = pyqtSignal(str)  # Arquivo WAV gerado
    audioError = pyqtSignal(str)  # Erro no processamento
    spectrumCalculated = pyqtSignal(np.ndarray, np.ndarray)  # Frequências e magnitudes
    
    def __init__(self, parent=None):
        """Inicializa o controlador de áudio"""
        super().__init__(parent)
        self.current_data = None
        self.current_audio_path = None
        self.sample_rate = 44100  # Taxa padrão para áudio
        
    @pyqtSlot(str)
    def load_audio_file(self, filename: str):
        """
        Carrega um arquivo com dados demodulados para análise de áudio
        
        Args:
            filename: Caminho do arquivo .pkl
        """
        try:
            log.info(f"Carregando arquivo para análise de áudio: {filename}")
            
            # Carregar dados do arquivo pickle
            import pickle
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                
            # Converter para dict se necessário
            if not isinstance(data, dict):
                temp_dict = {}
                for key in dir(data):
                    if not key.startswith('__') and not callable(getattr(data, key)):
                        temp_dict[key] = getattr(data, key)
                data = temp_dict
            
            # Verificar se temos dados demodulados
            if 'demodulated' not in data:
                raise ValueError("Arquivo não contém dados demodulados")
                
            if 't' not in data:
                raise ValueError("Arquivo não contém vetor de tempo")
            
            # Armazenar dados
            self.current_data = data
            log.info(f"Dados carregados: {len(data['demodulated'])} pontos")
            
            # Emitir sinal com os dados carregados
            self.audioLoaded.emit(data)
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo de áudio: {str(e)}"
            log.error(error_msg)
            self.audioError.emit(error_msg)
    
    @pyqtSlot()
    def generate_audio(self):
        """Gera arquivo WAV a partir dos dados demodulados"""
        if not self.current_data:
            self.audioError.emit("Nenhum arquivo carregado")
            return
            
        try:
            log.info("Gerando arquivo de áudio WAV")
            
            # Obter dados demodulados
            demodulated = self.current_data['demodulated']
            
            # Determinar taxa de amostragem original
            if 'sample_frequency_effective' in self.current_data:
                original_fs = self.current_data['sample_frequency_effective']
            elif 'sample_frequency' in self.current_data and 'decimation' in self.current_data:
                original_fs = self.current_data['sample_frequency'] / self.current_data['decimation']
            else:
                # Calcular a partir do vetor de tempo
                t = self.current_data['t']
                dt = t[1] - t[0]
                original_fs = 1 / dt
            
            log.debug(f"Taxa de amostragem original: {original_fs} Hz")
            
            # Aplicar filtros de áudio
            audio_signal = self._apply_audio_filters(demodulated, original_fs)
            
            # Reamostrar para taxa de áudio padrão
            audio_signal = self._resample_to_audio_rate(audio_signal, original_fs)
            
            # Normalizar e converter para formato de áudio
            audio_signal = self._normalize_and_convert(audio_signal)
            
            # Gerar nome do arquivo
            filename = self._generate_audio_filename()
            
            # Salvar arquivo WAV
            wavfile.write(filename, self.sample_rate, audio_signal)
            
            self.current_audio_path = filename
            log.info(f"Arquivo de áudio salvo: {filename}")
            
            # Emitir sinal de sucesso
            self.audioGenerated.emit(filename)
            
        except Exception as e:
            error_msg = f"Erro ao gerar áudio: {str(e)}"
            log.error(error_msg)
            self.audioError.emit(error_msg)
    
    @pyqtSlot()
    def calculate_spectrum(self):
        """Calcula o espectro do sinal demodulado"""
        if not self.current_data:
            self.audioError.emit("Nenhum arquivo carregado")
            return
            
        try:
            log.info("Calculando espectro do sinal")
            
            demodulated = self.current_data['demodulated']
            
            # Determinar taxa de amostragem
            if 'sample_frequency_effective' in self.current_data:
                fs = self.current_data['sample_frequency_effective']
            elif 'sample_frequency' in self.current_data and 'decimation' in self.current_data:
                fs = self.current_data['sample_frequency'] / self.current_data['decimation']
            else:
                t = self.current_data['t']
                dt = t[1] - t[0]
                fs = 1 / dt
            
            # Aplicar janela e calcular FFT
            window = signal.get_window('blackman', len(demodulated))
            signal_windowed = demodulated * window
            
            N = len(signal_windowed)
            fft_result = np.fft.fft(signal_windowed)
            fft_result = fft_result / N
            
            # Calcular magnitudes e frequências
            magnitudes = np.abs(fft_result[:N//2])
            frequencies = np.arange(N//2) * fs / N
            
            log.debug(f"Espectro calculado: {len(frequencies)} pontos, freq_max={frequencies[-1]} Hz")
            
            # Emitir sinal com o espectro
            self.spectrumCalculated.emit(frequencies, magnitudes)
            
        except Exception as e:
            error_msg = f"Erro ao calcular espectro: {str(e)}"
            log.error(error_msg)
            self.audioError.emit(error_msg)
    
    def _apply_audio_filters(self, signal_data, fs):
        """Aplica filtros para conversão para áudio"""
        # Filtro passa-alta para remover DC e frequências muito baixas
        sos_high = signal.butter(4, 20, btype='high', fs=fs, output='sos')
        filtered = signal.sosfilt(sos_high, signal_data)
        
        # Filtro passa-baixa para limitar a banda de áudio
        sos_low = signal.butter(4, 20000, btype='low', fs=fs, output='sos')
        filtered = signal.sosfilt(sos_low, filtered)
        
        return filtered
    
    def _resample_to_audio_rate(self, signal_data, original_fs):
        """Reamostra o sinal para taxa de áudio"""
        if original_fs == self.sample_rate:
            return signal_data
            
        # Calcular fatores de reamostragem
        from math import gcd
        common_divisor = gcd(int(original_fs), self.sample_rate)
        up = self.sample_rate // common_divisor
        down = int(original_fs) // common_divisor
        
        log.debug(f"Reamostragem: {original_fs} Hz -> {self.sample_rate} Hz (up={up}, down={down})")
        
        # Reamostrar
        resampled = signal.resample_poly(signal_data, up, down)
        return resampled
    
    def _normalize_and_convert(self, signal_data):
        """Normaliza e converte para formato PCM 16-bit"""
        # Normalizar para [-1, 1]
        max_val = np.max(np.abs(signal_data))
        if max_val > 0:
            normalized = signal_data / max_val
        else:
            normalized = signal_data
        
        # Converter para PCM 16-bit
        pcm_signal = (normalized * 32767).astype(np.int16)
        return pcm_signal
    
    def _generate_audio_filename(self):
        """Gera nome do arquivo de áudio baseado nos metadados"""
        if not self.current_data or 'metadata' not in self.current_data:
            return "audio_demodulado.wav"
            
        metadata = self.current_data['metadata']
        timestamp = metadata.get('timestamp', 'unknown')
        
        # Nome baseado no timestamp
        filename = f"audio_{timestamp}.wav"
        return filename
    
    def get_current_audio_path(self):
        """Retorna o caminho do último arquivo de áudio gerado"""
        return self.current_audio_path 