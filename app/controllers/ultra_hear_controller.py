"""
Controlador Ultra-Hear para processamento de frequências ultrassônicas
Implementa algoritmos de transposição de frequência e filtros avançados
"""
import os
import time
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, ifft
from scipy.io import wavfile
import pickle
from PyQt5.QtCore import QObject, pyqtSignal

import app.utils.log as log

class UltraHearController(QObject):
    """Controlador para processamento de áudio ultrassônico"""
    
    # Sinais
    dataLoaded = pyqtSignal(dict)  # Dados carregados
    processingFinished = pyqtSignal(dict)  # Processamento concluído
    processingError = pyqtSignal(str)  # Erro no processamento
    
    def __init__(self):
        """Inicializa o controlador"""
        super().__init__()
        self.current_data = None
        self.processed_audio_path = None
        
    def load_audio_file(self, file_path):
        """
        Carrega arquivo de áudio para processamento
        
        Args:
            file_path: Caminho do arquivo
        """
        try:
            log.info(f"Carregando arquivo para Ultra-Hear: {file_path}")
            
            # Carregar arquivo pickle
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # Verificar se contém dados demodulados
            if 'demodulated' not in data:
                raise ValueError("Arquivo não contém dados demodulados")
            
            self.current_data = data
            log.info(f"Dados carregados: {len(data['demodulated'])} pontos")
            
            # Emitir sinal
            self.dataLoaded.emit(data)
            
        except Exception as e:
            error_msg = f"Erro ao carregar arquivo: {str(e)}"
            log.error(error_msg)
            self.processingError.emit(error_msg)
    
    def process_ultrasonic_audio(self, params):
        """
        Processa áudio ultrassônico com base nos parâmetros
        
        Args:
            params: Dicionário com parâmetros de processamento
        """
        try:
            start_time = time.time()
            log.info("Iniciando processamento Ultra-Hear")
            log.debug(f"Parâmetros: {params}")
            
            # Carregar dados se necessário
            if params['file_path'] != getattr(self, 'current_file_path', None):
                self.load_audio_file(params['file_path'])
                self.current_file_path = params['file_path']
            
            if self.current_data is None:
                raise ValueError("Nenhum dado carregado")
            
            # Extrair sinal e parâmetros
            signal_data = self.current_data['demodulated'].copy()
            fs_original = self.current_data.get('sample_frequency_effective', 1953125.0)
            
            log.debug(f"Sinal original: {len(signal_data)} pontos, fs={fs_original} Hz")
            
            # ETAPA 1: Filtrar frequências
            filtered_signal, filtered_spectrum = self.apply_frequency_filters(
                signal_data, fs_original, params
            )
            
            # ETAPA 2: Transpor frequências se necessário
            if params['enable_transpose']:
                processed_signal, fs_output = self.transpose_frequencies(
                    filtered_signal, fs_original, params
                )
            else:
                processed_signal = filtered_signal
                fs_output = 44100  # Taxa padrão para áudio
                
                # Reamostrar para taxa de áudio padrão
                processed_signal = self.resample_signal(
                    processed_signal, fs_original, fs_output
                )
            
            # ETAPA 3: Controlar amplitude
            processed_signal = self.control_amplitude(processed_signal, params)
            
            # ETAPA 4: Salvar arquivo de áudio
            audio_path = self.save_processed_audio(processed_signal, fs_output, params)
            
            # Calcular informações do resultado
            processing_time = time.time() - start_time
            
            # Preparar resultado
            result = {
                'success': True,
                'audio_path': audio_path,
                'processed_signal': processed_signal,
                'time_axis': np.arange(len(processed_signal)) / fs_output,
                'filtered_spectrum': filtered_spectrum,
                'original_freq_range': (0, fs_original/2),
                'transposed_freq_range': (0, fs_output/2) if params['enable_transpose'] else None,
                'processing_time': processing_time,
                'bands_applied': params['frequency_bands']
            }
            
            self.processed_audio_path = audio_path
            log.info(f"Processamento concluído em {processing_time:.2f}s")
            
            # Emitir sinal de sucesso
            self.processingFinished.emit(result)
            
        except Exception as e:
            error_msg = f"Erro no processamento: {str(e)}"
            log.error(error_msg)
            self.processingError.emit(error_msg)
    
    def apply_frequency_filters(self, signal_data, fs, params):
        """
        Aplica filtros de frequência ao sinal
        
        Args:
            signal_data: Sinal original
            fs: Taxa de amostragem
            params: Parâmetros de filtragem
            
        Returns:
            tuple: (sinal_filtrado, espectro_filtrado)
        """
        log.debug("Aplicando filtros de frequência")
        
        # Calcular FFT do sinal original
        n = len(signal_data)
        freqs = fftfreq(n, 1/fs)[:n//2]
        spectrum = fft(signal_data)
        
        # Criar máscara de filtro
        filter_mask = np.zeros(len(spectrum), dtype=bool)
        
        if params['selection_mode'] == "Seleção Manual":
            # Usar frequências mínima e máxima
            freq_min = params['freq_min']
            freq_max = params['freq_max']
            
            # Encontrar índices correspondentes
            idx_min = np.searchsorted(freqs, freq_min)
            idx_max = np.searchsorted(freqs, freq_max)
            
            # Aplicar filtro (simétrico para frequências negativas)
            filter_mask[idx_min:idx_max] = True
            filter_mask[-(idx_max-1):-(idx_min-1)] = True
            
            log.debug(f"Filtro manual: {freq_min}-{freq_max} Hz")
            
        elif params['selection_mode'] == "Seleção Interativa no Espectro":
            # Usar bandas selecionadas interativamente
            for freq_min, freq_max in params['frequency_bands']:
                idx_min = np.searchsorted(freqs, freq_min)
                idx_max = np.searchsorted(freqs, freq_max)
                
                filter_mask[idx_min:idx_max] = True
                filter_mask[-(idx_max-1):-(idx_min-1)] = True
                
                log.debug(f"Banda interativa: {freq_min:.1f}-{freq_max:.1f} Hz")
        
        elif params['selection_mode'] == "Bandas Pré-definidas":
            # Usar bandas pré-definidas para ultrassom
            predefined_bands = [
                (20000, 40000),   # 20-40 kHz
                (40000, 80000),   # 40-80 kHz
                (80000, 120000),  # 80-120 kHz
            ]
            
            for freq_min, freq_max in predefined_bands:
                if freq_max <= fs/2:  # Verificar Nyquist
                    idx_min = np.searchsorted(freqs, freq_min)
                    idx_max = np.searchsorted(freqs, freq_max)
                    
                    filter_mask[idx_min:idx_max] = True
                    filter_mask[-(idx_max-1):-(idx_min-1)] = True
        
        # Aplicar filtro no domínio da frequência
        filtered_spectrum = spectrum.copy()
        filtered_spectrum[~filter_mask] = 0
        
        # Converter de volta para domínio do tempo
        filtered_signal = np.real(ifft(filtered_spectrum))
        
        # Preparar espectro para visualização
        filtered_spectrum_viz = {
            'frequencies': freqs,
            'magnitudes': 20 * np.log10(np.abs(filtered_spectrum[:n//2]) + 1e-12)
        }
        
        log.debug(f"Filtro aplicado, energia preservada: {np.sum(filter_mask)/len(filter_mask)*100:.1f}%")
        
        return filtered_signal, filtered_spectrum_viz
    
    def transpose_frequencies(self, signal_data, fs_input, params):
        """
        Transpõe frequências para faixa audível
        
        Args:
            signal_data: Sinal filtrado
            fs_input: Taxa de amostragem de entrada
            params: Parâmetros de transposição
            
        Returns:
            tuple: (sinal_transposto, fs_saida)
        """
        method = params['transpose_method']
        log.debug(f"Transposição por {method}")
        
        if method == "Divisão de Frequência":
            return self._frequency_division(signal_data, fs_input, params)
        
        elif method == "Heterodino (Mixing)":
            return self._heterodyne_mixing(signal_data, fs_input, params)
        
        elif method == "Modulação em Amplitude":
            return self._amplitude_modulation(signal_data, fs_input, params)
        
        elif method == "Compressão Temporal":
            return self._time_compression(signal_data, fs_input, params)
        
        else:
            raise ValueError(f"Método de transposição desconhecido: {method}")
    
    def _frequency_division(self, signal_data, fs_input, params):
        """Transposição por divisão de frequência"""
        division_factor = params['division_factor']
        maintain_speed = params['maintain_speed']
        
        if maintain_speed:
            # Reamostrar mantendo velocidade
            fs_output = 44100
            # Calcular nova taxa efetiva
            effective_fs = fs_input / division_factor
            
            # Reamostrar para taxa de áudio
            resampled_signal = self.resample_signal(signal_data, effective_fs, fs_output)
            
        else:
            # Simplesmente reduzir taxa de amostragem
            fs_output = fs_input // division_factor
            # Decimação simples
            resampled_signal = signal_data[::division_factor]
        
        log.debug(f"Divisão de frequência: fator={division_factor}, fs_out={fs_output}")
        return resampled_signal, fs_output
    
    def _heterodyne_mixing(self, signal_data, fs_input, params):
        """Transposição por mistura heteródina"""
        target_freq = params['target_freq']
        fs_output = 44100
        
        # Encontrar frequência central do sinal
        n = len(signal_data)
        freqs = fftfreq(n, 1/fs_input)
        spectrum = np.abs(fft(signal_data))
        
        # Encontrar pico principal
        peak_idx = np.argmax(spectrum[:n//2])
        center_freq = freqs[peak_idx]
        
        # Calcular frequência de mistura
        mix_freq = center_freq - target_freq
        
        # Gerar sinal de mistura
        t = np.arange(len(signal_data)) / fs_input
        mix_signal = np.cos(2 * np.pi * mix_freq * t)
        
        # Misturar sinais
        mixed_signal = signal_data * mix_signal
        
        # Filtro passa-baixa para remover componentes de alta frequência
        nyquist = fs_output / 2
        cutoff = min(target_freq * 2, nyquist * 0.9)
        b, a = signal.butter(6, cutoff / nyquist, btype='low')
        filtered_mixed = signal.filtfilt(b, a, mixed_signal)
        
        # Reamostrar para taxa de áudio
        resampled_signal = self.resample_signal(filtered_mixed, fs_input, fs_output)
        
        log.debug(f"Mistura heteródina: center={center_freq:.1f}Hz, mix={mix_freq:.1f}Hz, target={target_freq:.1f}Hz")
        return resampled_signal, fs_output
    
    def _amplitude_modulation(self, signal_data, fs_input, params):
        """Transposição por modulação de amplitude"""
        target_freq = params['target_freq']
        fs_output = 44100
        
        # Calcular envelope do sinal
        analytic_signal = signal.hilbert(signal_data)
        envelope = np.abs(analytic_signal)
        
        # Gerar portadora na frequência alvo
        t_output = np.arange(len(envelope)) / fs_input
        carrier = np.sin(2 * np.pi * target_freq * t_output)
        
        # Modular amplitude
        modulated_signal = envelope * carrier
        
        # Reamostrar para taxa de áudio
        resampled_signal = self.resample_signal(modulated_signal, fs_input, fs_output)
        
        log.debug(f"Modulação AM: freq_portadora={target_freq:.1f}Hz")
        return resampled_signal, fs_output
    
    def _time_compression(self, signal_data, fs_input, params):
        """Transposição por compressão temporal"""
        division_factor = params['division_factor']
        fs_output = 44100
        
        # Compressão temporal usando PSOLA (Pitch Synchronous Overlap and Add)
        # Implementação simplificada
        
        # Calcular novo comprimento
        new_length = len(signal_data) // division_factor
        
        # Reamostrar com interpolação
        from scipy.interpolate import interp1d
        
        old_indices = np.arange(len(signal_data))
        new_indices = np.linspace(0, len(signal_data)-1, new_length)
        
        interpolator = interp1d(old_indices, signal_data, kind='linear')
        compressed_signal = interpolator(new_indices)
        
        # Ajustar taxa de amostragem
        effective_fs = fs_input / division_factor
        resampled_signal = self.resample_signal(compressed_signal, effective_fs, fs_output)
        
        log.debug(f"Compressão temporal: fator={division_factor}, novo_comprimento={new_length}")
        return resampled_signal, fs_output
    
    def control_amplitude(self, signal_data, params):
        """
        Controla a amplitude do sinal processado
        
        Args:
            signal_data: Sinal a ser processado
            params: Parâmetros de controle
            
        Returns:
            np.array: Sinal com amplitude controlada
        """
        log.debug("Controlando amplitude")
        
        processed_signal = signal_data.copy()
        
        # Aplicar ganho
        gain_linear = 10 ** (params['gain_db'] / 20)
        processed_signal *= gain_linear
        
        # Aplicar normalização
        norm_type = params['normalization_type']
        
        if norm_type == "Peak Normalization":
            # Normalização por pico
            peak_value = np.max(np.abs(processed_signal))
            if peak_value > 0:
                processed_signal = processed_signal / peak_value * 0.95
                
        elif norm_type == "RMS Normalization":
            # Normalização RMS
            rms_value = np.sqrt(np.mean(processed_signal**2))
            if rms_value > 0:
                target_rms = 0.1  # -20 dB RMS
                processed_signal = processed_signal / rms_value * target_rms
                
        elif norm_type == "Compressão Dinâmica":
            # Compressão dinâmica simples
            threshold = 0.5
            ratio = 4.0
            
            # Calcular envelope
            envelope = np.abs(signal.hilbert(processed_signal))
            
            # Aplicar compressão onde necessário
            compression_mask = envelope > threshold
            compression_factor = 1 + (envelope[compression_mask] - threshold) * (1 - 1/ratio)
            
            processed_signal[compression_mask] /= compression_factor
        
        # Aplicar faixa de amplitude (clipping suave)
        amp_min_linear = 10 ** (params['amplitude_min'] / 20)
        amp_max_linear = 10 ** (params['amplitude_max'] / 20)
        
        # Clipping suave usando tanh
        processed_signal = np.tanh(processed_signal / amp_max_linear) * amp_max_linear
        
        # Garantir que não há valores muito pequenos
        processed_signal = np.where(
            np.abs(processed_signal) < amp_min_linear,
            0,
            processed_signal
        )
        
        log.debug(f"Amplitude controlada: ganho={params['gain_db']}dB, norm={norm_type}")
        return processed_signal
    
    def resample_signal(self, signal_data, fs_input, fs_output):
        """
        Reamostra sinal para nova taxa de amostragem
        
        Args:
            signal_data: Sinal original
            fs_input: Taxa de entrada
            fs_output: Taxa de saída
            
        Returns:
            np.array: Sinal reamostrado
        """
        if fs_input == fs_output:
            return signal_data
        
        # Calcular fator de reamostragem
        resample_ratio = fs_output / fs_input
        new_length = int(len(signal_data) * resample_ratio)
        
        # Usar scipy.signal.resample para reamostragem de alta qualidade
        resampled_signal = signal.resample(signal_data, new_length)
        
        log.debug(f"Reamostragem: {fs_input}Hz -> {fs_output}Hz, {len(signal_data)} -> {len(resampled_signal)} pontos")
        return resampled_signal
    
    def save_processed_audio(self, signal_data, fs, params):
        """
        Salva o áudio processado em arquivo WAV
        
        Args:
            signal_data: Sinal processado
            fs: Taxa de amostragem
            params: Parâmetros de processamento
            
        Returns:
            str: Caminho do arquivo salvo
        """
        # Gerar nome do arquivo
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"ultra_hear_{timestamp}.wav"
        
        # Normalizar para 16-bit PCM
        signal_normalized = signal_data / np.max(np.abs(signal_data)) * 0.95
        signal_16bit = (signal_normalized * 32767).astype(np.int16)
        
        # Salvar arquivo
        wavfile.write(filename, int(fs), signal_16bit)
        
        log.info(f"Áudio Ultra-Hear salvo: {filename}")
        return filename
    
    def get_current_audio_path(self):
        """Retorna o caminho do último áudio processado"""
        return self.processed_audio_path