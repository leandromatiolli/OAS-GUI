"""
Módulo com o painel de análise e visualização de dados
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton,
                           QComboBox, QLabel, QFileDialog, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal

from app.views.widgets.canvas import MplCanvas, NavigationToolbarCustom

class AnalysisPanel(QWidget):
    """Painel para análise e visualização de dados"""
    
    # Sinais
    fileSelected = pyqtSignal(str)  # Emitido quando um arquivo é selecionado
    demodulateRequested = pyqtSignal()  # Emitido quando o usuário solicita demodulação
    saveDemodulatedRequested = pyqtSignal()  # Emitido quando o usuário solicita salvar dados demodulados
    refreshFilesRequested = pyqtSignal()  # Emitido quando o usuário solicita atualização da lista de arquivos
    
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
        self.analysis_tabs.addTab(spectrum_tab, "Espectro")
        
        layout.addWidget(self.analysis_tabs)
        
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
        self.fileSelected.emit(filename)
        
    def on_demodulate_clicked(self):
        """Solicita demodulação dos dados"""
        self.demodulateRequested.emit()
        
    def clear_plots(self):
        """Limpa todos os gráficos"""
        self.raw_canvas.clear()
        self.ellipse_canvas.clear()
        self.demod_canvas.clear()
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
        self.raw_canvas.plot_timeseries(
            t, waveforms, channels=channels,
            title='Dados Brutos'
        )
        
    def show_ellipse(self, waveforms, ellipse_params=None):
        """
        Exibe o gráfico Lissajous e a elipse ajustada
        
        Args:
            waveforms: Array de formas de onda [canais, amostras]
            ellipse_params: Parâmetros da elipse ajustada (opcional)
        """
        # Limitar número de pontos para plot
        max_points = 5000
        if waveforms.shape[1] > max_points:
            step = waveforms.shape[1] // max_points
            waveforms_plot = waveforms[:, ::step]
        else:
            waveforms_plot = waveforms
            
        # Mostrar gráfico Lissajous
        self.ellipse_canvas.plot_scatter(
            waveforms_plot[0], waveforms_plot[1],
            xlabel='Canal 1', ylabel='Canal 2', 
            title='Figura de Lissajous'
        )
        
        # Se temos parâmetros da elipse, plotar a elipse ajustada
        if ellipse_params is not None:
            self.ellipse_canvas.plot_ellipse(
                fitted_params=ellipse_params,
                plot_params=True
            )
            
    def show_demodulated(self, t, demodulated):
        """
        Exibe o sinal demodulado
        
        Args:
            t: Vetor de tempo
            demodulated: Sinal demodulado
        """
        # Limitar número de pontos para plotagem
        max_points = 10000
        if len(t) > max_points:
            step = len(t) // max_points
            t_plot = t[::step]
            demod_plot = demodulated[::step]
        else:
            t_plot = t
            demod_plot = demodulated
        
        # Plotar sinal demodulado
        self.demod_canvas.axes.clear()
        self.demod_canvas.axes.plot(t_plot, demod_plot)
        self.demod_canvas.axes.set_xlabel('Tempo (s)')
        self.demod_canvas.axes.set_ylabel('Fase (rad)')
        self.demod_canvas.axes.set_title('Sinal Demodulado')
        self.demod_canvas.axes.grid(True)
        self.demod_canvas.draw()
        
    def show_spectrum(self, freq_axis, magnitudes, peaks=None):
        """
        Exibe o espectro de frequência
        
        Args:
            freq_axis: Vetor de frequências
            magnitudes: Magnitudes do espectro em dB
            peaks: Lista de tuplas (freq, mag) com picos detectados
        """
        # Plotar espectro principal
        self.spectrum_canvas.plot_spectrum(
            freq_axis, magnitudes, peaks=peaks,
            title=f'Espectro FFT (Fs={freq_axis[-1]*2/1000:.1f} kHz, N={len(magnitudes)*2})'
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