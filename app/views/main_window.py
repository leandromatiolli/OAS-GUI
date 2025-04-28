"""
Módulo com a janela principal da aplicação
"""
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar, QMessageBox
from PyQt5.QtCore import Qt

from app.views.panels.acquisition_panel import AcquisitionPanel
from app.views.panels.metadata_panel import MetadataPanel
from app.views.panels.analysis_panel import AnalysisPanel

class MainWindow(QMainWindow):
    """Janela principal da aplicação OAS"""
    
    def __init__(self):
        """Inicializa a janela principal"""
        super().__init__()
        self.setWindowTitle("OAS - Interface de Aquisição e Análise")
        self.setMinimumSize(1000, 800)
        
        # Configurar a interface
        self.setup_ui()
    
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
        
        # Aba de Aquisição
        self.acquisition_panel = AcquisitionPanel()
        
        # Aba de Metadados
        self.metadata_panel = MetadataPanel()
        
        # Aba de Análise
        self.analysis_panel = AnalysisPanel()
        
        # Adicionar todas as abas
        self.tabs.addTab(self.acquisition_panel, "Aquisição")
        self.tabs.addTab(self.metadata_panel, "Metadados")
        self.tabs.addTab(self.analysis_panel, "Análise")
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
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
            index: Índice da aba (0 = Aquisição, 1 = Metadados, 2 = Análise)
        """
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index) 