"""
Módulo com o painel de análise e visualização de dados
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton,
                           QComboBox, QLabel, QFileDialog, QMessageBox, QSplitter,
                           QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout,
                           QTextEdit, QListWidget)
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
import os

from app.views.widgets.canvas import MplCanvas, NavigationToolbarCustom
from app.utils import log
from app.models.data_store import DataStore

class AnalysisPanel(QWidget):
    """Painel para análise e visualização de dados"""
    
    # Sinais
    fileSelected = pyqtSignal(list)  # Emitido quando uma lista de arquivos é selecionada
    demodulateRequested = pyqtSignal()  # Emitido quando o usuário solicita demodulação
    saveDemodulatedRequested = pyqtSignal()  # Emitido quando o usuário solicita salvar dados demodulados
    saveFilteredRequested = pyqtSignal()  # Emitido quando o usuário solicita salvar dados filtrados
    refreshFilesRequested = pyqtSignal()  # Emitido quando o usuário solicita atualização da lista de arquivos
    movingAverageChanged = pyqtSignal(bool, int)  # Emitido quando a configuração de média móvel é alterada
    bandpassFilterChanged = pyqtSignal(bool, float, float, int)  # Emitido quando a configuração do filtro passa-banda é alterada
    spectrogramRequested = pyqtSignal(bool, int, float, float)  # Emitido quando o usuário solicita gerar espectrograma
    statusMessage = pyqtSignal(str)  # Signal for status bar messages
    
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
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        self.file_list.setMinimumWidth(400)
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        self.load_button = QPushButton("Carregar")
        self.load_button.clicked.connect(self.on_load_clicked)
        self.browse_button = QPushButton("Procurar...")
        self.browse_button.clicked.connect(self.on_browse_clicked)
        
        # Novo: seleção de pasta
        self.select_dir_button = QPushButton("Selecionar Pasta")
        self.select_dir_button.clicked.connect(self.on_select_dir_clicked)
        self.use_save_dir_button = QPushButton("Usar pasta de gravação")
        self.use_save_dir_button.clicked.connect(self.on_use_save_dir_clicked)
        self.current_dir = DataStore.load_last_state().get('save_directory', os.getcwd())
        self.dir_label = QLabel(self.current_dir)
        self.dir_label.setToolTip("Pasta para salvar os dado adquiridos")
        self.dir_label.setObjectName("mk_save_directory")


        file_buttons_group = QWidget()
        file_buttons_layout = QHBoxLayout()
        file_buttons_layout.addWidget(self.refresh_button)
        file_buttons_layout.addWidget(self.browse_button)
        file_buttons_layout.addWidget(self.load_button)
        file_buttons_layout.addWidget(self.select_dir_button)
        file_buttons_layout.addWidget(self.use_save_dir_button)
        file_buttons_group.setLayout(file_buttons_layout)

        file_right_group = QWidget()
        file_right_layout = QVBoxLayout()
        file_right_group.setLayout(file_right_layout)
        file_right_layout.addWidget(self.dir_label)
        file_right_layout.addWidget(file_buttons_group)
       
        file_selection_group = QGroupBox("Arquivo(s):")
        file_selection_layout = QHBoxLayout()
        file_selection_group.setLayout(file_selection_layout)
        file_selection_layout.addWidget(self.file_list)
        file_selection_layout.addWidget(file_right_group)
        layout.addWidget(file_selection_group)

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
        


        # Grupo variados

        variety_group = QGroupBox("Variados")
        variety_group_layout = QFormLayout()
        variety_group.setLayout(variety_group_layout)
        processing_layout.addWidget(variety_group)

        ## Linha para média móvel
        moving_avg_layout = QHBoxLayout()
        self.moving_avg_checkbox = QCheckBox("Ativar")
        self.moving_avg_checkbox.setObjectName("mk_moving_avg_active")
        moving_avg_layout.addWidget(self.moving_avg_checkbox)
        self.window_size_spinbox = QSpinBox()
        self.window_size_spinbox.setObjectName("mk_moving_avg_window_size")
        self.window_size_spinbox.setRange(2, 101)
        self.window_size_spinbox.setSingleStep(1)
        self.window_size_spinbox.setValue(10)
        self.window_size_spinbox.setEnabled(False)
        moving_avg_layout.addWidget(self.window_size_spinbox)
        variety_group_layout.addRow("Média Movel: ", moving_avg_layout)

        ## Linha salvar demodulado automaticamente

        self.autosave_demodulated_checkbox = QCheckBox()
        self.autosave_demodulated_checkbox.setChecked(False)
        self.autosave_demodulated_checkbox.setObjectName("mk_autosave_demodulated")
        variety_group_layout.addRow("Salvar Demodulado Automaticamente: ", self.autosave_demodulated_checkbox)
        
        ## Exibir medida automaticamente
        self.autoshow_waveform = QCheckBox("")
        self.autoshow_waveform.setObjectName("mk_autoshow_waveform")
        variety_group_layout.addRow("Exibir dados automaticamente: ", self.autoshow_waveform)
        
        ## Demodular dados automaticamente
        self.autodemodulate = QCheckBox("")
        self.autodemodulate.setObjectName("mk_autodemodulate")
        variety_group_layout.addRow("Demodular dados automaticamente: ", self.autodemodulate)
        
        
        # Grupo para filtro passa-banda
        bandpass_group = QGroupBox("Filtro Passa-Banda")
        bandpass_layout = QFormLayout()
        
        self.bandpass_checkbox = QCheckBox("Ativar")
        self.bandpass_checkbox.setObjectName("mk_apply_band_pass_filter")
        self.low_freq_spinbox = QDoubleSpinBox()
        self.low_freq_spinbox.setObjectName("mk_band_pass_filter_low_freq")
        self.low_freq_spinbox.setRange(0.1, 100000.0)
        self.low_freq_spinbox.setValue(50.0)
        self.low_freq_spinbox.setSuffix(" Hz")
        self.low_freq_spinbox.setEnabled(False)
        
        self.high_freq_spinbox = QDoubleSpinBox()
        self.high_freq_spinbox.setObjectName("mk_band_pass_filter_high_freq")
        self.high_freq_spinbox.setRange(0.1, 100000.0)
        self.high_freq_spinbox.setValue(5000.0)
        self.high_freq_spinbox.setSuffix(" Hz")
        self.high_freq_spinbox.setEnabled(False)
        
        self.order_spinbox = QSpinBox()
        self.order_spinbox.setObjectName("mk_band_pass_filter_order")
        self.order_spinbox.setRange(1, 10)
        self.order_spinbox.setValue(4)
        self.order_spinbox.setEnabled(False)
        
        self.apply_filter_button = QPushButton("Aplicar")   
        self.apply_filter_button.setEnabled(False)
        
        bandpass_layout.addRow(self.bandpass_checkbox)
        bandpass_layout.addRow("Freq. Mínima:", self.low_freq_spinbox)
        bandpass_layout.addRow("Freq. Máxima:", self.high_freq_spinbox)
        bandpass_layout.addRow("Ordem:", self.order_spinbox)
        bandpass_layout.addRow(self.apply_filter_button)
        bandpass_group.setLayout(bandpass_layout)
        processing_layout.addWidget(bandpass_group)
        
        layout.addLayout(processing_layout)
        
        # SubAbas para diferentes visualizações
        self.analysis_tabs = QTabWidget()
        
        # Aba de dados brutos
        raw_tab = QWidget()
        raw_layout = QHBoxLayout(raw_tab)
        self.raw_canvas = MplCanvas(self, width=9, height=5)
        self.raw_toolbar = NavigationToolbarCustom(self.raw_canvas, self)
        raw_layout.addWidget(self.raw_toolbar)
        raw_layout.addWidget(self.raw_canvas)
        self.analysis_tabs.addTab(raw_tab, "Dados Brutos")
        
        # Aba de elipse
        ellipse_tab = QWidget()
        ellipse_layout = QHBoxLayout(ellipse_tab)
        self.ellipse_canvas = MplCanvas(self, width=9, height=5)
        self.toolbars_and_buttons = QWidget()
        ellipse_toolbars_and_buttons_layout = QVBoxLayout(self.toolbars_and_buttons)
        
        self.ellipse_toolbar = NavigationToolbarCustom(self.ellipse_canvas, self)
        ellipse_toolbars_and_buttons_layout.addWidget(self.ellipse_toolbar)
        # Remove the coordinate label since we'll use status bar
        # self.coordinate_label = QLabel("")
        # ellipse_toolbars_and_buttons_layout.addWidget(self.coordinate_label)
        # self.ellipse_toolbar.set_coordinate_label(self.coordinate_label)
        self.fit_ellipse_button = QPushButton("Ajustar Elipse")
        self.fit_ellipse_button.setFixedWidth(250)
        ellipse_toolbars_and_buttons_layout.addWidget(self.fit_ellipse_button)
        ellipse_toolbars_and_buttons_layout.addWidget(QLabel(''), stretch=1)
        # align the button to the right
        
        ellipse_layout.addWidget(self.toolbars_and_buttons)
        ellipse_layout.addWidget(self.ellipse_canvas)
        ellipse_layout.addWidget(QLabel(''), stretch=1)  # Spacer
        self.analysis_tabs.addTab(ellipse_tab, "Elipse")
        
        # Aba de sinal demodulado
        demodulated_tab = QWidget()
        demodulated_layout = QHBoxLayout(demodulated_tab)
        self.demodulated_canvas = MplCanvas(self, width=9, height=5)
        self.demodulated_toolbar = NavigationToolbarCustom(self.demodulated_canvas, self)
        demodulated_layout.addWidget(self.demodulated_toolbar)
        demodulated_layout.addWidget(self.demodulated_canvas)
        self.analysis_tabs.addTab(demodulated_tab, "Sinal Demodulado")
        
        # Aba de sinal filtrado
        filtered_tab = QWidget()
        filtered_layout = QHBoxLayout(filtered_tab)
        self.filtered_canvas = MplCanvas(self, width=9, height=5)
        self.filtered_toolbar = NavigationToolbarCustom(self.filtered_canvas, self)
        filtered_layout.addWidget(self.filtered_toolbar)
        filtered_layout.addWidget(self.filtered_canvas)
        self.analysis_tabs.addTab(filtered_tab, "Sinal Filtrado")
        
        # Aba de espectro (log)
        spectrum_tab = QWidget()
        spectrum_layout = QHBoxLayout(spectrum_tab)
        self.spectrum_canvas = MplCanvas(self, width=9, height=5)
        self.spectrum_toolbar = NavigationToolbarCustom(self.spectrum_canvas, self)
        spectrum_layout.addWidget(self.spectrum_toolbar)
        spectrum_layout.addWidget(self.spectrum_canvas)
        self.analysis_tabs.addTab(spectrum_tab, "Espectro (Log)")
        
        # Nova aba de espectro (linear)
        spectrum_linear_tab = QWidget()
        spectrum_linear_layout = QHBoxLayout(spectrum_linear_tab)
        self.spectrum_linear_canvas = MplCanvas(self, width=9, height=5)
        self.spectrum_linear_toolbar = NavigationToolbarCustom(self.spectrum_linear_canvas, self)
        spectrum_linear_layout.addWidget(self.spectrum_linear_toolbar)
        spectrum_linear_layout.addWidget(self.spectrum_linear_canvas)
        self.analysis_tabs.addTab(spectrum_linear_tab, "Espectro (Linear)")
        
        # Aba de espectrograma
        spectrogram_tab = QWidget()
        spectrogram_layout = QHBoxLayout(spectrogram_tab)
        
        # Controles do espectrograma
        spectrogram_controls = QHBoxLayout()
        
        self.spectrogram_checkbox = QCheckBox("Ativar")
        self.spectrogram_checkbox.stateChanged.connect(self.on_spectrogram_changed)
        
        self.window_size_spectrogram_spinbox = QSpinBox()
        self.window_size_spectrogram_spinbox.setRange(16, 4096)
        self.window_size_spectrogram_spinbox.setValue(256)
        self.window_size_spectrogram_spinbox.setSingleStep(16)
        self.window_size_spectrogram_spinbox.setEnabled(False)
        
        self.overlap_spectrogram_spinbox = QDoubleSpinBox()
        self.overlap_spectrogram_spinbox.setRange(0.0, 0.99)
        self.overlap_spectrogram_spinbox.setValue(0.5)
        self.overlap_spectrogram_spinbox.setSingleStep(0.01)
        self.overlap_spectrogram_spinbox.setEnabled(False)
        
        self.max_freq_spectrogram_spinbox = QDoubleSpinBox()
        self.max_freq_spectrogram_spinbox.setRange(100.0, 1000000.0)
        self.max_freq_spectrogram_spinbox.setValue(100000.0)
        self.max_freq_spectrogram_spinbox.setSuffix(" Hz")
        self.max_freq_spectrogram_spinbox.setEnabled(False)
        
        self.generate_spectrogram_button = QPushButton("Gerar")
        self.generate_spectrogram_button.setEnabled(False)
        self.generate_spectrogram_button.clicked.connect(self.on_generate_spectrogram_clicked)
        
        spectrogram_controls.addWidget(self.spectrogram_checkbox)
        spectrogram_controls.addWidget(QLabel("Janela:"))
        spectrogram_controls.addWidget(self.window_size_spectrogram_spinbox)
        spectrogram_controls.addWidget(QLabel("Sobreposição:"))
        spectrogram_controls.addWidget(self.overlap_spectrogram_spinbox)
        spectrogram_controls.addWidget(QLabel("Freq. Máx:"))
        spectrogram_controls.addWidget(self.max_freq_spectrogram_spinbox)
        spectrogram_controls.addWidget(self.generate_spectrogram_button)
        
        spectrogram_layout.addLayout(spectrogram_controls)
        
        self.spectrogram_canvas = MplCanvas(self, width=9, height=5)
        self.spectrogram_toolbar = NavigationToolbarCustom(self.spectrogram_canvas, self)
        spectrogram_layout.addWidget(self.spectrogram_toolbar)
        spectrogram_layout.addWidget(self.spectrogram_canvas)
        
        self.analysis_tabs.addTab(spectrogram_tab, "Espectrograma")
        
        layout.addWidget(self.analysis_tabs)
        
        # Connect toolbar coordinate signals to status bar
        self.raw_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        self.ellipse_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        self.demodulated_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        self.filtered_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        self.spectrum_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        self.spectrum_linear_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        self.spectrogram_toolbar.coordinatesChanged.connect(self.statusMessage.emit)
        
        # Conectar sinais
        self.moving_avg_checkbox.stateChanged.connect(self.on_moving_average_changed)
        self.window_size_spinbox.valueChanged.connect(self.on_window_size_changed)
        self.bandpass_checkbox.stateChanged.connect(self.on_bandpass_filter_changed)
        self.low_freq_spinbox.valueChanged.connect(self.on_bandpass_params_changed)
        self.high_freq_spinbox.valueChanged.connect(self.on_bandpass_params_changed)
        self.order_spinbox.valueChanged.connect(self.on_bandpass_params_changed)
        self.apply_filter_button.clicked.connect(self.on_apply_filter_clicked)

    def on_moving_average_changed(self, state):
        """
        Manipula a mudança no estado da caixa de seleção de média móvel
        
        Args:
            state: Estado da caixa de seleção
        """
        is_checked = state == Qt.Checked
        # Atualizar a interface
        self.window_size_spinbox.setEnabled(is_checked)
        
        # Mostrar mensagem na barra de status
        if is_checked:
            log.info(f"Média móvel configurada com janela de {self.window_size_spinbox.value()}")
        else:
            log.info("Média móvel desativada")
        
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
            log.info(f"Tamanho da janela de média móvel alterado para {value}")
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
            log.info(f"Filtro passa-banda configurado ({low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order})")
        else:
            log.info("Filtro passa-banda desativado")
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
            
            log.info(f"Parâmetros do filtro passa-banda alterados: {low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order}")
            
            # NÃO emitir o sinal até que o botão seja clicado
            # self.bandpassFilterChanged.emit(True, low_freq, high_freq, order)
            
    def update_file_list(self, files):
        """
        Atualiza a lista de arquivos disponíveis
        
        Args:
            files: Lista de arquivos disponíveis
        """
        self.file_list.clear()
        for file in files:
            # Mostrar apenas o nome do arquivo, não o caminho completo
            filename = os.path.basename(file)
            self.file_list.addItem(filename)
            # Armazenar o caminho completo como dados do item
            self.file_list.item(self.file_list.count() - 1).setData(Qt.UserRole, file)
            
    def on_refresh_clicked(self):
        """Solicita atualização da lista de arquivos na pasta atual"""
        self.refresh_file_list_in_dir()
        
    def on_browse_clicked(self):
        """Abre um diálogo para selecionar arquivos manualmente (agora múltiplos)"""
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar arquivos de dados",
            self.dir_label.text(),
            "Arquivos pickle (*.pkl, *.pkl.gz) "
        )
        
        if file_paths:
            log.info(f"Arquivos selecionados: {file_paths}")
            # Adicionar arquivos à lista, evitando duplicados
            for file_path in file_paths:
                items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
                if file_path not in items:
                    self.file_list.addItem(file_path)
            # Selecionar todos os arquivos recém-adicionados
            for i in range(self.file_list.count()):
                self.file_list.item(i).setSelected(True)
            # Carregar os arquivos selecionados
            self.on_load_clicked()
            
    def on_load_clicked(self):
        """Solicita carregamento dos arquivos selecionados"""
        if self.file_list.count() == 0:
            return
        # Obter todos os arquivos selecionados
        selected_files = []
        for item in self.file_list.selectedItems():
            # Usar o caminho completo armazenado nos dados do item
            full_path = item.data(Qt.UserRole)
            if full_path:
                selected_files.append(full_path)
            else:
                # Fallback: usar o texto do item como caminho completo
                selected_files.append(item.text())
        
        if not selected_files:
            return
<<<<<<< HEAD
            
        log_info(f"Carregando arquivos: {selected_files}")
=======
        # Montar caminho completo para cada arquivo
        selected_files_full = [os.path.join(self.current_dir, f) for f in selected_files]
        log.info(f"Carregando arquivos: {selected_files_full}")
>>>>>>> db4e97fd2148c52ebfbb81570be8dfceb8b2e7e1
        # Emitir sinal com a lista de arquivos
        self.fileSelected.emit(selected_files)
        
    def on_demodulate_clicked(self):
        """Solicita demodulação dos dados"""
        log.info("Solicitando demodulação do sinal")
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
        self.demodulated_canvas.clear()
        self.filtered_canvas.clear()
        self.spectrum_canvas.clear()
        self.spectrum_linear_canvas.clear()
        self.spectrogram_canvas.clear()
        
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
        log.debug(f"show_raw_data: t={len(t)}, waveforms={waveforms.shape}, channels={channels}")
        try:
            # Verificar se a média móvel está ativada para adicionar ao título
            titulo = 'Dados Brutos'
            if self.moving_avg_checkbox.isChecked():
                titulo += f' (com Média Móvel: {self.window_size_spinbox.value()})'
                
            self.raw_canvas.plot_timeseries(
                t, waveforms, channels=channels,
            )
            self.raw_canvas.draw()
            log.debug("Gráfico de dados brutos atualizado com sucesso")
            # Certificar-se que a aba está visível
            self.analysis_tabs.setCurrentIndex(0)
        except Exception as e:
            log.error(f"Erro ao plotar dados brutos: {e}")
        
    def show_ellipse(self, waveforms, ellipse_params=None):
        """
        Exibe o gráfico Lissajous e a elipse ajustada
        
        Args:
            waveforms: Array de formas de onda [canais, amostras]
            ellipse_params: Parâmetros da elipse ajustada (opcional)
        """
        log.debug(f"show_ellipse: waveforms={waveforms.shape}, ellipse_params={ellipse_params is not None}")
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
            )
            # Se temos parâmetros da elipse, plotar a elipse ajustada
            if ellipse_params is not None:
                self.ellipse_canvas.plot_ellipse(
                    fitted_params=ellipse_params,
                    plot_params=True
                )
                log.debug("Elipse ajustada plotada com sucesso")
        except Exception as e:
            log.error(f"Erro ao plotar elipse: {e}")
            
    def show_demodulated(self, t, demodulated):
        """
        Exibe o sinal demodulado
        
        Args:
            t: Vetor de tempo
            demodulated: Sinal demodulado
        """
        log.debug(f"show_demodulated: t={len(t)}, demodulated={len(demodulated)}")
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
            self.demodulated_canvas.axes.clear()
            self.demodulated_canvas.axes.plot(t_plot, demod_plot)
            self.demodulated_canvas.axes.set_xlabel('Tempo (s)')
            self.demodulated_canvas.axes.set_ylabel('Fase (rad)')
            self.demodulated_canvas.axes.grid(True)
            self.demodulated_canvas.draw()
            log.debug("Sinal demodulado plotado com sucesso")
        except Exception as e:
            log.error(f"Erro ao plotar sinal demodulado: {e}")
        
    def show_filtered(self, t, filtered, filter_params):
        """
        Exibe o sinal após aplicação do filtro passa-banda
        
        Args:
            t: Vetor de tempo
            filtered: Sinal filtrado
            filter_params: Parâmetros do filtro (dicionário)
        """
        log.debug(f"show_filtered: t={len(t)}, filtered={len(filtered)}, params={filter_params}")
        
        # Verificação de segurança para dados válidos
        if len(t) == 0 or len(filtered) == 0:
            log.error("show_filtered: Dados vazios, não é possível exibir gráfico")
            self.show_message("Dados vazios, não é possível exibir gráfico", self.filtered_canvas)
            return
            
        if np.isnan(filtered).any() or np.isinf(filtered).any():
            log.warning("show_filtered: Dados contêm valores NaN ou infinitos")
            # Corrigir dados para exibição
            filtered_safe = np.copy(filtered)
            filtered_safe[np.isnan(filtered_safe)] = 0
            filtered_safe[np.isinf(filtered_safe)] = 0
            filtered = filtered_safe
                        
        try:
            # Limitar número de pontos para plotagem
            max_points = 10000
            if len(t) > max_points:
                step = len(t) // max_points
                t_plot = t[::step]
                filtered_plot = filtered[::step]
                log.debug(f"show_filtered: Reduzindo pontos para plot: {len(t)} -> {len(t_plot)}")
            else:
                t_plot = t
                filtered_plot = filtered
            
            # Preparar título
            low_freq = filter_params.get('low_freq', 0)
            high_freq = filter_params.get('high_freq', 0)
            order = filter_params.get('order', 0)
            titulo = f'Sinal Filtrado (Passa-banda {low_freq:.1f}Hz-{high_freq:.1f}Hz, ordem {order})'
            



            # Plotar sinal filtrado
            self.filtered_canvas.axes.clear()
            line, = self.filtered_canvas.axes.plot(t_plot, filtered_plot)
            self.filtered_canvas.axes.set_xlabel('Tempo (s)')
            self.filtered_canvas.axes.set_ylabel('Fase (rad)')

            #self.filtered_canvas.axes.set_title(titulo)
            self.filtered_canvas.axes.grid(True)
            self.filtered_canvas.draw()
            
            log.debug("show_filtered: Canvas atualizado")
                        
            def update_line_on_zoom(event):
                xlim = self.filtered_canvas.axes.get_xlim()
                # # Get a dense enough subset in current view

                idx = (t >= xlim[0]) & (t <= xlim[1])
                x_view = t[idx]
                y_view = filtered[idx]

                # # Optional: downsample only if still too dense (e.g. > 5000 points)
                if len(x_view) > max_points:
                     step = len(x_view) // max_points
                     x_view = x_view[::step]
                     y_view = y_view[::step]

                line.set_data(x_view, y_view)
                self.filtered_canvas.axes.relim()
                # self.filtered_canvas.axes.autoscale_view()
                # self.filtered_canvas.draw_idle()
            self.filtered_canvas.axes.callbacks.connect('xlim_changed', update_line_on_zoom)

            # Mudar para a aba de sinal filtrado
            self.analysis_tabs.setCurrentIndex(3)
            
            
            # Verificação final para garantir que a aba está correta
            if self.analysis_tabs.currentIndex() != 3:
                log.warning("show_filtered: Falha ao mudar para a aba de sinal filtrado!")
                # Forçar novamente após um pequeno atraso
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.analysis_tabs.setCurrentIndex(3))
            
        except Exception as e:
            log.error(f"Erro ao plotar sinal filtrado: {str(e)}")
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
        log.debug(f"show_spectrum: freq_axis={len(freq_axis)}, magnitudes={len(magnitudes)}, peaks={peaks is not None}, use_filtered={use_filtered}")
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
            log.debug("Espectro plotado com sucesso")
        except Exception as e:
            log.error(f"Erro ao plotar espectro: {str(e)}")
        
    def on_save_filtered_clicked(self):
        """Solicita salvar os dados filtrados"""
        log.info("Solicitando salvar dados filtrados")
        self.saveFilteredRequested.emit() 

    def on_apply_filter_clicked(self):
        """Método para aplicar o filtro passa-banda manualmente"""
        log.info("Aplicando filtro passa-banda manualmente")
        self.bandpassFilterChanged.emit(True, self.low_freq_spinbox.value(), self.high_freq_spinbox.value(), self.order_spinbox.value()) 



    def show_metadata(self, data):
        """
        Exibe os metadados do arquivo
        
        Args:
            metadata: Dicionário com os metadados
        """
        metadata = data.copy()
        del metadata['waveforms']  # Remover dados de onda para evitar sobrecarga
        del metadata['t']  # Remover vetor de tempo para evitar sobrecarga
            
        # Formatar texto
        metadata_str = ""
        for key, value in metadata.items():
            metadata_str += f"{key}: {value}\n"
            
        self.metadata_text.setPlainText(metadata_str) 

    def on_spectrogram_changed(self, state):
        """
        Manipula a mudança no estado da caixa de seleção do espectrograma
        
        Args:
            state: Estado da caixa de seleção
        """
        is_checked = state == Qt.Checked
        self.window_size_spectrogram_spinbox.setEnabled(is_checked)
        self.overlap_spectrogram_spinbox.setEnabled(is_checked)
        self.max_freq_spectrogram_spinbox.setEnabled(is_checked)
        self.generate_spectrogram_button.setEnabled(is_checked)
        
        if is_checked:
            window_size = self.window_size_spectrogram_spinbox.value()
            overlap = self.overlap_spectrogram_spinbox.value()
            max_freq = self.max_freq_spectrogram_spinbox.value()
            log.info(f"Espectrograma configurado (janela: {window_size}, sobreposição: {overlap:.2f}, freq_max: {max_freq:.1f}Hz)")
        else:
            log.info("Espectrograma desativado")
    
    def on_generate_spectrogram_clicked(self):
        """Solicita a geração do espectrograma"""
        if not self.spectrogram_checkbox.isChecked():
            return
            
        window_size = self.window_size_spectrogram_spinbox.value()
        overlap = self.overlap_spectrogram_spinbox.value()
        max_freq = self.max_freq_spectrogram_spinbox.value()
        
        log.info(f"Gerando espectrograma (janela: {window_size}, sobreposição: {overlap:.2f}, freq_max: {max_freq:.1f}Hz)")
        self.spectrogramRequested.emit(True, window_size, overlap, max_freq)
        
    def show_spectrogram(self, t, freqs, Sxx, params=None):
        """
        Exibe o espectrograma do sinal
        
        Args:
            t: Vetor de tempo para o eixo x
            freqs: Vetor de frequências para o eixo y
            Sxx: Matriz do espectrograma
            params: Parâmetros usados para gerar o espectrograma
        """
        log.debug(f"show_spectrogram: t={len(t)}, freqs={len(freqs)}, Sxx={Sxx.shape}")
        
        try:
            # Preparar título
            titulo = 'Espectrograma'
            if params:
                window_size = params.get('window_size', 0)
                overlap = params.get('overlap', 0)
                max_freq = params.get('max_freq', 0)
                titulo = f'Espectrograma (Janela: {window_size}, Sobreposição: {overlap:.2f}, Freq Max: {max_freq/1000:.1f} kHz)'
            
            # Plotar espectrograma
            self.spectrogram_canvas.axes.clear()
            pcm = self.spectrogram_canvas.axes.pcolormesh(t, freqs, 10 * np.log10(Sxx), shading='gouraud', cmap='viridis')
            self.spectrogram_canvas.axes.set_xlabel('Tempo (s)')
            self.spectrogram_canvas.axes.set_ylabel('Frequência (Hz)')
            self.spectrogram_canvas.axes.set_title(titulo)
            
            # Adicionar barra de cores
            cbar = self.spectrogram_canvas.fig.colorbar(pcm, ax=self.spectrogram_canvas.axes)
            cbar.set_label('Potência/Frequência (dB/Hz)')
            
            self.spectrogram_canvas.draw()
            
            # Mudar para a aba de espectrograma
            self.analysis_tabs.setCurrentIndex(5)  # Índice da aba de espectrograma
            
            log.debug("Espectrograma plotado com sucesso")
        except Exception as e:
            log.error(f"Erro ao plotar espectrograma: {str(e)}")
            
    def reset_spectrogram(self):
        """Reseta as configurações do espectrograma"""
        log.debug("reset_spectrogram: Resetando configurações do espectrograma")
        self.spectrogram_checkbox.setChecked(False)
        self.window_size_spectrogram_spinbox.setValue(256)
        self.overlap_spectrogram_spinbox.setValue(0.5)
        self.max_freq_spectrogram_spinbox.setValue(100000.0)
        self.window_size_spectrogram_spinbox.setEnabled(False)
        self.overlap_spectrogram_spinbox.setEnabled(False)
        self.max_freq_spectrogram_spinbox.setEnabled(False)
        self.generate_spectrogram_button.setEnabled(False)

    def reset_bandpass_filter(self):
        """Reseta as configurações do filtro passa-banda"""
        log.debug("reset_bandpass_filter: Resetando configurações do filtro passa-banda")
        self.bandpass_checkbox.setChecked(False)
        self.low_freq_spinbox.setValue(50.0)
        self.high_freq_spinbox.setValue(5000.0)
        self.order_spinbox.setValue(4)
        self.low_freq_spinbox.setEnabled(False)
        self.high_freq_spinbox.setEnabled(False)
        self.order_spinbox.setEnabled(False)
        self.apply_filter_button.setEnabled(False)

    def load_selected_file_from_list(self, file_list):
        """Carrega múltiplos arquivos a partir de uma lista de caminhos e plota espectros"""
        self.multiple_demodulated_data = []
        self.multiple_metadata = []  # Lista para armazenar metadados de todos os arquivos
        
        for filename in file_list:
            try:
                data = DataStore.load_data(filename)  # Carregar dados usando DataStore
                if 'demodulated' in data:
                    self.multiple_demodulated_data.append(data)
                    # Coletar metadados do arquivo
                    if 'metadata' in data.keys():
                        metadata = data.get('metadata', {})
                    else:
                        metadata = {k: v for k, v in data.items() if k not in ['waveforms', 'demodulated']}
                    metadata['filename'] = filename  # Adicionar nome do arquivo aos metadados
                    self.multiple_metadata.append(metadata)
                    
                # Para o primeiro arquivo, mostrar dados brutos e demodulados
                if len(self.multiple_demodulated_data) == 1:
                    if 't' in data and 'waveforms' in data:
                        channels = data.get('channels', [1, 2])
                        self.show_raw_data(data['t'], data['waveforms'], channels)
                    if 't' in data and 'demodulated' in data:
                        self.show_demodulated(data['t'], data['demodulated'])
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo: {str(e)}")
        
        # Após carregar todos, plotar espectros múltiplos e mostrar metadados
        if self.multiple_demodulated_data:
            # Plotar todos os sinais demodulados sobrepostos
            self.plot_demodulated_multiple()
            self.plot_spectrum_multiple()
            self.show_metadata_multiple(self.multiple_metadata)

    def plot_spectrum_multiple(self):
        """Plota o espectro de todos os arquivos carregados, com cores e transparências diferentes"""
        import numpy as np
        from scipy.signal import get_window
        
        # Plotar em ambas as abas (log e linear)
        for canvas, is_log in [(self.spectrum_canvas, True), (self.spectrum_linear_canvas, False)]:
            ax = canvas.axes
            ax.clear()
            colors = ['blue', 'red', 'green', 'orange', 'purple']
            alphas = [1.0, 0.5, 0.7, 0.7, 0.7]
            
            for idx, data in enumerate(self.multiple_demodulated_data):
                if 'demodulated' not in data:
                    continue
                demodulated = data['demodulated']
                # Determinar a taxa de amostragem
                if 'sample_frequency' in data and 'decimation' in data:
                    fs = data['sample_frequency'] / data['decimation']
                elif 'sample_frequency_effective' in data:
                    fs = data['sample_frequency_effective']
                elif 't' in data and len(data['t']) >= 2:
                    t = data['t']
                    dt = t[1] - t[0]
                    fs = 1 / dt
                else:
                    fs = 1.953125e6
                window = get_window('blackman', len(demodulated))
                signal_windowed = demodulated * window
                N = len(signal_windowed)
                fft_result = np.fft.fft(signal_windowed)
                fft_result = fft_result / N
                magnitudes = np.abs(fft_result[:N//2])
                freq_axis = np.arange(N//2) * fs / N
                
                if is_log:
                    # Escala logarítmica em dB
                    magnitudes_plot = 20 * np.log10(magnitudes + 1e-10)
                    ylabel = 'Amplitude (dB)'
                else:
                    # Escala linear
                    magnitudes_plot = magnitudes
                    ylabel = 'Amplitude'
                
                label = f"Arquivo {idx+1}"
                ax.plot(freq_axis, magnitudes_plot, color=colors[idx % len(colors)], alpha=alphas[idx % len(alphas)], label=label)
            
            # Configurar escala logarítmica no eixo x para ambas as abas
            ax.set_xscale('log')
            ax.set_xlim(10, fs/2)  # Começa em 10 Hz e vai até metade da frequência de amostragem
            
            # Configurar título e labels
            if is_log:
                ax.set_title('Espectro FFT de múltiplos arquivos (Escala Log)')
            else:
                ax.set_title('Espectro FFT de múltiplos arquivos (Amplitude Linear)')
            
            ax.set_xlabel('Frequência (Hz)')
            ax.set_ylabel(ylabel)
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.legend()
            canvas.draw()

    def plot_calibration_data(self, calibration_data):
                        
        # self.show_raw_data(calibration_data['t'], 
        #                    calibration_data['waveforms'], 
        #                    calibration_data['channels'])
        self.show_ellipse(calibration_data['waveforms'], 
                         calibration_data['ellipse_params'])
        

    def show_metadata_multiple(self, metadata_list):
        """
        Exibe os metadados de múltiplos arquivos
        
        Args:
            metadata_list: Lista de dicionários com os metadados de cada arquivo
        """
        if not metadata_list:
            self.metadata_text.setPlainText("Sem metadados disponíveis")
            return
            
        # Formatar texto para múltiplos arquivos
        metadata_str = ""
        for idx, metadata in enumerate(metadata_list, 1):
            metadata_str += f"=== ARQUIVO {idx} ===\n"
            if 'filename' in metadata:
                import os
                filename = os.path.basename(metadata['filename'])
                metadata_str += f"Nome: {filename}\n"
            
            # Exibir outros metadados
            for key, value in metadata.items():
                if key != 'filename':  # Já exibimos o filename acima
                    metadata_str += f"{key}: {value}\n"
            metadata_str += "\n"  # Linha em branco entre arquivos
            
        self.metadata_text.setPlainText(metadata_str) 

    def on_select_dir_clicked(self):
        """Abre diálogo para selecionar a pasta de análise"""
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a pasta para análise", self.current_dir)
        if dir_path:
            self.current_dir = dir_path
            self.dir_label.setText(dir_path)
            self.refresh_file_list_in_dir()
    
    def on_use_save_dir_clicked(self):
        """Usa a mesma pasta da gravação (configuração)"""
        dir_path = DataStore.load_last_state().get('save_directory', os.getcwd())
        self.current_dir = dir_path
        self.dir_label.setText(dir_path)
        self.refresh_file_list_in_dir()
    
    def refresh_file_list_in_dir(self):
        """Atualiza a lista de arquivos demodulados (.pkl.gz) na pasta atual de análise, sem duplicatas e só o nome do arquivo"""
        self.file_list.clear()
        # Procurar apenas arquivos demodulados na pasta selecionada
        demod_files = [f for f in os.listdir(self.current_dir)
                       if f.startswith("vazamento_demodulado_") and (f.endswith('.pkl') or f.endswith('.pkl.gz'))]
        # Remover duplicatas
        demod_files = list(sorted(set(demod_files), key=lambda x: os.path.getmtime(os.path.join(self.current_dir, x)), reverse=True))
        for file in demod_files:
            self.file_list.addItem(file) 

    def plot_demodulated_multiple(self):
        """Plota os sinais demodulados de todos os arquivos carregados simultaneamente."""
        import numpy as np

        if not getattr(self, 'multiple_demodulated_data', None):
            return

        ax = self.demodulated_canvas.axes
        ax.clear()

        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'cyan', 'magenta']
        alphas = [1.0, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]

        max_points = 10000  # limitar pontos para visualização

        for idx, data in enumerate(self.multiple_demodulated_data):
            demod = data.get('demodulated')
            if demod is None:
                continue

            # Recuperar eixo de tempo ou calcular
            if 't' in data:
                t = np.asarray(data['t'])
            else:
                # Determinar fs
                if 'sample_frequency' in data and 'decimation' in data:
                    fs = data['sample_frequency'] / data['decimation']
                elif 'sample_frequency_effective' in data:
                    fs = data['sample_frequency_effective']
                else:
                    fs = 1.0  # fallback
                t = np.arange(len(demod)) / fs

            # Reduzir pontos se necessário
            if len(t) > max_points:
                step = len(t) // max_points
                t_plot = t[::step]
                d_plot = demod[::step]
            else:
                t_plot = t
                d_plot = demod

            label = f"Arquivo {idx + 1}"
            ax.plot(t_plot, d_plot, color=colors[idx % len(colors)], alpha=alphas[idx % len(alphas)], label=label)

        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel('Fase (rad)')
        ax.set_title('Sinais Demodulados (Múltiplos Arquivos)')
        ax.grid(True)
        ax.legend()

        self.demodulated_canvas.draw()

        # Garantir que a aba correta está selecionada (índice 2 = Demodulado)
        try:
            self.analysis_tabs.setCurrentIndex(2)
        except Exception:
            pass 