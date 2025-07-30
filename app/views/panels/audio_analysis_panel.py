"""
Painel para análise dedicada de áudio
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTabWidget, QGroupBox, QFileDialog,
                             QTextEdit, QMessageBox, QFormLayout, QComboBox, 
                             QDoubleSpinBox, QSpinBox, QCheckBox)
from PyQt5.QtCore import pyqtSignal, Qt
import os
import numpy as np

from app.views.widgets.canvas import MplCanvas
import app.utils.log as log

class AudioAnalysisPanel(QWidget):
    """Painel dedicado para análise de áudio"""
    
    # Sinais
    audioFileSelected = pyqtSignal(str)  # Arquivo de áudio selecionado
    generateAudioRequested = pyqtSignal()  # Solicitação de geração de áudio
    playAudioRequested = pyqtSignal()  # Solicitação de reprodução
    
    def __init__(self, parent=None):
        """Inicializa o painel de análise de áudio"""
        super().__init__(parent)
        self.current_file = None
        self.current_audio_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Seção de controle de arquivo
        file_group = self.create_file_control_group()
        layout.addWidget(file_group)
        
        # Seção de controles de áudio
        audio_group = self.create_audio_control_group()
        layout.addWidget(audio_group)
        
        # Área principal com abas de visualização
        self.tabs_widget = self.create_visualization_tabs()
        layout.addWidget(self.tabs_widget)
        
        # Status e metadados
        info_group = self.create_info_group()
        layout.addWidget(info_group)
    
    def create_file_control_group(self):
        """Cria o grupo de controles de arquivo"""
        group = QGroupBox("Arquivo de Dados")
        layout = QVBoxLayout(group)
        
        # Layout horizontal para controles
        controls_layout = QHBoxLayout()
        
        # Botão para selecionar arquivo
        self.select_file_button = QPushButton("Selecionar Arquivo")
        self.select_file_button.clicked.connect(self.on_select_file)
        controls_layout.addWidget(self.select_file_button)
        
        # Label para mostrar arquivo selecionado
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setStyleSheet("color: gray; font-style: italic;")
        controls_layout.addWidget(self.file_label)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        return group
    
    def create_audio_control_group(self):
        """Cria o grupo de controles de áudio"""
        group = QGroupBox("Controles de Áudio")
        layout = QHBoxLayout(group)
        
        # Botão para gerar áudio
        self.generate_button = QPushButton("Gerar WAV")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self.on_generate_audio)
        layout.addWidget(self.generate_button)
        
        # Botão para reproduzir áudio
        self.play_button = QPushButton("Reproduzir")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.on_play_audio)
        layout.addWidget(self.play_button)
        
        # Status do áudio
        self.audio_status_label = QLabel("Nenhum áudio gerado")
        self.audio_status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.audio_status_label)
        
        layout.addStretch()
        
        return group
    
    def create_visualization_tabs(self):
        """Cria as abas de visualização"""
        tabs = QTabWidget()
        
        # Aba do sinal demodulado
        self.signal_tab = self.create_signal_tab()
        tabs.addTab(self.signal_tab, "Sinal Demodulado")
        
        # Aba do espectro
        self.spectrum_tab = self.create_spectrum_tab()
        tabs.addTab(self.spectrum_tab, "Espectro")
        
        # Aba de filtros (para implementação futura)
        self.filters_tab = self.create_filters_tab()
        tabs.addTab(self.filters_tab, "Filtros")
        
        # Aba de amplitude (para implementação futura)
        self.amplitude_tab = self.create_amplitude_tab()
        tabs.addTab(self.amplitude_tab, "Controle de Amplitude")
        
        return tabs
    
    def create_signal_tab(self):
        """Cria a aba do sinal demodulado"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Canvas para o sinal
        self.signal_canvas = MplCanvas()
        self.signal_canvas.setMinimumHeight(300)
        layout.addWidget(self.signal_canvas)
        
        # Informações do sinal
        info_layout = QHBoxLayout()
        self.signal_info_label = QLabel("Informações do sinal aparecerão aqui")
        self.signal_info_label.setStyleSheet("color: blue; font-size: 10pt;")
        info_layout.addWidget(self.signal_info_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        return widget
    
    def create_spectrum_tab(self):
        """Cria a aba do espectro"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Canvas para o espectro
        self.spectrum_canvas = MplCanvas()
        self.spectrum_canvas.setMinimumHeight(300)
        layout.addWidget(self.spectrum_canvas)
        
        # Informações do espectro
        info_layout = QHBoxLayout()
        self.spectrum_info_label = QLabel("Informações do espectro aparecerão aqui")
        self.spectrum_info_label.setStyleSheet("color: blue; font-size: 10pt;")
        info_layout.addWidget(self.spectrum_info_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        return widget
    
    def create_filters_tab(self):
        """Cria a aba de filtros avançados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de filtros de espectro
        spectrum_filter_group = QGroupBox("Filtros de Espectro")
        spectrum_layout = QFormLayout(spectrum_filter_group)
        
        # Botão para ativar seleção interativa
        self.activate_spectrum_selection_button = QPushButton("Ativar Seleção no Espectro")
        self.activate_spectrum_selection_button.setEnabled(False)
        spectrum_layout.addRow(self.activate_spectrum_selection_button)
        
        # Lista de bandas selecionadas
        self.spectrum_bands_text = QTextEdit()
        self.spectrum_bands_text.setMaximumHeight(100)
        self.spectrum_bands_text.setReadOnly(True)
        self.spectrum_bands_text.setPlaceholderText("Bandas selecionadas no espectro aparecerão aqui...")
        spectrum_layout.addRow("Bandas:", self.spectrum_bands_text)
        
        # Botões de controle
        filter_controls = QHBoxLayout()
        self.apply_spectrum_filter_button = QPushButton("Aplicar Filtro")
        self.apply_spectrum_filter_button.setEnabled(False)
        self.clear_spectrum_bands_button = QPushButton("Limpar Bandas")
        filter_controls.addWidget(self.apply_spectrum_filter_button)
        filter_controls.addWidget(self.clear_spectrum_bands_button)
        spectrum_layout.addRow(filter_controls)
        
        layout.addWidget(spectrum_filter_group)
        
        # Grupo de filtros tradicionais
        traditional_filter_group = QGroupBox("Filtros Tradicionais")
        traditional_layout = QFormLayout(traditional_filter_group)
        
        # Tipo de filtro
        self.filter_type = QComboBox()
        self.filter_type.addItems([
            "Passa-Baixa",
            "Passa-Alta", 
            "Passa-Banda",
            "Rejeita-Banda (Notch)"
        ])
        traditional_layout.addRow("Tipo:", self.filter_type)
        
        # Frequência de corte 1
        self.cutoff_freq1 = QDoubleSpinBox()
        self.cutoff_freq1.setRange(1, 100000)
        self.cutoff_freq1.setValue(1000)
        self.cutoff_freq1.setSuffix(" Hz")
        traditional_layout.addRow("Freq. Corte 1:", self.cutoff_freq1)
        
        # Frequência de corte 2 (para passa-banda e notch)
        self.cutoff_freq2 = QDoubleSpinBox()
        self.cutoff_freq2.setRange(1, 100000)
        self.cutoff_freq2.setValue(5000)
        self.cutoff_freq2.setSuffix(" Hz")
        self.cutoff_freq2.setEnabled(False)
        traditional_layout.addRow("Freq. Corte 2:", self.cutoff_freq2)
        
        # Ordem do filtro
        self.filter_order = QSpinBox()
        self.filter_order.setRange(1, 10)
        self.filter_order.setValue(4)
        traditional_layout.addRow("Ordem:", self.filter_order)
        
        # Conectar mudança de tipo de filtro
        self.filter_type.currentTextChanged.connect(self.on_filter_type_changed)
        
        # Botão aplicar filtro tradicional
        self.apply_traditional_filter_button = QPushButton("Aplicar Filtro Tradicional")
        self.apply_traditional_filter_button.setEnabled(False)
        traditional_layout.addRow(self.apply_traditional_filter_button)
        
        layout.addWidget(traditional_filter_group)
        
        layout.addStretch()
        
        return widget
    
    def create_amplitude_tab(self):
        """Cria a aba de controle de amplitude (preparação para implementação futura)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder para implementação futura
        placeholder = QLabel("📊 Controle de Amplitude\n\n"
                           "Esta seção será implementada nas próximas versões:\n"
                           "• Seleção de faixa de amplitude\n"
                           "• Saturação seletiva vs normalização global\n"
                           "• Compressão dinâmica\n"
                           "• Análise de picos e RMS")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 12pt; padding: 50px;")
        layout.addWidget(placeholder)
        
        return widget
    
    def create_info_group(self):
        """Cria o grupo de informações e metadados"""
        group = QGroupBox("Informações do Arquivo")
        layout = QVBoxLayout(group)
        
        # Área de texto para metadados
        self.metadata_text = QTextEdit()
        self.metadata_text.setMaximumHeight(100)
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setPlainText("Carregue um arquivo para ver os metadados")
        layout.addWidget(self.metadata_text)
        
        return group
    
    def on_select_file(self):
        """Manipula a seleção de arquivo"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Dados Demodulados",
            "data/Dados para treinamento",
            "Arquivos Pickle (*.pkl);;Todos os arquivos (*)"
        )
        
        if file_path:
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(f"Arquivo: {filename}")
            self.file_label.setStyleSheet("color: black; font-weight: bold;")
            
            # Habilitar botão de gerar áudio
            self.generate_button.setEnabled(True)
            
            # Emitir sinal para carregar arquivo
            log.info(f"Arquivo selecionado para análise de áudio: {file_path}")
            self.audioFileSelected.emit(file_path)
    
    def on_generate_audio(self):
        """Manipula a solicitação de geração de áudio"""
        if not self.current_file:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro")
            return
            
        log.info("Solicitando geração de áudio WAV")
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Gerando...")
        self.generateAudioRequested.emit()
    
    def on_play_audio(self):
        """Manipula a solicitação de reprodução de áudio"""
        if not self.current_audio_path:
            QMessageBox.warning(self, "Aviso", "Gere um arquivo de áudio primeiro")
            return
            
        log.info("Solicitando reprodução de arquivo de áudio")
        self.playAudioRequested.emit()
    
    def on_audio_loaded(self, data):
        """Manipula o carregamento de dados de áudio"""
        log.info("Dados de áudio carregados no painel")
        
        # Atualizar metadados
        self.update_metadata_display(data)
        
        # Mostrar sinal demodulado
        self.show_demodulated_signal(data)
        
        # Calcular e mostrar espectro será feito pelo controlador
    
    def on_audio_generated(self, audio_path):
        """Manipula a geração de arquivo de áudio"""
        self.current_audio_path = audio_path
        filename = os.path.basename(audio_path)
        
        # Atualizar interface
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Gerar WAV")
        self.play_button.setEnabled(True)
        self.audio_status_label.setText(f"Áudio gerado: {filename}")
        self.audio_status_label.setStyleSheet("color: green; font-weight: bold;")
        
        # Mostrar mensagem de sucesso
        QMessageBox.information(
            self, 
            "Áudio Gerado", 
            f"Arquivo de áudio salvo com sucesso:\n{filename}"
        )
    
    def on_audio_error(self, error_message):
        """Manipula erros de áudio"""
        log.error(f"Erro de áudio: {error_message}")
        
        # Restaurar interface
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Gerar WAV")
        
        # Mostrar erro
        QMessageBox.critical(self, "Erro", error_message)
    
    def show_demodulated_signal(self, data):
        """Exibe o sinal demodulado"""
        try:
            if 't' not in data or 'demodulated' not in data:
                log.warning("Dados incompletos para exibir sinal")
                return
            
            t = data['t']
            demodulated = data['demodulated']
            
            # Limitar pontos para plotagem
            max_points = 10000
            if len(t) > max_points:
                step = len(t) // max_points
                t_plot = t[::step]
                demod_plot = demodulated[::step]
            else:
                t_plot = t
                demod_plot = demodulated
            
            # Plotar sinal
            self.signal_canvas.axes.clear()
            self.signal_canvas.axes.plot(t_plot, demod_plot, 'b-', linewidth=0.8)
            self.signal_canvas.axes.set_xlabel('Tempo (s)')
            self.signal_canvas.axes.set_ylabel('Fase (rad)')
            self.signal_canvas.axes.set_title('Sinal Demodulado para Análise de Áudio')
            self.signal_canvas.axes.grid(True, alpha=0.3)
            self.signal_canvas.draw()
            
            # Atualizar informações
            duration = t[-1] - t[0]
            sample_rate = len(t) / duration
            self.signal_info_label.setText(
                f"Duração: {duration:.2f}s | Pontos: {len(demodulated):,} | "
                f"Taxa: {sample_rate:.0f} Hz | Min: {np.min(demodulated):.3f} | Max: {np.max(demodulated):.3f}"
            )
            
            log.debug("Sinal demodulado exibido na aba de análise de áudio")
            
        except Exception as e:
            log.error(f"Erro ao exibir sinal demodulado: {str(e)}")
    
    def show_spectrum(self, frequencies, magnitudes):
        """Exibe o espectro do sinal"""
        try:
            # Converter para escala logarítmica
            magnitudes_db = 20 * np.log10(magnitudes + 1e-10)
            
            # Plotar espectro
            self.spectrum_canvas.axes.clear()
            self.spectrum_canvas.axes.semilogx(frequencies, magnitudes_db, 'r-', linewidth=1)
            self.spectrum_canvas.axes.set_xlabel('Frequência (Hz)')
            self.spectrum_canvas.axes.set_ylabel('Amplitude (dB)')
            self.spectrum_canvas.axes.set_title('Espectro do Sinal Demodulado')
            self.spectrum_canvas.axes.grid(True, which='both', alpha=0.3)
            self.spectrum_canvas.axes.set_xlim(10, frequencies[-1])
            self.spectrum_canvas.draw()
            
            # Atualizar informações
            max_freq = frequencies[np.argmax(magnitudes)]
            max_amplitude = np.max(magnitudes_db)
            self.spectrum_info_label.setText(
                f"Freq. Máxima: {max_freq:.1f} Hz | Amplitude Máx: {max_amplitude:.1f} dB | "
                f"Banda: 10 Hz - {frequencies[-1]/1000:.1f} kHz"
            )
            
            log.debug("Espectro exibido na aba de análise de áudio")
            
        except Exception as e:
            log.error(f"Erro ao exibir espectro: {str(e)}")
    
    def update_metadata_display(self, data):
        """Atualiza a exibição de metadados"""
        try:
            if 'metadata' not in data:
                self.metadata_text.setPlainText("Metadados não disponíveis")
                return
            
            metadata = data['metadata']
            metadata_str = ""
            
            # Formatear metadados importantes
            important_keys = ['timestamp', 'sensor_sn', 'test_type', 'material', 
                            'pressure', 'flow', 'distance', 'location']
            
            for key in important_keys:
                if key in metadata:
                    value = metadata[key]
                    if isinstance(value, (int, float)):
                        metadata_str += f"{key}: {value} | "
                    else:
                        metadata_str += f"{key}: {value} | "
            
            # Remover última barra
            metadata_str = metadata_str.rstrip(" | ")
            
            self.metadata_text.setPlainText(metadata_str)
            
        except Exception as e:
            log.error(f"Erro ao atualizar metadados: {str(e)}")
            self.metadata_text.setPlainText("Erro ao carregar metadados")
    
    def clear_displays(self):
        """Limpa todas as visualizações"""
        self.signal_canvas.clear()
        self.spectrum_canvas.clear()
        self.signal_info_label.setText("Informações do sinal aparecerão aqui")
        self.spectrum_info_label.setText("Informações do espectro aparecerão aqui")
        self.metadata_text.setPlainText("Carregue um arquivo para ver os metadados")
    
    def on_filter_type_changed(self, filter_type):
        """Manipula a mudança do tipo de filtro"""
        # Habilitar/desabilitar segunda frequência de corte conforme o tipo
        needs_two_freqs = filter_type in ["Passa-Banda", "Rejeita-Banda (Notch)"]
        self.cutoff_freq2.setEnabled(needs_two_freqs) 