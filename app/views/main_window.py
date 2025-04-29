"""
Módulo com a janela principal da aplicação
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                            QStatusBar, QMessageBox, QToolBar, QAction)
from PyQt5.QtCore import Qt, QSize

from app.views.panels.acquisition_panel import AcquisitionPanel
from app.views.panels.metadata_panel import MetadataPanel
from app.views.panels.analysis_panel import AnalysisPanel
from app.views.panels.log_panel import LogPanel
from app.utils.resources import get_icon, toggle_theme

class MainWindow(QMainWindow):
    """Janela principal da aplicação OAS"""
    
    def __init__(self):
        """Inicializa a janela principal"""
        super().__init__()
        self.setWindowTitle("OAS - Interface de Aquisição e Análise")
        self.setMinimumSize(1000, 800)
        
        # Definir ícone da aplicação
        self.setWindowIcon(get_icon("app_icon"))
        
        # Configurar a interface
        self.setup_ui()
        
        # Configurar a barra de ferramentas
        self.setup_toolbar()
    
    def setup_ui(self):
        """Configura a interface da janela principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Criar abas
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Aba de Metadados
        self.metadata_panel = MetadataPanel()
        
        # Aba de Aquisição
        self.acquisition_panel = AcquisitionPanel()
        
        # Aba de Análise
        self.analysis_panel = AnalysisPanel()
        
        # Aba de Logs
        self.log_panel = LogPanel()
        
        # Adicionar todas as abas
        self.tabs.addTab(self.metadata_panel, "Metadados")
        self.tabs.addTab(self.acquisition_panel, "Aquisição")
        self.tabs.addTab(self.analysis_panel, "Análise")
        self.tabs.addTab(self.log_panel, "Logs")
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def setup_toolbar(self):
        """Configura a barra de ferramentas"""
        # Criar barra de ferramentas principal
        self.toolbar = QToolBar("Barra de Ferramentas")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # Ação para aquisição
        self.action_acquisition = QAction(get_icon("acquisition"), "Aquisição", self)
        self.action_acquisition.setStatusTip("Realizar aquisição de dados")
        self.action_acquisition.triggered.connect(lambda: self.switch_to_tab(0))
        self.toolbar.addAction(self.action_acquisition)
        
        # Ação para análise
        self.action_analysis = QAction(get_icon("analysis"), "Análise", self)
        self.action_analysis.setStatusTip("Analisar dados")
        self.action_analysis.triggered.connect(lambda: self.switch_to_tab(2))
        self.toolbar.addAction(self.action_analysis)
        
        self.toolbar.addSeparator()
        
        # Ação para abrir arquivo
        self.action_open = QAction(get_icon("open"), "Abrir", self)
        self.action_open.setStatusTip("Abrir arquivo de dados")
        self.action_open.triggered.connect(self.on_open_file)
        self.toolbar.addAction(self.action_open)
        
        # Ação para salvar
        self.action_save = QAction(get_icon("save"), "Salvar", self)
        self.action_save.setStatusTip("Salvar dados")
        self.action_save.triggered.connect(self.on_save_file)
        self.toolbar.addAction(self.action_save)
        
        self.toolbar.addSeparator()
        
        # Ação para processar dados
        self.action_process = QAction(get_icon("process"), "Processar", self)
        self.action_process.setStatusTip("Processar dados")
        self.action_process.triggered.connect(self.on_process_data)
        self.toolbar.addAction(self.action_process)
        
        # Ação para atualizar
        self.action_refresh = QAction(get_icon("refresh"), "Atualizar", self)
        self.action_refresh.setStatusTip("Atualizar lista de arquivos")
        self.action_refresh.triggered.connect(self.on_refresh_files)
        self.toolbar.addAction(self.action_refresh)
        
        self.toolbar.addSeparator()
        
        # Ação para visualizar logs
        self.action_logs = QAction(get_icon("logs"), "Logs", self)
        self.action_logs.setStatusTip("Visualizar logs da aplicação")
        self.action_logs.triggered.connect(lambda: self.switch_to_tab(3))
        self.toolbar.addAction(self.action_logs)
        
        # Ação para alternar tema
        self.action_theme = QAction(get_icon("theme"), "Alternar Tema", self)
        self.action_theme.setStatusTip("Alternar entre tema claro e escuro")
        self.action_theme.triggered.connect(self.on_toggle_theme)
        self.toolbar.addAction(self.action_theme)
        
        # Ação para configurações
        self.action_settings = QAction(get_icon("settings"), "Configurações", self)
        self.action_settings.setStatusTip("Configurações")
        self.action_settings.triggered.connect(lambda: self.switch_to_tab(1))
        self.toolbar.addAction(self.action_settings)
    
    def on_open_file(self):
        """Manipula o evento de abrir arquivo"""
        self.switch_to_tab(2)  # Muda para a aba de análise
        self.analysis_panel.on_select_file()  # Abre o diálogo de selecionar arquivo
    
    def on_save_file(self):
        """Manipula o evento de salvar arquivo"""
        # Implementar conforme necessário
        self.show_status_message("Função de salvar não implementada")
    
    def on_process_data(self):
        """Manipula o evento de processar dados"""
        self.switch_to_tab(2)  # Muda para a aba de análise
        # Tenta demodular dados se disponíveis
        self.analysis_panel.on_demodulate()
    
    def on_refresh_files(self):
        """Manipula o evento de atualizar lista de arquivos"""
        self.switch_to_tab(2)  # Muda para a aba de análise
        self.analysis_panel.on_refresh_files()
    
    def on_toggle_theme(self):
        """Manipula o evento de alternar tema"""
        from PyQt5.QtWidgets import QApplication
        theme = toggle_theme(QApplication.instance())
        self.show_status_message(f"Tema alterado para: {theme}")
        
    def show_status_message(self, message, timeout=0):
        """
        Exibe uma mensagem na barra de status
        
        Args:
            message: Mensagem a ser exibida
            timeout: Tempo em milissegundos para a mensagem desaparecer (0 = permanente)
        """
        self.status_bar.showMessage(message, timeout)
        
    def show_error_message(self, title, message):
        """
        Exibe uma mensagem de erro
        
        Args:
            title: Título da mensagem
            message: Texto da mensagem
        """
        QMessageBox.critical(self, title, message)
        
    def show_warning_message(self, title, message):
        """
        Exibe uma mensagem de aviso
        
        Args:
            title: Título da mensagem
            message: Texto da mensagem
        """
        QMessageBox.warning(self, title, message)
        
    def show_info_message(self, title, message):
        """
        Exibe uma mensagem informativa
        
        Args:
            title: Título da mensagem
            message: Texto da mensagem
        """
        QMessageBox.information(self, title, message)
        
    def show_question_message(self, title, message):
        """
        Exibe uma mensagem de pergunta
        
        Args:
            title: Título da mensagem
            message: Texto da mensagem
            
        Returns:
            True se o usuário clicou em Sim, False caso contrário
        """
        reply = QMessageBox.question(self, title, message,
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.Yes)
        return reply == QMessageBox.Yes
    
    def switch_to_tab(self, index):
        """
        Muda para a aba especificada
        
        Args:
            index: Índice da aba (0 = Aquisição, 1 = Metadados, 2 = Análise, 3 = Logs)
        """
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index) 