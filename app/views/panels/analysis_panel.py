"""
Módulo com o painel de análise e visualização de dados
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton,
                           QComboBox, QLabel, QFileDialog, QMessageBox, QSplitter,
                           QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout,
                           QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np

from app.views.widgets.canvas import MplCanvas, NavigationToolbarCustom
from app.utils.debug_log import log_debug, log_info, log_warning, log_error

class AnalysisPanel(QWidget):
    """Painel para análise e visualização de dados"""
    
    # Sinais
    fileSelected = pyqtSignal(str)  # Emitido quando um arquivo é selecionado
    demodulateRequested = pyqtSignal()  # Emitido quando o usuário solicita demodulação
    saveDemodulatedRequested = pyqtSignal()  # Emitido quando o usuário solicita salvar dados demodulados
    saveFilteredRequested = pyqtSignal()  # Emitido quando o usuário solicita salvar dados filtrados
    refreshFilesRequested = pyqtSignal()  # Emitido quando o usuário solicita atualização da lista de arquivos
    movingAverageChanged = pyqtSignal(bool, int)  # Emitido quando a configuração de média móvel é alterada
    bandpassFilterChanged = pyqtSignal(bool, float, float, int)  # Emitido quando a configuração do filtro passa-banda é alterada
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de análise
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do painel"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Widget para selecionar arquivo
        file_selection = QHBoxLayout()
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(400)
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        self.load_button = QPushButton("Carregar")
        self.load_button.clicked.connect(self.on_load_clicked)
        self.browse_button = QPushButton("Procurar...")
        self.browse_button.clicked.connect(self.on_browse_clicked)
        
        file_selection.addWidget(QLabel("Arquivo:"))
        file_selection.addWidget(self.file_combo)
        file_selection.addWidget(self.refresh_button)
        file_selection.addWidget(self.browse_button)
        file_selection.addWidget(self.load_button)
        
        layout.addLayout(file_selection)

        # Área de metadados
        metadata_group = QGroupBox("Metadados do Arquivo")
        metadata_layout = QVBoxLayout()
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setMaximumHeight(150)
        self.metadata_text.setStyleSheet("font-family: monospace;")
        metadata_layout.addWidget(self.metadata_text)
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Layout para os controles de processamento
        processing_layout = QHBoxLayout()
        
        # Grupo para média móvel
        moving_avg_group = QGroupBox("Média Móvel")
        moving_avg_layout = QFormLayout()
        
        self.moving_avg_checkbox = QCheckBox("Ativar")
        self.window_size_spinbox = QSpinBox()
        self.window_size_spinbox.setRange(2, 101)
        self.window_size_spinbox.setSingleStep(1)
        self.window_size_spinbox.setValue(4)
        self.window_size_spinbox.setEnabled(False)
        
        # Botão para aplicar manualmente a média móvel
        self.apply_moving_avg_button = QPushButton("Aplicar Média Móvel")
        self.apply_moving_avg_button.clicked.connect(self.on_apply_moving_avg_clicked)
        self.apply_moving_avg_button.setEnabled(False)
        
        moving_avg_layout.addRow(self.moving_avg_checkbox)
        moving_avg_layout.addRow("Tamanho da Janela:", self.window_size_spinbox)
        moving_avg_layout.addRow(self.apply_moving_avg_button)
        moving_avg_group.setLayout(moving_avg_layout)
        
        # Grupo para filtro passa-banda
        bandpass_group = QGroupBox("Filtro Passa-Banda")
        bandpass_layout = QFormLayout()
        
        self.bandpass_checkbox = QCheckBox("Ativar")
        self.low_freq_spinbox = QDoubleSpinBox()
        self.low_freq_spinbox.setRange(0.1, 250_000.0)
        self.low_freq_spinbox.setSingleStep(10.0)
        self.low_freq_spinbox.setValue(20_000.0)
        self.low_freq_spinbox.setSuffix(" Hz")
        self.low_freq_spinbox.setEnabled(False)
        
        self.high_freq_spinbox = QDoubleSpinBox()
        self.high_freq_spinbox.setRange(0.1, 1_000_000.0)
        self.high_freq_spinbox.setSingleStep(100.0)
        self.high_freq_spinbox.setValue(250_000.0)
        self.high_freq_spinbox.setSuffix(" Hz")
        self.high_freq_spinbox.setEnabled(False)
        
        self.order_spinbox = QSpinBox()
        self.order_spinbox.setRange(1, 10)
        self.order_spinbox.setValue(4)
        self.order_spinbox.setEnabled(False)
        
        # Botão para aplicar manualmente o filtro
        self.apply_filter_button = QPushButton("Aplicar Filtro")
        self.apply_filter_button.clicked.connect(self.on_apply_filter_clicked)
        self.apply_filter_button.setEnabled(False)
        
        bandpass_layout.addRow(self.bandpass_checkbox)
        bandpass_layout.addRow("Frequência Inferior:", self.low_freq_spinbox)
        bandpass_layout.addRow("Frequência Superior:", self.high_freq_spinbox)
        bandpass_layout.addRow("Ordem do Filtro:", self.order_spinbox)
        bandpass_layout.addRow(self.apply_filter_button)
        bandpass_group.setLayout(bandpass_layout)
        
        # Adicionar grupos ao layout de processamento
        processing_layout.addWidget(moving_avg_group)
        processing_layout.addWidget(bandpass_group)
        processing_layout.addStretch()
        
        # Conectar sinais
        self.moving_avg_checkbox.stateChanged.connect(self.on_moving_average_changed)
        self.window_size_spinbox.valueChanged.connect(self.on_window_size_changed)
        
        self.bandpass_checkbox.stateChanged.connect(self.on_bandpass_filter_changed)
        self.low_freq_spinbox.valueChanged.connect(self.on_bandpass_params_changed)
        self.high_freq_spinbox.valueChanged.connect(self.on_bandpass_params_changed)
        self.order_spinbox.valueChanged.connect(self.on_bandpass_params_changed)
        
        layout.addLayout(processing_layout)
        
        # TabWidget para diferentes visualizações
        self.analysis_tabs = QTabWidget()
        
        # Aba de dados brutos
        raw_tab = QWidget()
        raw_layout = QVBoxLayout(raw_tab)
        self.raw_canvas = MplCanvas(self, width=9, height=5)
        self.raw_toolbar = NavigationToolbarCustom(self.raw_canvas, self)
        raw_layout.addWidget(self.raw_toolbar)
        raw_layout.addWidget(self.raw_canvas)
        
        # Aba de fit de elipse
        ellipse_tab = QWidget()
        ellipse_layout = QVBoxLayout(ellipse_tab)
        self.ellipse_canvas = MplCanvas(self, width=9, height=5)
        self.ellipse_toolbar = NavigationToolbarCustom(self.ellipse_canvas, self)
        self.demodulate_button = QPushButton("Demodular Sinal")
        self.demodulate_button.clicked.connect(self.on_demodulate_clicked)
        
        ellipse_layout.addWidget(self.ellipse_toolbar)
        ellipse_layout.addWidget(self.ellipse_canvas)
        ellipse_layout.addWidget(self.demodulate_button)
        
        # Aba de sinal demodulado
        demod_tab = QWidget()
        demod_layout = QVBoxLayout(demod_tab)
        self.demod_canvas = MplCanvas(self, width=9, height=5)
        self.demod_toolbar = NavigationToolbarCustom(self.demod_canvas, self)
        demod_layout.addWidget(self.demod_toolbar)
        demod_layout.addWidget(self.demod_canvas)
        
        # Aba de sinal filtrado
        filtered_tab = QWidget()
        filtered_layout = QVBoxLayout(filtered_tab)
        self.filtered_canvas = MplCanvas(self, width=9, height=5)
        self.filtered_toolbar = NavigationToolbarCustom(self.filtered_canvas, self)
        
        # Adicionar botão para salvar o sinal filtrado
        self.save_filtered_button = QPushButton("Salvar Sinal Filtrado")
        self.save_filtered_button.setEnabled(False)
        self.save_filtered_button.clicked.connect(self.on_save_filtered_clicked)
        
        filtered_layout.addWidget(self.filtered_toolbar)
        filtered_layout.addWidget(self.filtered_canvas)
        filtered_layout.addWidget(self.save_filtered_button)
        
        # Aba de espectro
        spectrum_tab = QWidget()
        spectrum_layout = QVBoxLayout(spectrum_tab)
        self.spectrum_canvas = MplCanvas(self, width=9, height=5)
        self.spectrum_toolbar = NavigationToolbarCustom(self.spectrum_canvas, self)
        spectrum_layout.addWidget(self.spectrum_toolbar)
        spectrum_layout.addWidget(self.spectrum_canvas)
        
        # Adicionar as sub-abas ao TabWidget de análise
        self.analysis_tabs.addTab(raw_tab, "Dados Brutos")
        self.analysis_tabs.addTab(ellipse_tab, "Fit da Elipse")
        self.analysis_tabs.addTab(demod_tab, "Sinal Demodulado")
        self.analysis_tabs.addTab(filtered_tab, "Sinal Filtrado")
        self.analysis_tabs.addTab(spectrum_tab, "Espectro")
        
        layout.addWidget(self.analysis_tabs)
        
    def on_moving_average_changed(self, state):
        """
        Manipula a mudança no estado da caixa de seleção de média móvel
        
        Args:
            state: Estado da caixa de seleção
        """
        is_checked = state == Qt.Checked
        # Atualizar a interface
        self.window_size_spinbox.setEnabled(is_checked)
        self.apply_moving_avg_button.setEnabled(is_checked)
        
        # Mostrar mensagem na barra de status
        if is_checked:
            log_info(f"Média móvel configurada com janela de {self.window_size_spinbox.value()}")
        else:
            log_info("Média móvel desativada")
        
        # Emitir sinal para aplicar ou remover a média móvel
        # (comentado para aplicar somente ao clicar no botão)
        # self.movingAverageChanged.emit(is_checked, self.window_size_spinbox.value())
        
    def on_window_size_changed(self, value):
        """
        Manipula a mudança no tamanho da janela de média móvel
        
        Args:
            value: Novo valor da janela
        """
        if self.moving_avg_checkbox.isChecked():
            log_info(f"Tamanho da janela de média móvel alterado para {value}")
            # Emitir sinal (comentado para aplicar somente ao clicar no botão)
            # self.movingAverageChanged.emit(True, value)
    
    def on_bandpass_filter_changed(self, state):
        """
        Manipula a mudança no estado da caixa de seleção do filtro passa-banda
        
        Args:
            state: Estado da caixa de seleção
        """
        is_checked = state == Qt.Checked
        # Atualizar a interface
        self.low_freq_spinbox.setEnabled(is_checked)
        self.high_freq_spinbox.setEnabled(is_checked)
        self.order_spinbox.setEnabled(is_checked)
        self.apply_filter_button.setEnabled(is_checked)
        
        # Mostrar mensagem na barra de status
        if is_checked:
            low_freq = self.low_freq_spinbox.value()
            high_freq = self.high_freq_spinbox.value()
            order = self.order_spinbox.value()
            log_info(f"Filtro passa-banda configurado ({low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order})")
        else:
            log_info("Filtro passa-banda desativado")
            # Quando o filtro é desativado, emitir sinal com enabled=False para restaurar o sinal original
            self.bandpassFilterChanged.emit(
                False, 
                self.low_freq_spinbox.value(),
                self.high_freq_spinbox.value(),
                self.order_spinbox.value()
            )
        
        # NÃO emitir o sinal até que o botão seja clicado quando estiver ativando
        # if is_checked:
        #     self.bandpassFilterChanged.emit(
        #         is_checked, 
        #         self.low_freq_spinbox.value(),
        #         self.high_freq_spinbox.value(),
        #         self.order_spinbox.value()
        #     )
        
    def on_bandpass_params_changed(self):
        """Manipula a mudança nos parâmetros do filtro passa-banda"""
        if self.bandpass_checkbox.isChecked():
            low_freq = self.low_freq_spinbox.value()
            high_freq = self.high_freq_spinbox.value()
            order = self.order_spinbox.value()
            
            log_info(f"Parâmetros do filtro passa-banda alterados: {low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order}")
            
            # NÃO emitir o sinal até que o botão seja clicado
            # self.bandpassFilterChanged.emit(True, low_freq, high_freq, order)
            
    def update_file_list(self, files):
        """
        Atualiza a lista de arquivos disponíveis
        
        Args:
            files: Lista de arquivos disponíveis
        """
        self.file_combo.clear()
        for file in files:
            self.file_combo.addItem(file)
            
    def on_refresh_clicked(self):
        """Solicita atualização da lista de arquivos"""
        log_debug("Solicitando atualização da lista de arquivos")
        self.refreshFilesRequested.emit()
        
    def on_browse_clicked(self):
        """Abre um diálogo para selecionar arquivo manualmente"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo de dados",
            "",
            "Arquivos pickle (*.pkl)"
        )
        
        if file_path:
            log_info(f"Arquivo selecionado: {file_path}")
            # Adicionar o arquivo ao combo box, se já não estiver lá
            index = self.file_combo.findText(file_path)
            if index == -1:
                self.file_combo.addItem(file_path)
                self.file_combo.setCurrentIndex(self.file_combo.count() - 1)
            else:
                self.file_combo.setCurrentIndex(index)
            
            # Carregar o arquivo selecionado
            self.on_load_clicked()
            
    def on_load_clicked(self):
        """Solicita carregamento do arquivo selecionado"""
        if self.file_combo.count() == 0:
            return
        
        filename = self.file_combo.currentText()
        log_info(f"Carregando arquivo: {filename}")
        self.fileSelected.emit(filename)
        
    def on_demodulate_clicked(self):
        """Solicita demodulação dos dados"""
        log_info("Solicitando demodulação do sinal")
        self.demodulateRequested.emit()
    
    def on_demodulate(self):
        """Método para demodular dados a partir da barra de ferramentas"""
        self.on_demodulate_clicked()
    
    def on_select_file(self):
        """Método para selecionar arquivo a partir da barra de ferramentas"""
        self.on_browse_clicked()
    
    def on_refresh_files(self):
        """Método para atualizar lista de arquivos a partir da barra de ferramentas"""
        self.on_refresh_clicked()
        
    def clear_plots(self):
        """Limpa todos os gráficos"""
        self.raw_canvas.clear()
        self.ellipse_canvas.clear()
        self.demod_canvas.clear()
        self.filtered_canvas.clear()
        self.spectrum_canvas.clear()
        
    def show_message(self, text, canvas):
        """
        Mostra mensagem em um canvas
        
        Args:
            text: Texto da mensagem
            canvas: Canvas onde a mensagem será exibida
        """
        canvas.clear()
        canvas.add_text(text, fontsize=12)
        
    def show_raw_data(self, t, waveforms, channels):
        """
        Exibe os dados brutos
        
        Args:
            t: Vetor de tempo
            waveforms: Array de formas de onda
            channels: Lista com identificadores dos canais
        """
        log_debug(f"show_raw_data: t={len(t)}, waveforms={waveforms.shape}, channels={channels}")
        try:
            # Verificar se a média móvel está ativada para adicionar ao título
            titulo = 'Dados Brutos'
            if self.moving_avg_checkbox.isChecked():
                titulo += f' (com Média Móvel: {self.window_size_spinbox.value()})'
                
            self.raw_canvas.plot_timeseries(
                t, waveforms, channels=channels,
                title=titulo
            )
            # Garantir que o gráfico seja atualizado
            self.raw_canvas.draw()
            log_debug("Gráfico de dados brutos atualizado com sucesso")
            # Certificar-se que a aba está visível
            self.analysis_tabs.setCurrentIndex(0)
        except Exception as e:
            log_error(f"Erro ao plotar dados brutos: {e}")
        
    def show_ellipse(self, waveforms, ellipse_params=None):
        """
        Exibe o gráfico Lissajous e a elipse ajustada
        
        Args:
            waveforms: Array de formas de onda [canais, amostras]
            ellipse_params: Parâmetros da elipse ajustada (opcional)
        """
        log_debug(f"show_ellipse: waveforms={waveforms.shape}, ellipse_params={ellipse_params is not None}")
        try:
            # Limitar número de pontos para plot
            max_points = 5000
            if waveforms.shape[1] > max_points:
                step = waveforms.shape[1] // max_points
                waveforms_plot = waveforms[:, ::step]
            else:
                waveforms_plot = waveforms
                
            # Preparar título
            titulo = 'Figura de Lissajous'
            if self.moving_avg_checkbox.isChecked():
                titulo += f' (com Média Móvel: {self.window_size_spinbox.value()})'
                
            # Mostrar gráfico Lissajous
            self.ellipse_canvas.plot_scatter(
                waveforms_plot[0], waveforms_plot[1],
                xlabel='Canal 1', ylabel='Canal 2', 
                title=titulo
            )
            
            # Se temos parâmetros da elipse, plotar a elipse ajustada
            if ellipse_params is not None:
                self.ellipse_canvas.plot_ellipse(
                    fitted_params=ellipse_params,
                    plot_params=True
                )
                log_debug("Elipse ajustada plotada com sucesso")
        except Exception as e:
            log_error(f"Erro ao plotar elipse: {e}")
            
    def show_demodulated(self, t, demodulated):
        """
        Exibe o sinal demodulado
        
        Args:
            t: Vetor de tempo
            demodulated: Sinal demodulado
        """
        log_debug(f"show_demodulated: t={len(t)}, demodulated={len(demodulated)}")
        try:
            # Limitar número de pontos para plotagem
            max_points = 10000
            if len(t) > max_points:
                step = len(t) // max_points
                t_plot = t[::step]
                demod_plot = demodulated[::step]
            else:
                t_plot = t
                demod_plot = demodulated
            
            # Preparar título
            titulo = 'Sinal Demodulado'
            if self.moving_avg_checkbox.isChecked():
                titulo += f' (com Média Móvel: {self.window_size_spinbox.value()})'
            
            # Plotar sinal demodulado
            self.demod_canvas.axes.clear()
            self.demod_canvas.axes.plot(t_plot, demod_plot)
            self.demod_canvas.axes.set_xlabel('Tempo (s)')
            self.demod_canvas.axes.set_ylabel('Fase (rad)')
            self.demod_canvas.axes.set_title(titulo)
            self.demod_canvas.axes.grid(True)
            self.demod_canvas.draw()
            log_debug("Sinal demodulado plotado com sucesso")
        except Exception as e:
            log_error(f"Erro ao plotar sinal demodulado: {e}")
        
    def show_filtered(self, t, filtered, filter_params):
        """
        Exibe o sinal após aplicação do filtro passa-banda
        
        Args:
            t: Vetor de tempo
            filtered: Sinal filtrado
            filter_params: Parâmetros do filtro (dicionário)
        """
        log_debug(f"show_filtered: t={len(t)}, filtered={len(filtered)}, params={filter_params}")
        
        # Verificação de segurança para dados válidos
        if len(t) == 0 or len(filtered) == 0:
            log_error("show_filtered: Dados vazios, não é possível exibir gráfico")
            self.show_message("Dados vazios, não é possível exibir gráfico", self.filtered_canvas)
            return
            
        if np.isnan(filtered).any() or np.isinf(filtered).any():
            log_warning("show_filtered: Dados contêm valores NaN ou infinitos")
            # Corrigir dados para exibição
            filtered_safe = np.copy(filtered)
            filtered_safe[np.isnan(filtered_safe)] = 0
            filtered_safe[np.isinf(filtered_safe)] = 0
            filtered = filtered_safe
            
        # Salvar em arquivo temporário para diagnóstico
        try:
            import os
            import pickle
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, 'last_filtered_data.pkl')
            with open(temp_file, 'wb') as f:
                pickle.dump({'t': t, 'filtered': filtered, 'params': filter_params}, f)
            log_debug(f"show_filtered: Dados salvos em {temp_file}")
        except Exception as e:
            log_warning(f"show_filtered: Não foi possível salvar dados temporários: {str(e)}")
            
        try:
            # Limitar número de pontos para plotagem
            max_points = 10000
            if len(t) > max_points:
                step = len(t) // max_points
                t_plot = t[::step]
                filtered_plot = filtered[::step]
                log_debug(f"show_filtered: Reduzindo pontos para plot: {len(t)} -> {len(t_plot)}")
            else:
                t_plot = t
                filtered_plot = filtered
            
            # Preparar título
            low_freq = filter_params.get('low_freq', 0)
            high_freq = filter_params.get('high_freq', 0)
            order = filter_params.get('order', 0)
            titulo = f'Sinal Filtrado (Passa-banda {low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order})'
            log_debug(f"show_filtered: Título do gráfico: '{titulo}'")
            
            # Plotar sinal filtrado
            self.filtered_canvas.axes.clear()
            self.filtered_canvas.axes.plot(t_plot, filtered_plot)
            self.filtered_canvas.axes.set_xlabel('Tempo (s)')
            self.filtered_canvas.axes.set_ylabel('Fase (rad)')
            self.filtered_canvas.axes.set_title(titulo)
            self.filtered_canvas.axes.grid(True)
            self.filtered_canvas.draw()
            log_debug("show_filtered: Canvas atualizado")
            
            # Habilitar botão para salvar dados filtrados
            self.save_filtered_button.setEnabled(True)
            
            # Mudar para a aba de sinal filtrado
            log_debug("show_filtered: Alterando para a aba de sinal filtrado (índice 3)")
            self.analysis_tabs.setCurrentIndex(3)
            
            log_debug("Sinal filtrado plotado com sucesso")
            
            # Verificação final para garantir que a aba está correta
            if self.analysis_tabs.currentIndex() != 3:
                log_warning("show_filtered: Falha ao mudar para a aba de sinal filtrado!")
                # Forçar novamente após um pequeno atraso
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.analysis_tabs.setCurrentIndex(3))
            
        except Exception as e:
            log_error(f"Erro ao plotar sinal filtrado: {str(e)}")
            # Tentar mostrar mensagem de erro no canvas
            try:
                self.show_message(f"Erro ao plotar sinal filtrado: {str(e)}", self.filtered_canvas)
            except:
                pass
            # Desabilitar botão em caso de erro
            self.save_filtered_button.setEnabled(False)
        
    def show_spectrum(self, freq_axis, magnitudes, peaks=None, use_filtered=False):
        """
        Exibe o espectro de frequência
        
        Args:
            freq_axis: Vetor de frequências
            magnitudes: Magnitudes do espectro em dB
            peaks: Lista de tuplas (freq, mag) com picos detectados
            use_filtered: Se True, indica que o espectro é do sinal filtrado
        """
        log_debug(f"show_spectrum: freq_axis={len(freq_axis)}, magnitudes={len(magnitudes)}, peaks={peaks is not None}, use_filtered={use_filtered}")
        try:
            # Preparar título
            titulo = f'Espectro FFT (Fs={freq_axis[-1]*2/1000:.1f} kHz, N={len(magnitudes)*2})'
            
            # Incluir informações sobre filtragem
            if use_filtered and self.bandpass_checkbox.isChecked():
                low_freq = self.low_freq_spinbox.value()
                high_freq = self.high_freq_spinbox.value()
                order = self.order_spinbox.value()
                titulo += f' [Filtrado: {low_freq:.1f}Hz-{high_freq:.1f}Hz]'
                
            if self.moving_avg_checkbox.isChecked():
                titulo += f' (com Média Móvel: {self.window_size_spinbox.value()})'
            
            # Plotar espectro principal
            self.spectrum_canvas.plot_spectrum(
                freq_axis, magnitudes, peaks=peaks,
                title=titulo
            )
            
            # Adicionar visualização com escala logarítmica
            inset_ax = self.spectrum_canvas.draw_inset()
            inset_ax.semilogx(freq_axis, magnitudes)
            inset_ax.set_title("Escala log", fontsize=8)
            inset_ax.grid(True, which='both', linestyle='--', alpha=0.6)
            
            # Marcar os mesmos picos na visualização em escala logarítmica
            if peaks:
                for freq, mag in peaks:
                    inset_ax.plot(freq, mag, 'ro', markersize=4)
                    
            self.spectrum_canvas.draw()
            log_debug("Espectro plotado com sucesso")
        except Exception as e:
            log_error(f"Erro ao plotar espectro: {str(e)}")
        
    def on_save_filtered_clicked(self):
        """Solicita salvar os dados filtrados"""
        log_info("Solicitando salvar dados filtrados")
        self.saveFilteredRequested.emit() 

    def on_apply_filter_clicked(self):
        """Método para aplicar o filtro passa-banda manualmente"""
        log_info("Aplicando filtro passa-banda manualmente")
        self.bandpassFilterChanged.emit(True, self.low_freq_spinbox.value(), self.high_freq_spinbox.value(), self.order_spinbox.value()) 

    def on_apply_moving_avg_clicked(self):
        """Método para aplicar a média móvel manualmente"""
        log_info("Aplicando média móvel manualmente")
        self.movingAverageChanged.emit(True, self.window_size_spinbox.value()) 

    def reset_bandpass_filter(self):
        """Reseta as configurações do filtro passa-banda"""
        log_debug("reset_bandpass_filter: Resetando configurações do filtro passa-banda")
        self.bandpass_checkbox.setChecked(False)
        self.low_freq_spinbox.setValue(50.0)
        self.high_freq_spinbox.setValue(5000.0)
        self.order_spinbox.setValue(4)
        self.low_freq_spinbox.setEnabled(False)
        self.high_freq_spinbox.setEnabled(False)
        self.order_spinbox.setEnabled(False)
        self.apply_filter_button.setEnabled(False)
        
        # Emitir sinal para desabilitar o filtro
        self.bandpassFilterChanged.emit(False, 50.0, 5000.0, 4) 

    def show_metadata(self, metadata):
        """
        Exibe os metadados do arquivo
        
        Args:
            metadata: Dicionário com os metadados
        """
        if not metadata:
            self.metadata_text.setPlainText("Sem metadados disponíveis")
            return
            
        # Formatar texto
        metadata_str = ""
        for key, value in metadata.items():
            metadata_str += f"{key}: {value}\n"
            
        self.metadata_text.setPlainText(metadata_str) 