#!/usr/bin/env python
"""
OAS - Interface de Aquisição e Análise
Programa principal para detecção e análise de vazamentos
"""
import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# Certificar-se de que os pacotes estão no path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes da aplicação
from app.views.main_window import MainWindow
from app.controllers.acquisition_controller import AcquisitionController
from app.controllers.processing_controller import ProcessingController
from app.controllers.file_controller import FileController
from app.models.hardware.redpitaya_client import RedPitayaClient

def exception_hook(exctype, value, tb):
    """
    Captura exceções não tratadas e exibe uma mensagem de erro
    
    Args:
        exctype: Tipo da exceção
        value: Valor da exceção
        tb: Traceback
    """
    error_message = ''.join(traceback.format_exception(exctype, value, tb))
    print(error_message)
    
    # Verificar se a aplicação ainda está em execução
    if QApplication.instance():
        error_dialog = QMessageBox()
        error_dialog.setWindowTitle("Erro")
        error_dialog.setText("Ocorreu um erro não tratado:")
        error_dialog.setDetailedText(error_message)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.exec_()
    else:
        print("Erro crítico: A aplicação já está encerrando")

class Application:
    """Classe principal da aplicação"""
    
    def __init__(self):
        """Inicializa a aplicação"""
        # Configurar hook para exceções não tratadas
        sys.excepthook = exception_hook
        
        # Criar a aplicação Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("OAS - Interface de Aquisição e Análise")
        
        # Inicializar controladores
        self.init_controllers()
        
        # Criar e configurar a janela principal
        self.init_window()
        
        # Conectar sinais e slots
        self.connect_signals()
        
        # Inicializar estado
        self.initialize_state()
    
    def init_controllers(self):
        """Inicializa os controladores da aplicação"""
        self.acquisition_controller = AcquisitionController()
        self.processing_controller = ProcessingController()
        self.file_controller = FileController()
    
    def init_window(self):
        """Inicializa a janela principal"""
        self.window = MainWindow()
    
    def connect_signals(self):
        """Conecta sinais e slots entre os componentes"""
        # Conexões do controlador de aquisição
        self.window.acquisition_panel.acquisitionRequested.connect(self.on_acquisition_requested)
        self.acquisition_controller.acquisitionStarted.connect(self.on_acquisition_started)
        self.acquisition_controller.acquisitionFinished.connect(self.on_acquisition_finished)
        self.acquisition_controller.acquisitionProgress.connect(self.window.show_status_message)
        self.acquisition_controller.acquisitionError.connect(self.on_acquisition_error)
        
        # Conexões do controlador de arquivos
        self.window.analysis_panel.fileSelected.connect(self.file_controller.load_file)
        self.window.analysis_panel.refreshFilesRequested.connect(self.file_controller.refresh_file_list)
        self.file_controller.fileListUpdated.connect(self.window.analysis_panel.update_file_list)
        self.file_controller.fileLoaded.connect(self.on_file_loaded)
        self.file_controller.fileError.connect(self.on_file_error)
        
        # Conexões do controlador de processamento
        self.window.analysis_panel.demodulateRequested.connect(self.processing_controller.demodulate_data)
        self.processing_controller.demodulationStarted.connect(self.on_demodulation_started)
        self.processing_controller.demodulationFinished.connect(self.on_demodulation_finished)
        self.processing_controller.demodulationError.connect(self.on_demodulation_error)
        self.processing_controller.processingProgress.connect(self.window.show_status_message)
    
    def initialize_state(self):
        """Inicializa o estado da aplicação"""
        # Verificar disponibilidade de hardware
        hardware_available = RedPitayaClient.is_available()
        self.window.acquisition_panel.set_enabled(hardware_available)
        
        if not hardware_available:
            self.window.show_status_message("Hardware de aquisição não disponível")
        
        # Carregar lista de arquivos
        self.file_controller.refresh_file_list()
    
    def on_acquisition_requested(self, params):
        """
        Manipula o evento de solicitação de aquisição
        
        Args:
            params: Parâmetros da aquisição
        """
        # Obter metadados
        metadata = self.window.metadata_panel.get_metadata()
        
        # Iniciar aquisição
        self.acquisition_controller.start_acquisition(params, metadata)
    
    def on_acquisition_started(self):
        """Manipula o evento de início de aquisição"""
        self.window.acquisition_panel.set_enabled(False)
        self.window.show_status_message("Aquisição em andamento...")
    
    def on_acquisition_finished(self, data):
        """
        Manipula o evento de conclusão de aquisição
        
        Args:
            data: Dados adquiridos
        """
        self.window.acquisition_panel.set_enabled(True)
        self.window.show_status_message("Aquisição concluída")
        
        # Processar dados automaticamente
        self.window.show_status_message("Realizando processamento automático...")
        success = self.processing_controller.auto_demodulate(data)
        
        if success:
            # Salvar dados com demodulação incluída
            try:
                filename = self.processing_controller.save_demodulated_data()
                self.window.show_status_message(f"Dados processados salvos em {filename}")
            except Exception as e:
                self.window.show_status_message(f"Erro ao salvar dados processados: {str(e)}")
        
        # Atualizar lista de arquivos e mudar para aba de análise
        self.file_controller.refresh_file_list()
        self.window.switch_to_tab(2)  # Mudar para a aba de análise (índice 2)
    
    def on_acquisition_error(self, message):
        """
        Manipula o evento de erro na aquisição
        
        Args:
            message: Mensagem de erro
        """
        self.window.acquisition_panel.set_enabled(True)
        self.window.show_error_message("Erro na Aquisição", message)
        self.window.show_status_message("Erro na aquisição")
    
    def on_file_loaded(self, data):
        """
        Manipula o evento de carregamento de arquivo
        
        Args:
            data: Dados carregados
        """
        self.window.show_status_message(f"Arquivo carregado")
        
        # Atualizar controlador de processamento com os novos dados
        self.processing_controller.set_data(data)
        
        # Atualizar visualizações
        try:
            # Verificar se temos dados de formas de onda
            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                self.window.analysis_panel.show_raw_data(data['t'], data['waveforms'], channels)
                
                # Verificar se temos dois canais para a elipse
                if data['waveforms'].shape[0] >= 2:
                    ellipse_params = data.get('ellipse_params', None)
                    self.window.analysis_panel.show_ellipse(data['waveforms'], ellipse_params)
                
            # Verificar se temos dados demodulados
            if 'demodulated' in data and 't' in data:
                self.window.analysis_panel.show_demodulated(data['t'], data['demodulated'])
                
                # Calcular e mostrar espectro
                try:
                    freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum()
                    self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks)
                except Exception as e:
                    self.window.show_status_message(f"Erro ao calcular espectro: {str(e)}")
                    
        except Exception as e:
            self.window.show_error_message("Erro ao Visualizar Dados", str(e))
    
    def on_file_error(self, message):
        """
        Manipula o evento de erro no carregamento de arquivo
        
        Args:
            message: Mensagem de erro
        """
        self.window.show_error_message("Erro no Arquivo", message)
    
    def on_demodulation_started(self):
        """Manipula o evento de início de demodulação"""
        self.window.show_status_message("Demodulação em andamento...")
    
    def on_demodulation_finished(self, data):
        """
        Manipula o evento de conclusão de demodulação
        
        Args:
            data: Dados demodulados
        """
        self.window.show_status_message("Demodulação concluída")
        
        # Atualizar visualizações
        try:
            if 'waveforms' in data and data['waveforms'].shape[0] >= 2:
                self.window.analysis_panel.show_ellipse(data['waveforms'], data.get('ellipse_params'))
                
            if 'demodulated' in data and 't' in data:
                self.window.analysis_panel.show_demodulated(data['t'], data['demodulated'])
                
                # Calcular e mostrar espectro
                freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum()
                self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks)
                
            # Perguntar se deseja salvar
            if self.window.show_question_message('Salvar Dados', 'Deseja salvar os dados demodulados?'):
                filename = self.processing_controller.save_demodulated_data()
                self.window.show_status_message(f"Dados demodulados salvos em {filename}")
                
        except Exception as e:
            self.window.show_error_message("Erro ao Visualizar Dados Demodulados", str(e))
    
    def on_demodulation_error(self, message):
        """
        Manipula o evento de erro na demodulação
        
        Args:
            message: Mensagem de erro
        """
        self.window.show_error_message("Erro na Demodulação", message)
    
    def run(self):
        """Executa a aplicação"""
        self.window.show()
        return self.app.exec_()

if __name__ == '__main__':
    app = Application()
    sys.exit(app.run()) 