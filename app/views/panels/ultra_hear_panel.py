"""
Painel Ultra-Hear para análise de frequências ultrassônicas
Permite ouvir sinais em frequências acima do limite audível humano
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTabWidget, QGroupBox, QFileDialog,
                             QTextEdit, QMessageBox, QSlider, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QComboBox, QFormLayout,
                             QProgressBar, QSplitter)
from PyQt5.QtCore import pyqtSignal, Qt, QThread, pyqtSlot
import os
import numpy as np
from matplotlib.widgets import SpanSelector
import matplotlib.pyplot as plt

from app.views.widgets.canvas import MplCanvas
from app.utils.debug_log import log_debug, log_info, log_warning, log_error

class FrequencyBandSelector:
    """Classe para gerenciar seleção interativa de bandas de frequência"""
    
    def __init__(self, canvas, callback=None):
        self.canvas = canvas
        self.callback = callback
        self.selected_bands = []
        self.span_selectors = []
        self.active = False
        
    def activate(self):
        """Ativa a seleção de bandas"""
        self.active = True
        # Criar SpanSelector para seleção interativa
        span = SpanSelector(
            self.canvas.axes,
            self.on_band_selected,
            'horizontal',
            useblit=True,
            props=dict(alpha=0.3, facecolor='yellow'),
            interactive=True
        )
        self.span_selectors.append(span)
        log_info("Seleção de bandas de frequência ativada")
        
    def deactivate(self):
        """Desativa a seleção de bandas"""
        self.active = False
        for span in self.span_selectors:
            span.set_active(False)
        self.span_selectors.clear()
        log_info("Seleção de bandas de frequência desativada")
        
    def on_band_selected(self, xmin, xmax):
        """Callback quando uma banda é selecionada"""
        if xmin == xmax:
            return
            
        # Garantir ordem correta
        if xmin > xmax:
            xmin, xmax = xmax, xmin
            
        band = (xmin, xmax)
        self.selected_bands.append(band)
        
        log_info(f"Banda selecionada: {xmin:.1f} Hz - {xmax:.1f} Hz")
        
        if self.callback:
            self.callback(self.selected_bands)
            
    def clear_bands(self):
        """Limpa todas as bandas selecionadas"""
        self.selected_bands.clear()
        log_info("Bandas de frequência limpas")
        
    def get_bands(self):
        """Retorna as bandas selecionadas"""
        return self.selected_bands.copy()

class UltraHearPanel(QWidget):
    """Painel para análise de frequências ultrassônicas"""
    
    # Sinais
    audioFileSelected = pyqtSignal(str)  # Arquivo selecionado
    processUltrasonicRequested = pyqtSignal(dict)  # Processamento solicitado
    playProcessedAudioRequested = pyqtSignal()  # Reprodução solicitada
    
    def __init__(self, parent=None):
        """Inicializa o painel Ultra-Hear"""
        super().__init__(parent)
        self.current_file = None
        self.current_data = None
        self.processed_audio_path = None
        self.frequency_bands = []
        self.band_selector = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Seção de controle de arquivo
        file_group = self.create_file_control_group()
        layout.addWidget(file_group)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo - Controles
        controls_widget = self.create_controls_panel()
        main_splitter.addWidget(controls_widget)
        
        # Painel direito - Visualizações
        viz_widget = self.create_visualization_panel()
        main_splitter.addWidget(viz_widget)
        
        # Definir proporções
        main_splitter.setStretchFactor(0, 1)  # Controles
        main_splitter.setStretchFactor(1, 2)  # Visualizações
        
        layout.addWidget(main_splitter)
        
        # Barra de status
        self.status_bar = self.create_status_bar()
        layout.addWidget(self.status_bar)
    
    def create_file_control_group(self):
        """Cria o grupo de controles de arquivo"""
        group = QGroupBox("Arquivo de Dados")
        layout = QHBoxLayout(group)
        
        # Botão para selecionar arquivo
        self.select_file_button = QPushButton("Selecionar Arquivo")
        self.select_file_button.clicked.connect(self.on_select_file)
        layout.addWidget(self.select_file_button)
        
        # Label para mostrar arquivo selecionado
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.file_label)
        
        layout.addStretch()
        
        return group
    
    def create_controls_panel(self):
        """Cria o painel de controles"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de filtros de frequência
        freq_group = self.create_frequency_filter_group()
        layout.addWidget(freq_group)
        
        # Grupo de transposição de frequência
        transpose_group = self.create_frequency_transpose_group()
        layout.addWidget(transpose_group)
        
        # Grupo de controle de amplitude
        amplitude_group = self.create_amplitude_control_group()
        layout.addWidget(amplitude_group)
        
        # Grupo de processamento
        process_group = self.create_processing_group()
        layout.addWidget(process_group)
        
        layout.addStretch()
        
        return widget
    
    def create_frequency_filter_group(self):
        """Cria o grupo de filtros de frequência"""
        group = QGroupBox("Filtros de Frequência")
        layout = QFormLayout(group)
        
        # Modo de seleção
        self.selection_mode = QComboBox()
        self.selection_mode.addItems([
            "Seleção Manual",
            "Seleção Interativa no Espectro",
            "Bandas Pré-definidas"
        ])
        layout.addRow("Modo:", self.selection_mode)
        
        # Frequência mínima e máxima (para modo manual)
        self.freq_min_spinbox = QDoubleSpinBox()
        self.freq_min_spinbox.setRange(0, 1000000)
        self.freq_min_spinbox.setValue(20000)  # 20 kHz
        self.freq_min_spinbox.setSuffix(" Hz")
        layout.addRow("Freq. Mín:", self.freq_min_spinbox)
        
        self.freq_max_spinbox = QDoubleSpinBox()
        self.freq_max_spinbox.setRange(0, 1000000)
        self.freq_max_spinbox.setValue(100000)  # 100 kHz
        self.freq_max_spinbox.setSuffix(" Hz")
        layout.addRow("Freq. Máx:", self.freq_max_spinbox)
        
        # Botões de controle
        controls_layout = QHBoxLayout()
        
        self.activate_selection_button = QPushButton("Ativar Seleção")
        self.activate_selection_button.clicked.connect(self.on_activate_selection)
        self.activate_selection_button.setEnabled(False)
        controls_layout.addWidget(self.activate_selection_button)
        
        self.clear_bands_button = QPushButton("Limpar")
        self.clear_bands_button.clicked.connect(self.on_clear_bands)
        controls_layout.addWidget(self.clear_bands_button)
        
        layout.addRow(controls_layout)
        
        # Lista de bandas selecionadas
        self.bands_text = QTextEdit()
        self.bands_text.setMaximumHeight(80)
        self.bands_text.setReadOnly(True)
        self.bands_text.setPlaceholderText("Bandas selecionadas aparecerão aqui...")
        layout.addRow("Bandas:", self.bands_text)
        
        return group
    
    def create_frequency_transpose_group(self):
        """Cria o grupo de transposição de frequência"""
        group = QGroupBox("Transposição de Frequência")
        layout = QFormLayout(group)
        
        # Habilitar transposição
        self.enable_transpose = QCheckBox("Ativar Transposição")
        self.enable_transpose.stateChanged.connect(self.on_transpose_changed)
        layout.addRow(self.enable_transpose)
        
        # Método de transposição
        self.transpose_method = QComboBox()
        self.transpose_method.addItems([
            "Divisão de Frequência",
            "Heterodino (Mixing)",
            "Modulação em Amplitude",
            "Compressão Temporal"
        ])
        self.transpose_method.setEnabled(False)
        layout.addRow("Método:", self.transpose_method)
        
        # Fator de divisão
        self.division_factor = QSpinBox()
        self.division_factor.setRange(2, 50)
        self.division_factor.setValue(10)
        self.division_factor.setEnabled(False)
        layout.addRow("Fator Divisão:", self.division_factor)
        
        # Frequência alvo
        self.target_freq = QDoubleSpinBox()
        self.target_freq.setRange(20, 20000)
        self.target_freq.setValue(1000)  # 1 kHz
        self.target_freq.setSuffix(" Hz")
        self.target_freq.setEnabled(False)
        layout.addRow("Freq. Alvo:", self.target_freq)
        
        # Manter velocidade de reprodução
        self.maintain_speed = QCheckBox("Manter Velocidade de Reprodução")
        self.maintain_speed.setChecked(True)
        self.maintain_speed.setEnabled(False)
        layout.addRow(self.maintain_speed)
        
        return group
    
    def create_amplitude_control_group(self):
        """Cria o grupo de controle de amplitude"""
        group = QGroupBox("Controle de Amplitude")
        layout = QFormLayout(group)
        
        # Faixa de amplitude
        self.amplitude_min = QDoubleSpinBox()
        self.amplitude_min.setRange(-200, 0)
        self.amplitude_min.setValue(-60)
        self.amplitude_min.setSuffix(" dB")
        layout.addRow("Amplitude Mín:", self.amplitude_min)
        
        self.amplitude_max = QDoubleSpinBox()
        self.amplitude_max.setRange(-200, 0)
        self.amplitude_max.setValue(-10)
        self.amplitude_max.setSuffix(" dB")
        layout.addRow("Amplitude Máx:", self.amplitude_max)
        
        # Tipo de normalização
        self.normalization_type = QComboBox()
        self.normalization_type.addItems([
            "Sem Normalização",
            "Peak Normalization",
            "RMS Normalization",
            "Compressão Dinâmica"
        ])
        layout.addRow("Normalização:", self.normalization_type)
        
        # Ganho adicional
        self.gain_db = QDoubleSpinBox()
        self.gain_db.setRange(-60, 60)
        self.gain_db.setValue(0)
        self.gain_db.setSuffix(" dB")
        layout.addRow("Ganho:", self.gain_db)
        
        return group
    
    def create_processing_group(self):
        """Cria o grupo de processamento"""
        group = QGroupBox("Processamento")
        layout = QVBoxLayout(group)
        
        # Botão de processamento
        self.process_button = QPushButton("🔄 Processar Áudio")
        self.process_button.clicked.connect(self.on_process_audio)
        self.process_button.setEnabled(False)
        self.process_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.process_button)
        
        # Botão de reprodução
        self.play_button = QPushButton("🔊 Reproduzir")
        self.play_button.clicked.connect(self.on_play_audio)
        self.play_button.setEnabled(False)
        layout.addWidget(self.play_button)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return group
    
    def create_visualization_panel(self):
        """Cria o painel de visualizações"""
        tabs = QTabWidget()
        
        # Aba do espectro original
        self.original_spectrum_tab = self.create_spectrum_tab("original")
        tabs.addTab(self.original_spectrum_tab, "Espectro Original")
        
        # Aba do espectro filtrado
        self.filtered_spectrum_tab = self.create_spectrum_tab("filtered")
        tabs.addTab(self.filtered_spectrum_tab, "Espectro Filtrado")
        
        # Aba do sinal processado
        self.processed_signal_tab = self.create_signal_tab()
        tabs.addTab(self.processed_signal_tab, "Sinal Processado")
        
        return tabs
    
    def create_spectrum_tab(self, spectrum_type):
        """Cria uma aba de espectro"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Canvas para o espectro
        canvas = MplCanvas()
        canvas.setMinimumHeight(300)
        
        # Armazenar referência
        if spectrum_type == "original":
            self.original_spectrum_canvas = canvas
        else:
            self.filtered_spectrum_canvas = canvas
            
        layout.addWidget(canvas)
        
        # Informações
        info_label = QLabel("Clique e arraste para selecionar bandas de frequência")
        info_label.setStyleSheet("color: blue; font-size: 10pt;")
        layout.addWidget(info_label)
        
        return widget
    
    def create_signal_tab(self):
        """Cria a aba do sinal processado"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Canvas para o sinal
        self.processed_signal_canvas = MplCanvas()
        self.processed_signal_canvas.setMinimumHeight(300)
        layout.addWidget(self.processed_signal_canvas)
        
        # Informações do processamento
        self.processing_info_label = QLabel("Informações do processamento aparecerão aqui")
        self.processing_info_label.setStyleSheet("color: blue; font-size: 10pt;")
        layout.addWidget(self.processing_info_label)
        
        return widget
    
    def create_status_bar(self):
        """Cria a barra de status"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return widget
    
    def on_select_file(self):
        """Manipula a seleção de arquivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Dados",
            "",
            "Arquivos PKL (*.pkl);;Todos os Arquivos (*)"
        )
        
        if file_path:
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(filename)
            self.file_label.setStyleSheet("color: black;")
            
            # Habilitar controles
            self.activate_selection_button.setEnabled(True)
            self.process_button.setEnabled(True)
            
            log_info(f"Arquivo selecionado para Ultra-Hear: {file_path}")
            self.audioFileSelected.emit(file_path)
    
    def on_activate_selection(self):
        """Ativa/desativa a seleção interativa de bandas"""
        if not self.band_selector:
            self.band_selector = FrequencyBandSelector(
                self.original_spectrum_canvas,
                self.on_bands_updated
            )
        
        if not self.band_selector.active:
            self.band_selector.activate()
            self.activate_selection_button.setText("Desativar Seleção")
            self.status_label.setText("Seleção ativa - Clique e arraste no espectro")
        else:
            self.band_selector.deactivate()
            self.activate_selection_button.setText("Ativar Seleção")
            self.status_label.setText("Seleção desativada")
    
    def on_clear_bands(self):
        """Limpa as bandas selecionadas"""
        if self.band_selector:
            self.band_selector.clear_bands()
        self.frequency_bands.clear()
        self.bands_text.clear()
        self.status_label.setText("Bandas limpas")
    
    def on_bands_updated(self, bands):
        """Atualiza a lista de bandas selecionadas"""
        self.frequency_bands = bands
        
        # Atualizar texto
        bands_text = []
        for i, (fmin, fmax) in enumerate(bands):
            bands_text.append(f"Banda {i+1}: {fmin:.1f} - {fmax:.1f} Hz")
        
        self.bands_text.setPlainText("\n".join(bands_text))
        self.status_label.setText(f"{len(bands)} banda(s) selecionada(s)")
    
    def on_transpose_changed(self, state):
        """Manipula a mudança no estado da transposição"""
        is_enabled = state == Qt.Checked
        
        self.transpose_method.setEnabled(is_enabled)
        self.division_factor.setEnabled(is_enabled)
        self.target_freq.setEnabled(is_enabled)
        self.maintain_speed.setEnabled(is_enabled)
    
    def on_process_audio(self):
        """Inicia o processamento do áudio"""
        if not self.current_file:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro.")
            return
        
        # Coletar parâmetros
        params = self.get_processing_parameters()
        
        log_info("Iniciando processamento Ultra-Hear")
        log_debug(f"Parâmetros: {params}")
        
        # Mostrar progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.status_label.setText("Processando...")
        
        # Emitir sinal para processamento
        self.processUltrasonicRequested.emit(params)
    
    def on_play_audio(self):
        """Reproduz o áudio processado"""
        if not self.processed_audio_path:
            QMessageBox.warning(self, "Aviso", "Processe o áudio primeiro.")
            return
        
        log_info("Reproduzindo áudio processado")
        self.playProcessedAudioRequested.emit()
    
    def get_processing_parameters(self):
        """Coleta todos os parâmetros de processamento"""
        params = {
            'file_path': self.current_file,
            
            # Filtros de frequência
            'frequency_bands': self.frequency_bands.copy(),
            'freq_min': self.freq_min_spinbox.value(),
            'freq_max': self.freq_max_spinbox.value(),
            'selection_mode': self.selection_mode.currentText(),
            
            # Transposição
            'enable_transpose': self.enable_transpose.isChecked(),
            'transpose_method': self.transpose_method.currentText(),
            'division_factor': self.division_factor.value(),
            'target_freq': self.target_freq.value(),
            'maintain_speed': self.maintain_speed.isChecked(),
            
            # Amplitude
            'amplitude_min': self.amplitude_min.value(),
            'amplitude_max': self.amplitude_max.value(),
            'normalization_type': self.normalization_type.currentText(),
            'gain_db': self.gain_db.value(),
        }
        
        return params
    
    def on_data_loaded(self, data):
        """Manipula o carregamento de dados"""
        self.current_data = data
        log_info("Dados carregados no painel Ultra-Hear")
        
        # Atualizar visualizações se necessário
        if 'demodulated' in data and 't' in data:
            self.show_original_spectrum(data)
    
    def show_original_spectrum(self, data):
        """Mostra o espectro original"""
        try:
            # Calcular espectro
            from scipy.fft import fft, fftfreq
            
            signal = data['demodulated']
            fs = data.get('sample_frequency_effective', 44100)
            
            # FFT
            n = len(signal)
            freqs = fftfreq(n, 1/fs)[:n//2]
            spectrum = np.abs(fft(signal))[:n//2]
            
            # Remover frequência zero para evitar problemas com log
            freqs = freqs[1:]
            spectrum = spectrum[1:]
            
            # Converter para dB
            spectrum_db = 20 * np.log10(spectrum + 1e-12)
            
            # Plotar
            self.original_spectrum_canvas.axes.clear()
            self.original_spectrum_canvas.axes.semilogx(freqs, spectrum_db)
            self.original_spectrum_canvas.axes.set_xlabel('Frequência (Hz) - Escala Log')
            self.original_spectrum_canvas.axes.set_ylabel('Amplitude (dB)')
            self.original_spectrum_canvas.axes.set_title('Espectro Original')
            self.original_spectrum_canvas.axes.grid(True, which="both", ls="-", alpha=0.3)
            self.original_spectrum_canvas.draw()
            
            log_debug("Espectro original exibido com escala logarítmica")
            
        except Exception as e:
            log_error(f"Erro ao exibir espectro original: {str(e)}")
    
    def on_processing_finished(self, result):
        """Manipula o fim do processamento"""
        self.progress_bar.setVisible(False)
        
        if result.get('success', False):
            self.processed_audio_path = result.get('audio_path')
            self.play_button.setEnabled(True)
            self.status_label.setText("Processamento concluído!")
            
            # Atualizar visualizações
            if 'processed_signal' in result:
                self.show_processed_signal(result)
            if 'filtered_spectrum' in result:
                self.show_filtered_spectrum(result)
                
            # Mostrar informações
            info = self.format_processing_info(result)
            self.processing_info_label.setText(info)
            
        else:
            error_msg = result.get('error', 'Erro desconhecido')
            self.status_label.setText(f"Erro: {error_msg}")
            QMessageBox.critical(self, "Erro", f"Erro no processamento:\n{error_msg}")
    
    def show_processed_signal(self, result):
        """Mostra o sinal processado"""
        try:
            signal = result['processed_signal']
            t = result.get('time_axis', np.arange(len(signal)) / 44100)
            
            self.processed_signal_canvas.axes.clear()
            self.processed_signal_canvas.axes.plot(t, signal)
            self.processed_signal_canvas.axes.set_xlabel('Tempo (s)')
            self.processed_signal_canvas.axes.set_ylabel('Amplitude')
            self.processed_signal_canvas.axes.set_title('Sinal Processado (Ultra-Hear)')
            self.processed_signal_canvas.axes.grid(True)
            self.processed_signal_canvas.draw()
            
        except Exception as e:
            log_error(f"Erro ao exibir sinal processado: {str(e)}")
    
    def show_filtered_spectrum(self, result):
        """Mostra o espectro filtrado"""
        try:
            freqs = result['filtered_spectrum']['frequencies']
            spectrum = result['filtered_spectrum']['magnitudes']
            
            # Remover frequências zero ou negativas para log
            mask = freqs > 0
            freqs = freqs[mask]
            spectrum = spectrum[mask]
            
            self.filtered_spectrum_canvas.axes.clear()
            self.filtered_spectrum_canvas.axes.semilogx(freqs, spectrum)
            self.filtered_spectrum_canvas.axes.set_xlabel('Frequência (Hz) - Escala Log')
            self.filtered_spectrum_canvas.axes.set_ylabel('Amplitude (dB)')
            self.filtered_spectrum_canvas.axes.set_title('Espectro Filtrado')
            self.filtered_spectrum_canvas.axes.grid(True, which="both", ls="-", alpha=0.3)
            
            # Destacar bandas selecionadas
            for fmin, fmax in self.frequency_bands:
                if fmin > 0 and fmax > 0:  # Verificar se as frequências são válidas para log
                    self.filtered_spectrum_canvas.axes.axvspan(
                        fmin, fmax, alpha=0.3, color='yellow', label='Banda Selecionada'
                    )
            
            self.filtered_spectrum_canvas.draw()
            
        except Exception as e:
            log_error(f"Erro ao exibir espectro filtrado: {str(e)}")
    
    def format_processing_info(self, result):
        """Formata as informações do processamento"""
        info_lines = []
        
        if 'original_freq_range' in result:
            freq_range = result['original_freq_range']
            info_lines.append(f"Faixa Original: {freq_range[0]:.1f} - {freq_range[1]:.1f} Hz")
        
        if 'transposed_freq_range' in result:
            freq_range = result['transposed_freq_range']
            info_lines.append(f"Faixa Transposta: {freq_range[0]:.1f} - {freq_range[1]:.1f} Hz")
        
        if 'processing_time' in result:
            info_lines.append(f"Tempo de Processamento: {result['processing_time']:.2f}s")
        
        if 'bands_applied' in result:
            info_lines.append(f"Bandas Aplicadas: {len(result['bands_applied'])}")
        
        return "\n".join(info_lines)
    
    def on_error(self, error_message):
        """Manipula erros"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Erro: {error_message}")
        log_error(f"Erro no Ultra-Hear: {error_message}")