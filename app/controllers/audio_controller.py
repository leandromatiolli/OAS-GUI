"""
Controlador especializado para análise e processamento de áudio
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import numpy as np
import os
from scipy import signal
from scipy.io import wavfile
from app.utils.debug_log import log_debug, log_info, log_warning, log_error

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
        Carrega um arquivo com dados demodulados para análise de áudio.
        Se o arquivo contém dados brutos, aplica demodulação automática.
        
        Args:
            filename: Caminho do arquivo .pkl
        """
        try:
            log_info(f"Carregando arquivo para análise de áudio: {filename}")
            
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
                # Verificar se temos dados brutos para demodular
                if 'waveforms' in data and data['waveforms'] is not None:
                    log_info("Arquivo contém dados brutos - aplicando demodulação automática")
                    data = self._demodulate_raw_data(data)
                else:
                    raise ValueError("Arquivo não contém dados demodulados nem dados brutos")
                
            if 't' not in data:
                raise ValueError("Arquivo não contém vetor de tempo")
            
            # Armazenar dados
            self.current_data = data
            log_info(f"Dados carregados: {len(data['demodulated'])} pontos")
            
            # Emitir sinal com os dados carregados
            self.audioLoaded.emit(data)
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo de áudio: {str(e)}"
            log_error(error_msg)
            self.audioError.emit(error_msg)
    
    @pyqtSlot()
    def generate_audio(self):
        """Gera arquivo WAV a partir dos dados demodulados"""
        if not self.current_data:
            self.audioError.emit("Nenhum arquivo carregado")
            return
            
        try:
            log_info("Gerando arquivo de áudio WAV")
            
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
            
            log_debug(f"Taxa de amostragem original: {original_fs} Hz")
            
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
            log_info(f"Arquivo de áudio salvo: {filename}")
            
            # Emitir sinal de sucesso
            self.audioGenerated.emit(filename)
            
        except Exception as e:
            error_msg = f"Erro ao gerar áudio: {str(e)}"
            log_error(error_msg)
            self.audioError.emit(error_msg)
    
    @pyqtSlot()
    def calculate_spectrum(self):
        """Calcula o espectro do sinal demodulado"""
        if not self.current_data:
            self.audioError.emit("Nenhum arquivo carregado")
            return
            
        try:
            log_info("Calculando espectro do sinal")
            
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
            
            log_debug(f"Espectro calculado: {len(frequencies)} pontos, freq_max={frequencies[-1]} Hz")
            
            # Emitir sinal com o espectro
            self.spectrumCalculated.emit(frequencies, magnitudes)
            
        except Exception as e:
            error_msg = f"Erro ao calcular espectro: {str(e)}"
            log_error(error_msg)
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
        
        log_debug(f"Reamostragem: {original_fs} Hz -> {self.sample_rate} Hz (up={up}, down={down})")
        
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
    
    def _demodulate_raw_data(self, data):
        """
        Demodula dados brutos usando parâmetros da elipse contidos no arquivo
        
        Args:
            data: Dados brutos do arquivo
            
        Returns:
            Dados com sinal demodulado adicionado
        """
        try:
            log_info("Iniciando demodulação automática de dados brutos")
            
            # Verificar se temos dados brutos suficientes
            if 'waveforms' not in data or data['waveforms'] is None:
                raise ValueError("Dados brutos não encontrados")
                
            waveforms = data['waveforms']
            if waveforms.shape[0] < 2:
                raise ValueError("Precisamos de pelo menos 2 canais para demodulação")
            
            # Determinar taxa de amostragem
            if 'sample_frequency' in data and 'decimation' in data:
                fs = data['sample_frequency'] / data['decimation']
            elif 'sample_frequency_effective' in data:
                fs = data['sample_frequency_effective']
            else:
                fs = 1.953125e6  # valor padrão (125MHz/64)
            
            log_debug(f"Taxa de amostragem: {fs} Hz")
            
            # Procurar parâmetros da elipse nos metadados
            ellipse_params = None
            
            # Verificar metadados TOML
            if 'metadata' in data and isinstance(data['metadata'], dict):
                metadata = data['metadata']
                if 'calibration_info' in metadata and metadata['calibration_info'].get('ellipse_params'):
                    ellipse_params_raw = metadata['calibration_info']['ellipse_params']
                    log_info("Encontrados parâmetros da elipse nos metadados TOML")
                    ellipse_params = self._convert_ellipse_params(ellipse_params_raw)
                elif 'ellipse_params' in metadata:
                    ellipse_params_raw = metadata['ellipse_params']
                    log_info("Encontrados parâmetros da elipse nos metadados (formato antigo)")
                    ellipse_params = self._convert_ellipse_params(ellipse_params_raw)
            
            # Se não encontrou nos metadados, verificar se existem nos dados
            if ellipse_params is None and 'ellipse_params' in data and data['ellipse_params'] is not None:
                log_info("Usando parâmetros da elipse existentes nos dados")
                ellipse_params = self._convert_ellipse_params(data['ellipse_params'])
            
            # Se ainda não encontrou, calcular novos parâmetros
            if ellipse_params is None:
                log_info("Calculando novos parâmetros da elipse")
                from app.models.processing import SignalProcessor
                ellipse_params = SignalProcessor.fit_ellipse(waveforms)
            
            # Demodular o sinal
            log_debug("Demodulando sinal usando parâmetros da elipse")
            from app.models.processing import SignalProcessor
            demodulated = SignalProcessor.demodulate(waveforms, ellipse_params)
            
            # Adicionar dados demodulados ao arquivo
            data['demodulated'] = demodulated
            
            # Criar vetor de tempo se não existir
            if 't' not in data:
                num_samples = waveforms.shape[1]
                data['t'] = np.arange(num_samples) / fs
            
            # Adicionar parâmetros da elipse aos dados
            data['ellipse_params'] = ellipse_params
            
            log_info(f"Demodulação concluída: {len(demodulated)} pontos")
            return data
            
        except Exception as e:
            log_error(f"Erro na demodulação automática: {str(e)}")
            raise ValueError(f"Erro na demodulação automática: {str(e)}")
    
    def _convert_ellipse_params(self, ellipse_params_raw):
        """
        Converte parâmetros da elipse para formato numpy array
        
        Args:
            ellipse_params_raw: Parâmetros em formato dict ou lista
            
        Returns:
            Array numpy com parâmetros da elipse
        """
        try:
            if isinstance(ellipse_params_raw, dict):
                # Converter dict para array
                if 'a' in ellipse_params_raw and 'b' in ellipse_params_raw:
                    # Formato com parâmetros a, b, etc.
                    a = ellipse_params_raw['a']
                    b = ellipse_params_raw['b']
                    x0 = ellipse_params_raw.get('x0', 0)
                    y0 = ellipse_params_raw.get('y0', 0)
                    theta = ellipse_params_raw.get('theta', 0)
                    ellipse_params = np.array([a, b, x0, y0, theta])
                else:
                    # Formato com chaves numéricas
                    keys = sorted([k for k in ellipse_params_raw.keys() if isinstance(k, (int, str)) and str(k).isdigit()])
                    ellipse_params = np.array([ellipse_params_raw[k] for k in keys])
            elif isinstance(ellipse_params_raw, (list, tuple)):
                # Converter lista/tupla para array
                ellipse_params = np.array(ellipse_params_raw)
            else:
                # Assumir que já é um array numpy
                ellipse_params = np.array(ellipse_params_raw)
            
            log_debug(f"Parâmetros da elipse convertidos: {ellipse_params}")
            return ellipse_params
            
        except Exception as e:
            log_error(f"Erro ao converter parâmetros da elipse: {str(e)}")
            raise ValueError(f"Erro ao converter parâmetros da elipse: {str(e)}") 