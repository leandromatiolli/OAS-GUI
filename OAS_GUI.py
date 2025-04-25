import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTabWidget, QLabel, QFileDialog, QComboBox, 
                             QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QStatusBar, QSplitter, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import glob
import pickle
from datetime import datetime
from scipy import signal

# Importar nossas funções dos outros módulos
try:
    import mkf
    import redpitaya_scpi as scpi
    from OAS_Acquire_Continuous import bring_up_scpi_server, acquire_continuous_data, save_data
    ACQUISITION_AVAILABLE = True
except ImportError:
    ACQUISITION_AVAILABLE = False
    print("Módulos de aquisição não encontrados. Funcionalidade de aquisição será desabilitada.")

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)

class AcquisitionThread(QThread):
    """Thread para aquisição de dados sem congelar a interface"""
    finished = pyqtSignal(dict)  # Sinal emitido quando a aquisição termina
    progress = pyqtSignal(str)   # Sinal para atualizar o status
    error = pyqtSignal(str)      # Sinal para reportar erros

    def __init__(self, ip, duration, sample_rate, decimation, channels):
        super().__init__()
        self.ip = ip
        self.duration = duration
        self.sample_rate = sample_rate
        self.decimation = decimation
        self.channels = channels

    def run(self):
        """Executa a aquisição em thread separada"""
        try:
            self.progress.emit("Iniciando aquisição...")
            data = acquire_continuous_data(
                self.ip, duration=self.duration,
                sample_rate=self.sample_rate,
                decimation=self.decimation,
                channels=self.channels
            )
            self.progress.emit("Salvando dados...")
            filename = save_data(data)
            self.progress.emit(f"Dados salvos em {filename}")
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(f"Erro na aquisição: {str(e)}")

class OASGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OAS - Interface de Aquisição e Análise")
        self.setMinimumSize(1000, 800)
        
        # Variáveis de estado
        self.data = None
        self.demodulated_data = None
        
        # Configurar a interface
        self.setup_ui()
        
        # Verificar se a aquisição está disponível
        if not ACQUISITION_AVAILABLE:
            self.acquisition_group.setEnabled(False)
            self.statusBar().showMessage("Módulos de aquisição não disponíveis")
    
    def setup_ui(self):
        """Configura a interface de usuário"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Criar abas
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Aba de Aquisição
        acquisition_tab = QWidget()
        acquisition_layout = QVBoxLayout(acquisition_tab)
        
        # Grupo de configurações de aquisição
        self.acquisition_group = QGroupBox("Configurações de Aquisição")
        acquisition_form = QFormLayout()
        
        # IP do RedPitaya
        self.ip_edit = QLineEdit("rp-f0b916.local")
        acquisition_form.addRow("IP RedPitaya:", self.ip_edit)
        
        # Duração da aquisição
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 60.0)
        self.duration_spin.setValue(5.0)
        self.duration_spin.setSingleStep(0.5)
        acquisition_form.addRow("Duração (s):", self.duration_spin)
        
        # Decimação
        self.decimation_combo = QComboBox()
        for i in range(0, 17):  # Potências de 2 de 1 a 2^16
            self.decimation_combo.addItem(f"{2**i}", 2**i)
        self.decimation_combo.setCurrentIndex(6)  # 2^6 = 64
        acquisition_form.addRow("Decimação:", self.decimation_combo)
        
        # Canais
        self.ch1_check = QCheckBox("Canal 1")
        self.ch1_check.setChecked(True)
        self.ch2_check = QCheckBox("Canal 2")
        self.ch2_check.setChecked(True)
        
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(self.ch1_check)
        channels_layout.addWidget(self.ch2_check)
        acquisition_form.addRow("Canais:", channels_layout)
        
        self.acquisition_group.setLayout(acquisition_form)
        acquisition_layout.addWidget(self.acquisition_group)
        
        # Botões de aquisição
        acquisition_buttons = QHBoxLayout()
        self.acquire_button = QPushButton("Adquirir Dados")
        self.acquire_button.clicked.connect(self.start_acquisition)
        acquisition_buttons.addWidget(self.acquire_button)
        
        acquisition_layout.addLayout(acquisition_buttons)
        
        # Aba de Análise
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Widget para selecionar arquivo
        file_selection = QHBoxLayout()
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(400)
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.refresh_file_list)
        self.load_button = QPushButton("Carregar")
        self.load_button.clicked.connect(self.load_selected_file)
        self.browse_button = QPushButton("Procurar...")
        self.browse_button.clicked.connect(self.browse_file)
        
        file_selection.addWidget(QLabel("Arquivo:"))
        file_selection.addWidget(self.file_combo)
        file_selection.addWidget(self.refresh_button)
        file_selection.addWidget(self.browse_button)
        file_selection.addWidget(self.load_button)
        
        analysis_layout.addLayout(file_selection)
        
        # SubAbas para diferentes visualizações
        self.analysis_tabs = QTabWidget()
        
        # Aba de dados brutos
        raw_tab = QWidget()
        raw_layout = QVBoxLayout(raw_tab)
        self.raw_canvas = MplCanvas(self, width=9, height=5)
        self.raw_toolbar = NavigationToolbar(self.raw_canvas, self)
        raw_layout.addWidget(self.raw_toolbar)
        raw_layout.addWidget(self.raw_canvas)
        
        # Aba de fit de elipse
        ellipse_tab = QWidget()
        ellipse_layout = QVBoxLayout(ellipse_tab)
        self.ellipse_canvas = MplCanvas(self, width=9, height=5)
        self.ellipse_toolbar = NavigationToolbar(self.ellipse_canvas, self)
        self.demodulate_button = QPushButton("Demodular Sinal")
        self.demodulate_button.clicked.connect(self.demodulate_data)
        
        ellipse_layout.addWidget(self.ellipse_toolbar)
        ellipse_layout.addWidget(self.ellipse_canvas)
        ellipse_layout.addWidget(self.demodulate_button)
        
        # Aba de sinal demodulado
        demod_tab = QWidget()
        demod_layout = QVBoxLayout(demod_tab)
        self.demod_canvas = MplCanvas(self, width=9, height=5)
        self.demod_toolbar = NavigationToolbar(self.demod_canvas, self)
        demod_layout.addWidget(self.demod_toolbar)
        demod_layout.addWidget(self.demod_canvas)
        
        # Aba de espectro
        spectrum_tab = QWidget()
        spectrum_layout = QVBoxLayout(spectrum_tab)
        self.spectrum_canvas = MplCanvas(self, width=9, height=5)
        self.spectrum_toolbar = NavigationToolbar(self.spectrum_canvas, self)
        spectrum_layout.addWidget(self.spectrum_toolbar)
        spectrum_layout.addWidget(self.spectrum_canvas)
        
        # Adicionar as sub-abas ao TabWidget de análise
        self.analysis_tabs.addTab(raw_tab, "Dados Brutos")
        self.analysis_tabs.addTab(ellipse_tab, "Fit da Elipse")
        self.analysis_tabs.addTab(demod_tab, "Sinal Demodulado")
        self.analysis_tabs.addTab(spectrum_tab, "Espectro")
        
        analysis_layout.addWidget(self.analysis_tabs)
        
        # Adicionar as abas principais
        self.tabs.addTab(acquisition_tab, "Aquisição")
        self.tabs.addTab(analysis_tab, "Análise")
        
        # Barra de status
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Atualizar lista de arquivos
        self.refresh_file_list()
    
    def browse_file(self):
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
            self.load_selected_file()
    
    def refresh_file_list(self):
        """Atualiza a lista de arquivos .pkl disponíveis"""
        self.file_combo.clear()
        
        # Procurar arquivos .pkl
        pkl_files = []
        pkl_files.extend(glob.glob("vazamento_sensor_*.pkl"))
        pkl_files.extend(glob.glob("vazamento_continuo_*.pkl"))
        pkl_files.extend(glob.glob("vazamento_demodulado_*.pkl"))
        
        # Ordenar por data de modificação (mais recente primeiro)
        pkl_files.sort(key=os.path.getmtime, reverse=True)
        
        # Adicionar ao combobox
        for file in pkl_files:
            self.file_combo.addItem(file)
    
    def start_acquisition(self):
        """Inicia a aquisição de dados em thread separada"""
        if not ACQUISITION_AVAILABLE:
            QMessageBox.warning(self, "Erro", "Módulos de aquisição não disponíveis")
            return
        
        # Obter parâmetros de aquisição
        ip = self.ip_edit.text()
        duration = self.duration_spin.value()
        decimation = self.decimation_combo.currentData()
        
        # Verificar canais selecionados
        channels = []
        if self.ch1_check.isChecked():
            channels.append(1)
        if self.ch2_check.isChecked():
            channels.append(2)
        
        if not channels:
            QMessageBox.warning(self, "Erro", "Selecione pelo menos um canal")
            return
        
        # Desabilitar interface durante a aquisição
        self.acquire_button.setEnabled(False)
        self.statusBar.showMessage("Aguarde, adquirindo dados...")
        
        # Criar e iniciar thread de aquisição
        self.acquisition_thread = AcquisitionThread(
            ip, duration, 125e6, decimation, channels
        )
        self.acquisition_thread.progress.connect(self.update_status)
        self.acquisition_thread.error.connect(self.show_error)
        self.acquisition_thread.finished.connect(self.acquisition_finished)
        self.acquisition_thread.start()
    
    def update_status(self, message):
        """Atualiza a barra de status"""
        self.statusBar.showMessage(message)
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        self.acquire_button.setEnabled(True)
        QMessageBox.critical(self, "Erro", message)
        self.statusBar.showMessage("Erro na aquisição")
    
    def acquisition_finished(self, data):
        """Chamado quando a aquisição é concluída"""
        self.acquire_button.setEnabled(True)
        self.data = data
        
        # Realizar demodulação automática após a aquisição
        self.statusBar.showMessage("Aquisição concluída. Realizando demodulação automática...")
        success = self.auto_demodulate()
        
        if success:
            # Salvar dados com demodulação incluída
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vazamento_demodulado_{timestamp}.pkl"
            
            with open(filename, 'wb') as f:
                pickle.dump(self.demodulated_data, f)
            
            self.statusBar.showMessage(f"Aquisição e demodulação concluídas. Dados salvos em {filename}")
        else:
            # Dados brutos já são salvos pela thread de aquisição
            self.statusBar.showMessage("Aquisição concluída, mas a demodulação falhou. Apenas dados brutos foram salvos.")
        
        self.refresh_file_list()
        
        # Mudar para a aba de análise e carregar o arquivo
        self.tabs.setCurrentIndex(1)
        if self.file_combo.count() > 0:
            self.load_selected_file()
    
    def auto_demodulate(self):
        """Realiza demodulação automática após a aquisição"""
        if not self.data or 'waveforms' not in self.data:
            print("Sem dados para demodular automaticamente")
            return False
        
        try:
            # Verificar se temos dois canais
            if self.data['waveforms'].shape[0] < 2:
                print("Necessários dois canais para demodulação automática")
                return False
            
            # Realizar fit da elipse
            waveforms = self.data['waveforms']
            
            # Limitar o número de pontos para o fit, se necessário
            max_fit_points = 100000
            if waveforms.shape[1] > max_fit_points:
                step = waveforms.shape[1] // max_fit_points
                waveforms_fit = waveforms[:, ::step]
                print(f"Usando {waveforms_fit.shape[1]} pontos para fit automático da elipse")
            else:
                waveforms_fit = waveforms
            
            try:
                print("Iniciando ajuste de elipse automático...")
                ellipse_params = mkf.fit_ellipse(*waveforms_fit)
                print(f"Parâmetros da elipse: {ellipse_params}")
            except Exception as e:
                print(f"Erro no fit automático da elipse: {str(e)}")
                return False
            
            # Demodular o sinal
            try:
                print("Iniciando demodulação automática...")
                demodulated = mkf.demodulate(waveforms, ellipse_params)
                print(f"Demodulação automática concluída. Shape={demodulated.shape}")
            except Exception as e:
                try:
                    # Tentar implementação manual
                    print("Tentando demodulação manual...")
                    x, y = mkf.rescale(*waveforms, ellipse_params)
                    demodulated = np.unwrap(np.arctan2(y, x))
                    print(f"Demodulação manual concluída. Shape={demodulated.shape}")
                except Exception as e2:
                    print(f"Erro na demodulação automática: {str(e)}\nE na manual: {str(e2)}")
                    return False
            
            # Adicionar dados demodulados aos dados existentes
            self.demodulated_data = self.data.copy()
            self.demodulated_data['demodulated'] = demodulated
            self.demodulated_data['ellipse_params'] = ellipse_params
            
            # Plotar resultados
            self.plot_ellipse()
            self.plot_demodulated()
            self.plot_spectrum()
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Erro na demodulação automática: {str(e)}")
            return False
    
    def load_selected_file(self):
        """Carrega o arquivo selecionado"""
        if self.file_combo.count() == 0:
            return
        
        filename = self.file_combo.currentText()
        try:
            self.statusBar.showMessage(f"Carregando arquivo {filename}...")
            
            with open(filename, 'rb') as f:
                self.data = pickle.load(f)
            
            # Converter dicionário para dict se for necessário
            if not isinstance(self.data, dict):
                temp_dict = {}
                for key in dir(self.data):
                    if not key.startswith('__') and not callable(getattr(self.data, key)):
                        temp_dict[key] = getattr(self.data, key)
                self.data = temp_dict
                print("Convertido objeto para dicionário")
            
            # Verificar se já é um arquivo demodulado
            if 'demodulated' in self.data:
                self.demodulated_data = self.data
                print(f"Arquivo contém dados demodulados: {self.data['demodulated'].shape if isinstance(self.data['demodulated'], np.ndarray) else type(self.data['demodulated'])}")
            else:
                self.demodulated_data = None
                print("Arquivo não contém dados demodulados")
            
            # Verificar se temos dados de formas de onda
            if 'waveforms' not in self.data:
                QMessageBox.warning(self, "Aviso", "Arquivo não contém dados de formas de onda")
                return
                
            # Verificar se temos dados de tempo
            if 't' not in self.data:
                # Criar vetor de tempo se não existir
                if 'sample_frequency_effective' in self.data and 'waveforms' in self.data:
                    fs = self.data['sample_frequency_effective']
                    wf_len = self.data['waveforms'].shape[1]
                    self.data['t'] = np.arange(wf_len) / fs
                    print(f"Vetor de tempo criado: {wf_len} pontos")
                else:
                    QMessageBox.warning(self, "Aviso", "Impossível criar vetor de tempo")
                    return
            
            # Atualizar visualizações
            self.plot_raw_data()
            self.plot_ellipse()
            
            # Verificar se temos dados demodulados para plotar
            if self.demodulated_data and 'demodulated' in self.demodulated_data:
                try:
                    self.plot_demodulated()
                    self.plot_spectrum()
                    print("Dados demodulados plotados com sucesso")
                except Exception as e:
                    print(f"Erro ao plotar dados demodulados: {str(e)}")
                    self.statusBar.showMessage(f"Erro ao plotar dados demodulados: {str(e)}")
            
            self.statusBar.showMessage(f"Arquivo carregado: {filename}")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo: {str(e)}")
            self.statusBar.showMessage(f"Erro ao carregar arquivo")
    
    def plot_raw_data(self):
        """Plota os dados brutos"""
        if not self.data or 'waveforms' not in self.data:
            return
        
        ax = self.raw_canvas.axes
        ax.clear()
        
        # Obter dados e parâmetros
        waveforms = self.data['waveforms']
        t = self.data['t']
        channels = self.data.get('channels', [1, 2])
        
        # Verificar se os comprimentos coincidem
        if len(t) != waveforms.shape[1]:
            print(f"AVISO: Comprimentos diferentes - t: {len(t)}, waveforms: {waveforms.shape}")
            # Truncar ou expandir para corresponder ao tamanho menor
            min_len = min(len(t), waveforms.shape[1])
            t = t[:min_len]
            waveforms = waveforms[:, :min_len]
        
        # Limitar número de pontos para plotagem
        max_points = 10000
        if len(t) > max_points:
            step = len(t) // max_points
            t_plot = t[::step]
            waveforms_plot = waveforms[:, ::step]
        else:
            t_plot = t
            waveforms_plot = waveforms
        
        # Plotar cada canal
        colors = ['b', 'r', 'g', 'c']
        for i, channel in enumerate(channels):
            if i < len(waveforms_plot):
                ax.plot(t_plot, waveforms_plot[i], color=colors[i % len(colors)], 
                        label=f'Canal {channel}')
        
        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Dados Brutos')
        ax.legend()
        ax.grid(True)
        
        self.raw_canvas.draw()
    
    def plot_ellipse(self):
        """Plota o gráfico Lissajous (CH1 vs CH2)"""
        if not self.data or 'waveforms' not in self.data:
            return
        
        ax = self.ellipse_canvas.axes
        ax.clear()
        
        # Obter waveforms
        waveforms = self.data['waveforms']
        
        # Verificar se temos dois canais
        if waveforms.shape[0] < 2:
            ax.text(0.5, 0.5, "Necessários dois canais para o fit da elipse", 
                   ha='center', va='center')
            self.ellipse_canvas.draw()
            return
        
        # Limitar número de pontos para plot
        max_points = 5000
        if waveforms.shape[1] > max_points:
            step = waveforms.shape[1] // max_points
            waveforms_plot = waveforms[:, ::step]
        else:
            waveforms_plot = waveforms
        
        # Plotar os dados
        ax.scatter(waveforms_plot[0], waveforms_plot[1], s=1, alpha=0.3)
        
        # Se já temos dados demodulados, plotar a elipse ajustada
        if self.demodulated_data and 'ellipse_params' in self.demodulated_data:
            try:
                t = np.linspace(0, 2*np.pi, 200)
                ellipse_params = self.demodulated_data['ellipse_params']
                fitted_ellipse = mkf.rescale(np.sin(t), np.cos(t), ellipse_params, invert=True)
                ax.plot(fitted_ellipse[0], fitted_ellipse[1], 'r-', linewidth=2)
                
                # Mostrar parâmetros da elipse
                y_inc = 1000/2**13
                p, q, r, s, alpha = ellipse_params
                plt_text = (f"DC CH1: {p*y_inc:.0f} mV\n"
                            f"DC CH2: {q*y_inc:.0f} mV\n"
                            f"Raio: {s*y_inc:.0f} mV\n"
                            f"Excent: {r:.2f}\n"
                            f"Ângulo: {alpha*360/(2*np.pi):.1f}°")
                ax.text(0.05, 0.95, plt_text, transform=ax.transAxes, 
                        verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.5))
            except Exception as e:
                print(f"Erro ao plotar elipse ajustada: {str(e)}")
                self.statusBar.showMessage(f"Erro ao plotar elipse: {str(e)}")
        
        ax.set_xlabel('Canal 1')
        ax.set_ylabel('Canal 2')
        ax.set_title('Figura de Lissajous')
        ax.axis('equal')
        ax.grid(True)
        
        self.ellipse_canvas.draw()
    
    def demodulate_data(self):
        """Demodula os dados usando o fit de elipse"""
        if not self.data or 'waveforms' not in self.data:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado para demodular")
            return
        
        try:
            # Verificar se temos dois canais
            if self.data['waveforms'].shape[0] < 2:
                QMessageBox.warning(self, "Aviso", "Necessários dois canais para demodulação")
                return
            
            # Realizar fit da elipse
            self.statusBar.showMessage("Ajustando elipse...")
            waveforms = self.data['waveforms']
            
            # Limitar o número de pontos para o fit, se necessário
            max_fit_points = 100000  # ajustar conforme necessário
            if waveforms.shape[1] > max_fit_points:
                step = waveforms.shape[1] // max_fit_points
                waveforms_fit = waveforms[:, ::step]
                print(f"Usando {waveforms_fit.shape[1]} pontos para fit da elipse")
            else:
                waveforms_fit = waveforms
            
            try:
                print("Iniciando ajuste de elipse...")
                ellipse_params = mkf.fit_ellipse(*waveforms_fit)
                print(f"Parâmetros da elipse: {ellipse_params}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro no fit da elipse: {str(e)}")
                return
            
            # Demodular o sinal
            self.statusBar.showMessage("Demodulando sinal...")
            try:
                print("Iniciando demodulação com parâmetros:", ellipse_params)
                # Verificar se está passando dados na ordem correta
                if waveforms.shape[0] != 2:
                    print(f"AVISO: Formato de waveforms inesperado: {waveforms.shape}")
                
                # Tentar demodular com implementação manual se necessário
                try:
                    demodulated = mkf.demodulate(waveforms, ellipse_params)
                    print(f"Demodulação concluída com sucesso. Shape={demodulated.shape}, tipo={type(demodulated)}")
                    print(f"Valores: min={np.min(demodulated) if isinstance(demodulated, np.ndarray) else 'N/A'}, "
                          f"max={np.max(demodulated) if isinstance(demodulated, np.ndarray) else 'N/A'}")
                except AttributeError:
                    # Implementação manual caso falhe
                    print("Tentando demodulação manual...")
                    # Obter pontos normalizados
                    x, y = mkf.rescale(*waveforms, ellipse_params)
                    # Calcular fase
                    demodulated = np.unwrap(np.arctan2(y, x))
                    print(f"Demodulação manual concluída. Shape={demodulated.shape}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Erro", f"Erro na demodulação: {str(e)}")
                return
            
            # Criar cópia dos dados e adicionar dados demodulados
            self.demodulated_data = self.data.copy()
            self.demodulated_data['demodulated'] = demodulated
            self.demodulated_data['ellipse_params'] = ellipse_params
            
            # Verificar explicitamente se os dados foram armazenados corretamente
            if not isinstance(self.demodulated_data, dict):
                print(f"AVISO: demodulated_data não é um dicionário: {type(self.demodulated_data)}")
            if 'demodulated' not in self.demodulated_data:
                print(f"ERRO: 'demodulated' não foi armazenado no dicionário")
                print(f"Chaves disponíveis: {self.demodulated_data.keys() if hasattr(self.demodulated_data, 'keys') else 'N/A'}")
            else:
                print(f"Dados demodulados armazenados com sucesso.")
                if isinstance(self.demodulated_data['demodulated'], np.ndarray):
                    print(f"  - Shape: {self.demodulated_data['demodulated'].shape}")
                    print(f"  - Tipo: {self.demodulated_data['demodulated'].dtype}")
                    print(f"  - Amostra: {self.demodulated_data['demodulated'][0:5]}")
            
            # Atualizar visualizações
            self.plot_ellipse()
            try:
                print("Chamando plot_demodulated()...")
                self.plot_demodulated()
                print("Chamando plot_spectrum()...")
                self.plot_spectrum()
            except Exception as e:
                print(f"Erro ao plotar: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Perguntar se deseja salvar
            reply = QMessageBox.question(self, 'Salvar Dados', 
                                        'Deseja salvar os dados demodulados?',
                                        QMessageBox.Yes | QMessageBox.No, 
                                        QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                self.save_demodulated_data()
            
            self.statusBar.showMessage("Demodulação concluída")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Erro na demodulação: {str(e)}")
            self.statusBar.showMessage(f"Erro na demodulação")
    
    def save_demodulated_data(self):
        """Salva os dados demodulados em arquivo"""
        if not self.demodulated_data:
            return
        
        try:
            # Criar nome de arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vazamento_demodulado_{timestamp}.pkl"
            
            with open(filename, 'wb') as f:
                pickle.dump(self.demodulated_data, f)
            
            self.statusBar.showMessage(f"Dados demodulados salvos em {filename}")
            self.refresh_file_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar dados: {str(e)}")
    
    def plot_demodulated(self):
        """Plota o sinal demodulado"""
        ax = self.demod_canvas.axes
        ax.clear()
        
        # Verificar se temos dados para plotar
        if not self.demodulated_data:
            print("Sem dados demodulados disponíveis - demodulated_data é None")
            ax.text(0.5, 0.5, "Sem dados demodulados disponíveis.\nPrimeiro demodule os dados na aba 'Fit da Elipse'.", 
                   ha='center', va='center', fontsize=12)
            self.demod_canvas.draw()
            return
        
        if 'demodulated' not in self.demodulated_data:
            print(f"Chave 'demodulated' não encontrada em demodulated_data")
            print(f"Chaves disponíveis: {list(self.demodulated_data.keys())}")
            ax.text(0.5, 0.5, "Dados demodulados não encontrados.\nTente demodular novamente.", 
                   ha='center', va='center', fontsize=12)
            self.demod_canvas.draw()
            return
        
        try:
            # Obter dados
            demodulated = self.demodulated_data['demodulated']
            print(f"Tipo de dados demodulados: {type(demodulated)}")
            
            if not isinstance(demodulated, np.ndarray):
                print(f"Dados demodulados não são um array numpy: {type(demodulated)}")
                ax.text(0.5, 0.5, f"Formato de dados inválido: {type(demodulated)}", 
                       ha='center', va='center', fontsize=12)
                self.demod_canvas.draw()
                return
            
            print(f"Shape dos dados demodulados: {demodulated.shape}")
            
            # Verificar se temos dados de tempo
            if 't' not in self.demodulated_data:
                print("Vetor de tempo não encontrado - criando automaticamente")
                if 'sample_frequency_effective' in self.demodulated_data:
                    fs = self.demodulated_data['sample_frequency_effective']
                    self.demodulated_data['t'] = np.arange(len(demodulated)) / fs
                else:
                    # Criar um vetor de tempo artificial
                    self.demodulated_data['t'] = np.arange(len(demodulated))
                    print("AVISO: Usando vetor de tempo arbitrário")
            
            t = self.demodulated_data['t']
            print(f"Shape do vetor de tempo: {t.shape}")
            
            # Verificar se os comprimentos coincidem
            if len(t) != len(demodulated):
                print(f"AVISO: Comprimentos diferentes - t: {len(t)}, demodulated: {len(demodulated)}")
                # Truncar para o tamanho menor
                min_len = min(len(t), len(demodulated))
                t = t[:min_len]
                demodulated = demodulated[:min_len]
            
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
            print(f"Plotando {len(t_plot)} pontos")
            ax.plot(t_plot, demod_plot)
            ax.set_xlabel('Tempo (s)')
            ax.set_ylabel('Fase (rad)')
            ax.set_title('Sinal Demodulado')
            ax.grid(True)
            
            self.demod_canvas.draw()
            print("Gráfico demodulado plotado com sucesso")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Erro ao plotar dados demodulados: {str(e)}")
            # Limpar o gráfico e mostrar mensagem de erro
            ax.clear()
            ax.text(0.5, 0.5, f"Erro ao plotar: {str(e)}", ha='center', va='center')
            self.demod_canvas.draw()
    
    def plot_spectrum(self):
        """Plota o espectro de frequência do sinal demodulado"""
        ax = self.spectrum_canvas.axes
        ax.clear()
        
        # Verificar se temos dados para plotar
        if not self.demodulated_data:
            print("Sem dados demodulados disponíveis para espectro - demodulated_data é None")
            ax.text(0.5, 0.5, "Sem dados demodulados disponíveis.\nPrimeiro demodule os dados na aba 'Fit da Elipse'.", 
                   ha='center', va='center', fontsize=12)
            self.spectrum_canvas.draw()
            return
        
        if 'demodulated' not in self.demodulated_data:
            print(f"Chave 'demodulated' não encontrada para espectro")
            ax.text(0.5, 0.5, "Dados demodulados não encontrados.\nTente demodular novamente.", 
                   ha='center', va='center', fontsize=12)
            self.spectrum_canvas.draw()
            return
        
        try:
            # Obter dados
            demodulated = self.demodulated_data['demodulated']
            
            if not isinstance(demodulated, np.ndarray):
                print(f"Dados demodulados não são um array numpy para espectro: {type(demodulated)}")
                ax.text(0.5, 0.5, f"Formato de dados inválido: {type(demodulated)}", 
                       ha='center', va='center', fontsize=12)
                self.spectrum_canvas.draw()
                return
            
            # Verificar se temos taxa de amostragem efetiva
            if 'sample_frequency_effective' in self.demodulated_data:
                fs = self.demodulated_data['sample_frequency_effective']
                print(f"Usando sample_frequency_effective: {fs} Hz")
            elif 'sample_frequency' in self.demodulated_data and 'decimation' in self.demodulated_data:
                fs = self.demodulated_data['sample_frequency'] / self.demodulated_data['decimation']
                print(f"Calculando fs a partir de sample_frequency e decimation: {fs} Hz")
            else:
                # Tentar estimar a taxa de amostragem a partir do vetor de tempo
                if 't' in self.demodulated_data and len(self.demodulated_data['t']) >= 2:
                    t = self.demodulated_data['t']
                    dt = t[1] - t[0]
                    fs = 1 / dt
                    print(f"Estimando fs a partir do vetor de tempo: {fs} Hz (dt={dt}s)")
                else:
                    fs = 1e6  # Valor padrão
                    print(f"AVISO: Usando taxa de amostragem padrão: {fs} Hz")
            
            # Verificar se fs é válido
            if fs <= 0 or np.isnan(fs) or np.isinf(fs):
                print(f"Taxa de amostragem inválida: {fs}")
                fs = 1e6  # Valor seguro
                print(f"Usando valor padrão: {fs} Hz")
            
            # Calcular o espectro
            # Limitar o número de pontos para o cálculo do espectro
            max_points = 2**18  # ~250k pontos
            if len(demodulated) > max_points:
                step = len(demodulated) // max_points
                demod_decimated = demodulated[::step]
                fs_decimated = fs / step
                print(f"Decimando para espectro: {len(demod_decimated)} pontos (1:{step})")
            else:
                demod_decimated = demodulated
                fs_decimated = fs
                print(f"Usando todos os {len(demod_decimated)} pontos para espectro")
            
            # Parâmetros do espectro de potência
            nperseg = min(8192, len(demod_decimated)//4)
            if nperseg < 10:
                print("AVISO: Poucos pontos para cálculo de espectro")
                ax.text(0.5, 0.5, "Poucos pontos para calcular espectro", 
                       ha='center', va='center', fontsize=12)
                self.spectrum_canvas.draw()
                return
            
            print(f"Calculando espectro: fs={fs_decimated:.2f} Hz, nperseg={nperseg}, len={len(demod_decimated)}")
            
            # Verificar se os dados contêm NaN ou infinitos
            if np.isnan(demod_decimated).any() or np.isinf(demod_decimated).any():
                print("AVISO: Dados demodulados contêm NaN ou infinitos")
                # Substituir valores problemáticos
                demod_clean = np.copy(demod_decimated)
                demod_clean[np.isnan(demod_clean)] = 0
                demod_clean[np.isinf(demod_clean)] = 0
                print(f"Valores problemáticos substituídos: {np.sum(np.isnan(demod_decimated)) + np.sum(np.isinf(demod_decimated))}")
            else:
                demod_clean = demod_decimated
            
            # Calcular espectro
            f, Pxx = signal.welch(demod_clean, fs_decimated, nperseg=nperseg)
            
            # Verificar se o resultado é válido
            if np.isnan(Pxx).any() or np.isinf(Pxx).any() or (Pxx <= 0).any():
                print("AVISO: Espectro contém valores inválidos")
                # Filtrar valores inválidos
                mask = ~(np.isnan(Pxx) | np.isinf(Pxx) | (Pxx <= 0))
                f = f[mask]
                Pxx = Pxx[mask]
                if len(Pxx) == 0:
                    raise ValueError("Todos os valores do espectro são inválidos")
            
            # Converter para dB
            print(f"Convertendo para dB: min={np.min(Pxx)}, max={np.max(Pxx)}")
            Pxx_db = 10 * np.log10(Pxx)
            
            # Plotar
            ax.semilogx(f, Pxx_db)
            ax.set_xlabel('Frequência (Hz)')
            ax.set_ylabel('Densidade Espectral (dB)')
            ax.set_title(f'Espectro do Sinal Demodulado (Fs={fs_decimated/1e6:.2f} MHz)')
            ax.grid(True)
            
            self.spectrum_canvas.draw()
            print("Espectro plotado com sucesso")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Erro ao plotar espectro: {str(e)}")
            # Limpar o gráfico e mostrar mensagem de erro
            ax.clear()
            ax.text(0.5, 0.5, f"Erro ao plotar espectro: {str(e)}", ha='center', va='center')
            self.spectrum_canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OASGui()
    window.show()
    sys.exit(app.exec_()) 