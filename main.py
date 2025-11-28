#!/usr/bin/env python
"""
OAS - Interface de Aquisição e Análise
Programa principal para detecção e análise de vazamentos ...
"""
import sys
import os
import traceback

# Configurar matplotlib antes de importar PyQt5
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QApplication, QMessageBox
import numpy as np

# Certificar-se de que os pacotes estão no path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes da aplicação
from app.views.main_window import MainWindow
from app.controllers.acquisition_controller import AcquisitionController
from app.controllers.processing_controller import ProcessingController
from app.controllers.audio_controller import AudioController
from app.controllers.file_controller import FileController
from app.controllers.ultra_hear_controller import UltraHearController
from app.controllers.lora_controller import LoraController
from app.models.hardware.redpitaya_client import RedPitayaClient
# Importar módulo de recursos
from app.utils.resources import apply_stylesheet
# Importar módulo de logging
from app.utils.debug_log import set_gui_log_handler, log_debug, log_info, log_warning, log_error
from app.models.data_store import DataStore

def exception_hook(exctype, value, tb):
    """
    Captura exceções não tratadas e exibe uma mensagem de erro
    
    Args:
        exctype: Tipo da exceção
        value: Valor da exceção
        tb: Traceback
    """
    error_message = ''.join(traceback.format_exception(exctype, value, tb))
    log_error(f"Exceção não tratada: {error_message}")
    
    # Verificar se a aplicação ainda está em execução
    if QApplication.instance():
        error_dialog = QMessageBox()
        error_dialog.setWindowTitle("Erro")
        error_dialog.setText("Ocorreu um erro não tratado:")
        error_dialog.setDetailedText(error_message)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.exec_()
    else:
        log_error("Erro crítico: A aplicação já está encerrando")

class Application:
    """Classe principal da aplicação"""
    
    def __init__(self):
        """Inicializa a aplicação"""
        # Configurar hook para exceções não tratadas
        sys.excepthook = exception_hook
        
        # Criar a aplicação Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("OAS - Interface de Aquisição e Análise")
        
        # Aplicar folha de estilo
        apply_stylesheet(self.app)
        
        # Inicializar controladores
        self.init_controllers()
        
        # Criar e configurar a janela principal
        self.init_window()
        
        # Configurar sistema de logging
        self.setup_logging()
        
        # Conectar sinais e slots
        self.connect_signals()
        
        # Inicializar estado
        self.initialize_state()
    
    def setup_logging(self):
        """Configurar sistema de logging"""
        # Definir o manipulador para atualizar o log na GUI
        set_gui_log_handler(self.window.log_panel.append_log)
        log_info("Sistema de logging inicializado")
    
    def init_controllers(self):
        """Inicializa os controladores da aplicação"""
        self.processing_controller = ProcessingController()
        self.acquisition_controller = AcquisitionController(processing_controller=self.processing_controller)
        self.file_controller = FileController()
        self.audio_controller = AudioController()
        self.ultra_hear_controller = UltraHearController()
        self.lora_controller = LoraController()
    
    def init_window(self):
        """Inicializa a janela principal"""
        self.window = MainWindow()
    
    def connect_signals(self):
        """Conecta sinais e slots entre os componentes"""
        # Conexões do controlador de aquisição
        self.window.acquisition_panel.acquisitionRequested.connect(self.on_acquisition_requested)
        self.window.acquisition_panel.calibrationFileSelected.connect(self.file_controller.set_current_calibration)
        self.window.acquisition_panel.calibrationFolderChanged.connect(self.file_controller.set_calibration_directory)
        self.acquisition_controller.acquisitionStarted.connect(self.on_acquisition_started)
        self.acquisition_controller.acquisitionFinished.connect(self.on_acquisition_finished)
        self.acquisition_controller.calibrationFinished.connect(self.on_calibration_finished)
        self.acquisition_controller.acquisitionProgress.connect(self.window.show_status_message)
        self.acquisition_controller.acquisitionError.connect(self.on_acquisition_error)
        
        # Conexões para aquisições automáticas
        self.window.acquisition_panel.automaticAcquisitionRequested.connect(self.on_automatic_acquisition_requested)
        self.window.acquisition_panel.cancelAutomaticAcquisitionRequested.connect(self.on_cancel_automatic_acquisition_requested)
        self.acquisition_controller.automaticAcquisitionStarted.connect(self.on_automatic_acquisition_started)
        self.acquisition_controller.automaticAcquisitionFinished.connect(self.on_automatic_acquisition_finished)
        self.acquisition_controller.automaticAcquisitionProgress.connect(self.on_automatic_acquisition_progress)
        
        # Conexões do controlador de arquivos
        self.window.analysis_panel.fileSelected.connect(self.on_files_selected)
        self.window.analysis_panel.refreshFilesRequested.connect(self.file_controller.refresh_file_list)
        self.file_controller.fileListUpdated.connect(self.window.analysis_panel.update_file_list)
        self.file_controller.fileLoaded.connect(self.on_file_loaded)
        self.file_controller.fileError.connect(self.on_file_error)
        self.file_controller.calibrationStatusChanged.connect(self.window.acquisition_panel.update_calibration_status)
        self.file_controller.calibrationListUpdated.connect(self.window.acquisition_panel.update_calibration_list)
        self.file_controller.calibrationDataLoaded.connect(self.processing_controller.set_calibration_data)
        
        # Conexões do controlador de processamento
        self.window.analysis_panel.demodulateRequested.connect(self.processing_controller.demodulate_data)
        self.processing_controller.demodulationStarted.connect(self.on_demodulation_started)
        self.processing_controller.demodulationFinished.connect(self.on_demodulation_finished)
        self.processing_controller.demodulationError.connect(self.on_demodulation_error)
        self.processing_controller.processingProgress.connect(self.window.show_status_message)
        
        # Conexão para configuração de média móvel
        self.window.analysis_panel.movingAverageChanged.connect(self.processing_controller.set_moving_average)
        self.processing_controller.movingAverageApplied.connect(self.on_moving_average_applied)
        
        # Conexão para configuração do filtro passa-banda
        self.window.analysis_panel.bandpassFilterChanged.connect(self.processing_controller.set_bandpass_filter)
        self.processing_controller.bandpassFilterApplied.connect(self.on_bandpass_filter_applied)
        
        # Conexão para geração de espectrograma
        self.window.analysis_panel.spectrogramRequested.connect(self.processing_controller.generate_spectrogram)
        self.processing_controller.spectrogramGenerated.connect(self.on_spectrogram_generated)
        
        # Conexões do controlador de áudio
        self.window.audio_analysis_panel.audioFileSelected.connect(self.audio_controller.load_audio_file)
        self.window.audio_analysis_panel.generateAudioRequested.connect(self.audio_controller.generate_audio)
        self.window.audio_analysis_panel.playAudioRequested.connect(self.on_play_audio_from_audio_panel)
        self.audio_controller.audioLoaded.connect(self.on_audio_file_loaded)
        self.audio_controller.audioGenerated.connect(self.on_audio_generated_from_audio_panel)
        self.audio_controller.audioError.connect(self.on_audio_error)
        self.audio_controller.spectrumCalculated.connect(self.on_spectrum_calculated_for_audio)
        
        # Conexões do controlador Ultra-Hear
        self.window.ultra_hear_panel.audioFileSelected.connect(self.ultra_hear_controller.load_audio_file)
        self.window.ultra_hear_panel.processUltrasonicRequested.connect(self.ultra_hear_controller.process_ultrasonic_audio)
        self.window.ultra_hear_panel.playProcessedAudioRequested.connect(self.on_play_ultra_hear_audio)
        self.ultra_hear_controller.dataLoaded.connect(self.on_ultra_hear_data_loaded)
        self.ultra_hear_controller.processingFinished.connect(self.on_ultra_hear_processing_finished)
        self.ultra_hear_controller.processingError.connect(self.on_ultra_hear_error)
        
        # Conexões do controlador LoRa
        self.window.acquisition_panel.loraLigarRequested.connect(self.on_lora_ligar_requested)
        self.window.acquisition_panel.loraDesligarRequested.connect(self.on_lora_desligar_requested)
        self.lora_controller.loraStatusChanged.connect(self.window.acquisition_panel.update_lora_status)
        # Removido: self.lora_controller.loraError.connect(self.on_lora_error)
    
    def initialize_state(self):
        """Inicializa o estado da aplicação"""
        # Verificar disponibilidade de hardware
        hardware_available = RedPitayaClient.is_available()
        self.window.acquisition_panel.set_enabled(hardware_available)
        
        if not hardware_available:
            log_warning("Hardware de aquisição não disponível")
            self.window.show_status_message("Hardware de aquisição não disponível")
        
        # Carregar configurações de diretórios
        config = DataStore.load_config()
        
        # Carregar diretório de calibração
        calib_folder = config.get('calibration_directory')
        if not calib_folder:
            # If not set, use default path from user request
            calib_folder = 'data/Calibrações'
            # Let's save it back to config
            config['calibration_directory'] = calib_folder
            DataStore.save_config(config)
        self.window.acquisition_panel.set_calibration_folder(calib_folder)
        
        # Carregar diretório de salvamento de dados
        save_dir = config.get('save_directory')
        if save_dir:
            self.window.acquisition_panel.set_save_directory(save_dir)

        # Carregar lista de arquivos
        self.file_controller.refresh_file_list()
        
        # Inicializar lista de portas LoRa
        ports = self.lora_controller.get_available_ports()
        self.window.acquisition_panel.update_lora_ports(ports)
        log_info("Lista de portas LoRa inicializada")
        
    def on_acquisition_requested(self, params):
        """
        Manipula o evento de solicitação de aquisição
        
        Args:
            params: Parâmetros da aquisição
        """
        log_info(f"Solicitação de aquisição recebida: {params}")
        
        # Verificar se é uma calibração
        is_calibration = params.get('is_calibration', False)
        if is_calibration:
            log_info("Modo de calibração selecionado")
            self.window.show_status_message("Iniciando aquisição para calibração...")
        else:
            # Verificar se temos uma calibração válida
            if not self.processing_controller.has_calibration_data():
                log_warning("Tentativa de aquisição sem calibração prévia")
                if QMessageBox.question(
                    self.window, 
                    "Calibração não encontrada", 
                    "Não foi encontrada uma calibração válida. Deseja continuar com a aquisição sem calibração?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.No:
                    log_info("Aquisição cancelada pelo usuário devido à falta de calibração")
                    return
                log_info("Usuário optou por continuar sem calibração")
        
        # Resetar as configurações de filtro e espectrograma na interface
        self.window.analysis_panel.reset_bandpass_filter()
        self.window.analysis_panel.reset_spectrogram()
        
        # Obter metadados
        metadata = self.window.metadata_panel.get_metadata()
        
        # Adicionar diretório de salvamento do painel de aquisição se configurado
        # (sobrescreve o do painel de metadados se existir)
        save_dir = self.window.acquisition_panel.get_save_directory()
        if save_dir:
            metadata['save_directory'] = save_dir
        
        # Iniciar aquisição
        self.acquisition_controller.start_acquisition(params, metadata)
    
    def on_acquisition_started(self):
        """Manipula o evento de início de aquisição"""
        log_info("Aquisição iniciada")
        self.window.acquisition_panel.set_enabled(False)
        self.window.show_status_message("Aquisição em andamento...")
    
    def on_calibration_finished(self, data):
        """
        Manipula o evento de conclusão de calibração
        
        Args:
            data: Dados de calibração adquiridos
        """
        log_info("Calibração concluída, processando dados de calibração...")
        self.window.acquisition_panel.set_enabled(True)
        self.window.show_status_message("Processando dados de calibração...")
        
        # Verificar se temos nome de arquivo específico
        calibration_file = data.get('calibration_file')
        if calibration_file:
            log_info(f"Usando arquivo de calibração especificado: {calibration_file}")
        
        # Processar os dados de calibração
        success = self.processing_controller.process_calibration_data(data)
        
        if success:
            log_info("Calibração processada com sucesso")
            self.window.show_status_message("Calibração concluída com sucesso")
            
            # Atualizar lista de calibrações e status
            self.file_controller.refresh_calibration_list()
            
            # Mudar para a aba de análise
            self.window.switch_to_tab(2)
            
            # Exibir os dados brutos da calibração
            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                waveforms = data['waveforms']
                self.window.analysis_panel.show_raw_data(data['t'], waveforms, channels)
                
                # Verificar se temos dois canais para a elipse
                if waveforms.shape[0] >= 2:
                    ellipse_params = data.get('ellipse_params')
                    if not ellipse_params and self.processing_controller.has_calibration_data():
                        ellipse_params = self.processing_controller.calibration_data['ellipse_params']
                    
                    if ellipse_params:
                        log_info("Exibindo elipse da calibração")
                        log_debug(f"Tipo dos parâmetros da elipse: {type(ellipse_params)}")
                        if isinstance(ellipse_params, dict):
                            log_debug(f"Conteúdo dos parâmetros: {ellipse_params}")
                            for key, value in ellipse_params.items():
                                log_debug(f"  {key}: {value} (tipo: {type(value)})")
                        self.window.analysis_panel.show_ellipse(waveforms, ellipse_params)

                        # Tentar demodular automaticamente após calibração
                        log_info("Iniciando demodulação automática após calibração...")
                        # Iniciar demodulação automaticamente
                        self.processing_controller.demodulate_data()
        else:
            log_error("Falha no processamento da calibração")
            self.window.show_error_message(
                "Erro de Calibração",
                "Não foi possível processar os dados de calibração. Verifique o log para mais detalhes."
            )
    
    def on_acquisition_finished(self, data):
        """
        Manipula o evento de conclusão de aquisição
        
        Args:
            data: Dados adquiridos
        """
        log_info("Aquisição concluída com sucesso")
        self.window.acquisition_panel.set_enabled(True)
        self.window.show_status_message("Aquisição concluída")
        
        # Mudar para a aba de análise
        self.window.switch_to_tab(2)
        
        # ETAPA 1: Mostrar dados brutos adquiridos
        try:
            # Verificar o conteúdo dos dados
            log_debug("Conteúdo dos dados adquiridos:")
            if 'waveforms' in data:
                log_debug(f"- Waveforms: shape={data['waveforms'].shape}")
            else:
                log_warning("- Waveforms: não encontrado")
                
            if 't' in data:
                log_debug(f"- Vetor de tempo: length={len(data['t'])}")
            else:
                log_warning("- Vetor de tempo: não encontrado")
                
            if 'channels' in data:
                log_debug(f"- Canais: {data['channels']}")
            else:
                log_warning("- Canais: não encontrado")
            
            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                log_info(f"Exibindo dados brutos: canais {channels}")
                
                # Usar as formas de onda diretamente dos dados
                waveforms = data['waveforms']
                self.window.analysis_panel.show_raw_data(data['t'], waveforms, channels)
                
                # Verificar se temos dois canais para a elipse
                if waveforms.shape[0] >= 2:
                    # Usar parâmetros da elipse da calibração carregada
                    ellipse_params = None
                    if self.processing_controller.has_calibration_data():
                        ellipse_params = self.processing_controller.calibration_data.get('ellipse_params')
                        log_info("Exibindo elipse da calibração carregada")
                        log_debug(f"Tipo dos parâmetros da elipse (calibração): {type(ellipse_params)}")
                        if isinstance(ellipse_params, dict):
                            log_debug(f"Conteúdo dos parâmetros (calibração): {ellipse_params}")
                            for key, value in ellipse_params.items():
                                log_debug(f"  {key}: {value} (tipo: {type(value)})")
                    else:
                        # Fallback para parâmetros dos dados (se existirem)
                        ellipse_params = data.get('ellipse_params', None)
                        if ellipse_params:
                            log_info("Exibindo elipse dos dados adquiridos")
                            log_debug(f"Tipo dos parâmetros da elipse (dados): {type(ellipse_params)}")
                            if isinstance(ellipse_params, dict):
                                log_debug(f"Conteúdo dos parâmetros (dados): {ellipse_params}")
                                for key, value in ellipse_params.items():
                                    log_debug(f"  {key}: {value} (tipo: {type(value)})")
                        else:
                            log_warning("Nenhuma elipse disponível para exibição")

                    if ellipse_params:
                        self.window.analysis_panel.show_ellipse(waveforms, ellipse_params)
            else:
                log_warning("Não foi possível exibir dados brutos: waveforms ou vetor de tempo ausentes")
                
            # Selecionar a aba de dados brutos no painel de análise
            self.window.analysis_panel.analysis_tabs.setCurrentIndex(0)
            
        except Exception as e:
            log_error(f"Erro ao exibir dados brutos: {str(e)}")
            self.window.show_status_message(f"Erro ao exibir dados brutos: {str(e)}")
        
        # ETAPA 2: Configurar dados para processamento e tentar demodular automaticamente
        try:
            log_info("Configurando dados para processamento...")
            self.processing_controller.set_data(data)
            log_info("Dados configurados para processamento")
            
            # Tentar demodular automaticamente se temos dados de calibração
            if self.processing_controller.has_calibration_data():
                log_info("Iniciando demodulação automática após aquisição...")
                # Iniciar demodulação automaticamente
                self.processing_controller.demodulate_data()
            else:
                log_warning("Não há dados de calibração disponíveis para demodulação automática")
                
        except Exception as e:
            log_error(f"Erro ao configurar dados para processamento: {str(e)}")
            self.window.show_status_message(f"Erro ao configurar dados: {str(e)}")
        
        # ETAPA 3: Atualizar lista de arquivos
        try:
            log_debug("Atualizando lista de arquivos...")
            self.file_controller.refresh_file_list()
        except Exception as e:
            log_error(f"Erro ao atualizar lista de arquivos: {str(e)}")
    
    def on_acquisition_error(self, message):
        """
        Manipula o evento de erro na aquisição
        
        Args:
            message: Mensagem de erro
        """
        log_error(f"Erro na aquisição: {message}")
        self.window.acquisition_panel.set_enabled(True)
        self.window.show_error_message("Erro na Aquisição", message)
        self.window.show_status_message("Erro na aquisição")
    
    def on_file_loaded(self, data):
        """
        Manipula o evento de carregamento de arquivo
        
        Args:
            data: Dados carregados
        """
        log_info(f"Arquivo carregado com sucesso")
        self.window.show_status_message(f"Arquivo carregado")
        
        # Exibir metadados do arquivo
        if 'metadata' in data:
            log_debug(f"Exibindo metadados do arquivo: {data['metadata']}")
            self.window.analysis_panel.show_metadata(data['metadata'])
        else:
            log_debug("Arquivo não contém metadados")
            self.window.analysis_panel.show_metadata(None)
        
        # Atualizar controlador de processamento com os novos dados
        self.processing_controller.set_data(data)
        
        # Atualizar visualizações
        try:
            # Verificar se temos dados de formas de onda
            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                
                # Obter formas de onda processadas (com ou sem média móvel)
                waveforms = self.processing_controller.get_waveforms_for_processing()
                log_debug(f"Exibindo dados brutos do arquivo (shape={waveforms.shape})")
                self.window.analysis_panel.show_raw_data(data['t'], waveforms, channels)
                
                # Verificar se temos dois canais para a elipse
                if waveforms.shape[0] >= 2:
                    ellipse_params = data.get('ellipse_params', None)
                    log_debug("Exibindo elipse do arquivo")
                    self.window.analysis_panel.show_ellipse(waveforms, ellipse_params)
                
            # Verificar se temos dados demodulados ou tentar demodular automaticamente
            demodulated_data = None
            if 'demodulated' in data and 't' in data:
                log_debug("Exibindo dados demodulados do arquivo")
                demodulated_data = data['demodulated']
                self.window.analysis_panel.show_demodulated(data['t'], demodulated_data)
            else:
                # Tentar demodular automaticamente usando os parâmetros da elipse do arquivo
                log_debug("Tentando demodular dados automaticamente com parâmetros da elipse do arquivo")
                try:
                    # Verificar se temos parâmetros da elipse nos metadados
                    metadata = data.get('metadata', {})
                    has_ellipse_in_metadata = False

                    if 'calibration_info' in metadata and metadata['calibration_info'].get('ellipse_params'):
                        log_info("Encontrados parâmetros da elipse nos metadados TOML")
                        has_ellipse_in_metadata = True
                    elif 'ellipse_params' in metadata:
                        log_info("Encontrados parâmetros da elipse nos metadados (formato antigo)")
                        has_ellipse_in_metadata = True

                    if has_ellipse_in_metadata:
                        log_info("Iniciando demodulação automática com parâmetros da elipse do arquivo...")
                        # Iniciar demodulação que usará os parâmetros da elipse dos metadados
                        self.processing_controller.demodulate_data()
                    else:
                        log_warning("Arquivo não contém parâmetros da elipse nos metadados - não é possível demodular automaticamente")
                except Exception as e:
                    log_error(f"Erro na demodulação automática: {str(e)}")
                
                # Verificar se temos dados filtrados
                if 'filtered_demodulated' in data and 'bandpass_params' in data:
                    log_debug("Exibindo dados filtrados do arquivo")
                    self.window.analysis_panel.show_filtered(
                        data['t'], 
                        data['filtered_demodulated'],
                        data['bandpass_params']
                    )
                    
                    # Atualizar a interface de filtro passa-banda com os parâmetros salvos no arquivo
                    params = data['bandpass_params']
                    if 'enabled' in params and 'low_freq' in params and 'high_freq' in params and 'order' in params:
                        # Atualizar a interface sem emitir sinais (será feito manualmente)
                        self.window.analysis_panel.bandpass_checkbox.setChecked(params['enabled'])
                        self.window.analysis_panel.low_freq_spinbox.setValue(params['low_freq'])
                        self.window.analysis_panel.high_freq_spinbox.setValue(params['high_freq'])
                        self.window.analysis_panel.order_spinbox.setValue(params['order'])
                        
                        # Habilitar/desabilitar os spinboxes conforme necessário
                        self.window.analysis_panel.low_freq_spinbox.setEnabled(params['enabled'])
                        self.window.analysis_panel.high_freq_spinbox.setEnabled(params['enabled'])
                        self.window.analysis_panel.order_spinbox.setEnabled(params['enabled'])
                        self.window.analysis_panel.apply_filter_button.setEnabled(params['enabled'])
                
                # Calcular e mostrar espectro
                try:
                    # Verificar se devemos usar o sinal filtrado para o espectro
                    use_filtered = 'filtered_demodulated' in data and data.get('bandpass_params', {}).get('enabled', False)
                    log_debug(f"Calculando espectro dos dados carregados (use_filtered={use_filtered})")
                    freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum(use_filtered=use_filtered)
                    self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks, use_filtered=use_filtered)
                except Exception as e:
                    log_error(f"Erro ao calcular espectro: {str(e)}")
                    
        except Exception as e:
            log_error(f"Erro ao exibir dados carregados: {str(e)}")
            self.window.show_status_message(f"Erro ao exibir dados: {str(e)}")
    
    def on_file_error(self, message):
        """
        Manipula o evento de erro no carregamento de arquivo
        
        Args:
            message: Mensagem de erro
        """
        log_error(f"Erro ao carregar arquivo: {message}")
        self.window.show_error_message("Erro no Arquivo", message)
    
    def on_demodulation_started(self):
        """Manipula o evento de início de demodulação"""
        log_info("Demodulação iniciada")
        self.window.show_status_message("Demodulação em andamento...")
    
    def on_demodulation_finished(self, data):
        """
        Manipula o evento de conclusão da demodulação
        
        Args:
            data: Dados demodulados
        """
        log_info("Demodulação concluída com sucesso")
        self.window.show_status_message("Demodulação concluída")
        
        # Verificar se o filtro deve ser aplicado automaticamente
        apply_filter = data.get('bandpass_params', {}).get('enabled', False)
        
        # Atualizar visualizações com os dados demodulados
        try:
            # Certificar-se que temos formas de onda e elipse para mostrar
            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                log_debug("Atualizando gráfico de dados brutos após demodulação")
                self.window.analysis_panel.show_raw_data(data['t'], data['waveforms'], channels)
                
                if 'ellipse_params' in data and data['waveforms'].shape[0] >= 2:
                    log_debug("Atualizando gráfico de elipse após demodulação")
                    self.window.analysis_panel.show_ellipse(data['waveforms'], data['ellipse_params'])
                    
            # Mostrar dados demodulados
            if 'demodulated' in data and 't' in data:
                log_debug("Atualizando gráfico de sinal demodulado")
                self.window.analysis_panel.show_demodulated(data['t'], data['demodulated'])
                
                # Mostrar sinal filtrado, se disponível e se o filtro estiver ativado
                if apply_filter and 'filtered_demodulated' in data and 'bandpass_params' in data:
                    log_debug("Atualizando gráfico de sinal filtrado")
                    self.window.analysis_panel.show_filtered(
                        data['t'], 
                        data['filtered_demodulated'],
                        data['bandpass_params']
                    )
                
                # Calcular e mostrar espectro
                try:
                    # Se o filtro estiver ativado, mostrar o espectro do sinal filtrado
                    use_filtered = apply_filter and 'filtered_demodulated' in data
                    log_debug(f"Calculando e atualizando espectro após demodulação (use_filtered={use_filtered})")
                    freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum(use_filtered=use_filtered)
                    self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks, use_filtered=use_filtered)
                except Exception as e:
                    log_error(f"Erro ao calcular espectro: {str(e)}")
                
                # Ir para a aba de sinal demodulado ou filtrado conforme apropriado
                if apply_filter and 'filtered_demodulated' in data:
                    self.window.analysis_panel.analysis_tabs.setCurrentIndex(3)  # Aba de sinal filtrado
                else:
                    self.window.analysis_panel.analysis_tabs.setCurrentIndex(2)  # Aba de sinal demodulado
                    log_info("Navegando automaticamente para a aba de dados demodulados")
                
        except Exception as e:
            log_error(f"Erro ao exibir dados demodulados: {str(e)}")
            self.window.show_status_message(f"Erro ao exibir dados demodulados: {str(e)}")
    
    def on_demodulation_error(self, message):
        """
        Manipula o evento de erro na demodulação
        
        Args:
            message: Mensagem de erro
        """
        log_error(f"Erro na demodulação: {message}")
        self.window.show_error_message("Erro na Demodulação", message)
    
    def on_moving_average_applied(self, data):
        """
        Manipula o evento de aplicação de média móvel
        
        Args:
            data: Dados com média móvel aplicada
        """
        log_info("Média móvel aplicada aos dados")
        try:
            # Atualizar visualizações com os dados processados com média móvel
            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                log_debug(f"Atualizando gráfico de dados brutos após aplicação de média (shape={data['waveforms'].shape})")
                self.window.analysis_panel.show_raw_data(data['t'], data['waveforms'], channels)
                
                # Verificar se temos dois canais para a elipse
                if data['waveforms'].shape[0] >= 2:
                    ellipse_params = data.get('ellipse_params', None)
                    log_debug("Atualizando gráfico de elipse após aplicação de média")
                    self.window.analysis_panel.show_ellipse(data['waveforms'], ellipse_params)
                
                # Se temos dados demodulados, atualizar o espectro
                if 'demodulated' in data:
                    try:
                        # Calcular e mostrar espectro
                        use_filtered = 'filtered_demodulated' in data and data.get('bandpass_params', {}).get('enabled', False)
                        log_debug(f"Atualizando espectro após aplicação de média (use_filtered={use_filtered})")
                        freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum(use_filtered=use_filtered)
                        self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks, use_filtered=use_filtered)
                    except Exception as e:
                        log_error(f"Erro ao atualizar espectro: {str(e)}")
            
            self.window.show_status_message("Média móvel aplicada aos dados")
                
        except Exception as e:
            log_error(f"Erro ao aplicar média móvel: {str(e)}")
            self.window.show_status_message(f"Erro ao aplicar média móvel: {str(e)}")
    
    def on_bandpass_filter_applied(self, data):
        """
        Manipula o evento de aplicação do filtro passa-banda
        
        Args:
            data: Dados com filtro passa-banda aplicado
        """
        log_info("Filtro passa-banda aplicado aos dados")
        log_debug(f"on_bandpass_filter_applied: Chaves disponíveis nos dados: {list(data.keys())}")
        
        # Função de diagnóstico - verificar todos os dados recebidos
        self.diagnose_filtered_data(data)
        
        try:
            # Verificar se o filtro está ativado
            filter_enabled = data.get('bandpass_params', {}).get('enabled', False)
            
            if 't' in data:
                # SEMPRE manter a aba demodulado com o sinal original (sem filtro)
                if 'demodulated' in data:
                    log_debug("on_bandpass_filter_applied: Mantendo sinal original na aba demodulado")
                    self.window.analysis_panel.show_demodulated(data['t'], data['demodulated'])
                
                if filter_enabled and 'filtered_demodulated' in data:
                    # Quando o filtro está ativado, mostrar o sinal filtrado apenas na aba de sinal filtrado
                    log_debug(f"on_bandpass_filter_applied: Mostrando sinal filtrado na aba de sinal filtrado")
                    log_debug(f"on_bandpass_filter_applied: Tamanho do sinal filtrado: {len(data['filtered_demodulated'])}")
                    
                    # Mostrar na aba de sinal filtrado
                    self.window.analysis_panel.show_filtered(
                        data['t'], 
                        data['filtered_demodulated'],
                        data['bandpass_params']
                    )
                    
                    # Calcular e mostrar espectro do sinal filtrado
                    try:
                        log_debug("Calculando espectro do sinal filtrado")
                        freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum(use_filtered=True)
                        self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks, use_filtered=True)
                    except Exception as e:
                        log_error(f"Erro ao calcular espectro do sinal filtrado: {str(e)}")
                    
                elif not filter_enabled:
                    # Quando o filtro está desativado, limpar a aba de sinal filtrado
                    log_debug("on_bandpass_filter_applied: Filtro desativado, limpando aba de sinal filtrado")
                    self.window.analysis_panel.filtered_canvas.axes.clear()
                    self.window.analysis_panel.filtered_canvas.axes.text(0.5, 0.5, 'Filtro passa-banda desativado', 
                                                                         ha='center', va='center', transform=self.window.analysis_panel.filtered_canvas.axes.transAxes)
                    self.window.analysis_panel.filtered_canvas.draw()
                    
                    # Calcular e mostrar espectro do sinal original
                    try:
                        log_debug("Calculando espectro do sinal original")
                        freq_axis, magnitudes, peaks = self.processing_controller.calculate_spectrum(use_filtered=False)
                        self.window.analysis_panel.show_spectrum(freq_axis, magnitudes, peaks, use_filtered=False)
                    except Exception as e:
                        log_error(f"Erro ao calcular espectro do sinal original: {str(e)}")
                else:
                    log_warning(f"on_bandpass_filter_applied: Dados incompletos para exibir sinal filtrado")
                    if 'filtered_demodulated' not in data:
                        log_warning("  - Sinal filtrado não encontrado")
            else:
                log_warning("on_bandpass_filter_applied: Vetor de tempo não encontrado")
            
            status_msg = "Filtro passa-banda aplicado aos dados" if filter_enabled else "Filtro passa-banda desativado"
            self.window.show_status_message(status_msg)
                
        except Exception as e:
            log_error(f"Erro ao aplicar filtro passa-banda: {str(e)}")
            self.window.show_status_message(f"Erro ao aplicar filtro passa-banda: {str(e)}")
            
    def on_spectrogram_generated(self, data, t, freqs, Sxx):
        """
        Manipula o evento de geração do espectrograma
        
        Args:
            data: Dados completos
            t: Vetor de tempo para o eixo x
            freqs: Vetor de frequências para o eixo y
            Sxx: Matriz do espectrograma
        """
        log_info("Espectrograma gerado com sucesso")
        
        try:
            # Mostrar espectrograma
            params = data.get('spectrogram_params', {})
            log_debug(f"on_spectrogram_generated: Parâmetros: {params}")
            log_debug(f"on_spectrogram_generated: t={len(t)}, freqs={len(freqs)}, Sxx={Sxx.shape}")
            
            self.window.analysis_panel.show_spectrogram(t, freqs, Sxx, params)
            self.window.show_status_message("Espectrograma gerado com sucesso")
                
        except Exception as e:
            log_error(f"Erro ao exibir espectrograma: {str(e)}")
            self.window.show_status_message(f"Erro ao exibir espectrograma: {str(e)}")
            

            
    def diagnose_filtered_data(self, data):
        """
        Diagnóstico detalhado dos dados de filtro passa-banda
        
        Args:
            data: Dados a serem diagnosticados
        """
        log_debug("DIAGNÓSTICO DE DADOS FILTRADOS:")
        log_debug(f"- Chaves disponíveis: {list(data.keys())}")
        
        # Verificar vetor de tempo
        if 't' in data:
            t = data['t']
            log_debug(f"- Vetor de tempo: tamanho={len(t)}, min={min(t)}, max={max(t)}")
        else:
            log_warning("- Vetor de tempo não encontrado")
            
        # Verificar sinal demodulado original
        if 'demodulated' in data:
            demod = data['demodulated']
            log_debug(f"- Sinal demodulado: tamanho={len(demod)}, min={min(demod)}, max={max(demod)}")
        else:
            log_warning("- Sinal demodulado não encontrado")
            
        # Verificar sinal filtrado
        if 'filtered_demodulated' in data:
            filtered = data['filtered_demodulated']
            log_debug(f"- Sinal filtrado: tamanho={len(filtered)}, min={min(filtered)}, max={max(filtered)}")
            
            # Verificar se o sinal filtrado é NaN ou infinito
            if np.isnan(filtered).any():
                log_warning("  -> ALERTA: Sinal filtrado contém valores NaN")
            if np.isinf(filtered).any():
                log_warning("  -> ALERTA: Sinal filtrado contém valores infinitos")
                
            # Verificar diferença entre original e filtrado
            if 'demodulated' in data:
                diff = np.abs(data['demodulated'] - filtered).mean()
                log_debug(f"- Diferença média entre original e filtrado: {diff}")
        else:
            log_warning("- Sinal filtrado não encontrado")
            
        # Verificar parâmetros do filtro
        if 'bandpass_params' in data:
            params = data['bandpass_params']
            log_debug(f"- Parâmetros do filtro: {params}")
        else:
            log_warning("- Parâmetros do filtro não encontrados")
    
    def on_files_selected(self, file_list):
        """Slot para carregar múltiplos arquivos selecionados na análise"""
        if not file_list:
            return

        log_info(f"Carregando {len(file_list)} arquivo(s) selecionado(s)")

        if len(file_list) == 1:
            # Para um único arquivo, usar o fluxo normal
            self._load_single_file(file_list[0])
        else:
            # Para múltiplos arquivos, usar o método de carregamento múltiplo
            self._load_multiple_files(file_list)

    def _load_single_file(self, filepath):
        """Carrega um único arquivo"""
        log_info(f"Carregando arquivo único: {filepath}")

        try:
            # Carregar dados usando o controlador de arquivos
            data = self.file_controller.load_file(filepath)
            if data:
                # Configurar dados no controlador de processamento
                self.processing_controller.set_data(data)

                # Exibir dados na interface
                if 't' in data and 'waveforms' in data:
                    channels = data.get('channels', [1, 2])
                    self.window.analysis_panel.show_raw_data(data['t'], data['waveforms'], channels)

                # Mostrar elipse usando parâmetros dos metadados do arquivo ou calibração
                ellipse_params = None
                if 'metadata' in data:
                    # Primeiro, tentar usar parâmetros da elipse dos metadados do arquivo
                    if 'calibration_info' in data['metadata'] and data['metadata']['calibration_info'].get('ellipse_params'):
                        ellipse_params = data['metadata']['calibration_info']['ellipse_params']
                        log_info("Usando parâmetros da elipse dos metadados TOML do arquivo")
                    elif 'ellipse_params' in data['metadata']:
                        ellipse_params = data['metadata']['ellipse_params']
                        log_info("Usando parâmetros da elipse dos metadados (formato antigo) do arquivo")

                # Se não encontrou nos metadados, tentar usar calibração carregada
                if not ellipse_params and self.processing_controller.has_calibration_data():
                    ellipse_params = self.processing_controller.calibration_data.get('ellipse_params')
                    if ellipse_params:
                        log_info("Usando parâmetros da elipse da calibração carregada")

                # Mostrar elipse se temos parâmetros
                if ellipse_params and 'waveforms' in data:
                    self.window.analysis_panel.show_ellipse(data['waveforms'], ellipse_params)

                # Mostrar metadados se disponíveis
                if 'metadata' in data:
                    self.window.analysis_panel.show_metadata(data['metadata'])

                # Atualizar status
                self.window.show_status_message(f"Arquivo carregado: {os.path.basename(filepath)}")

                # Verificar se há parâmetros da elipse para demodulação automática
                metadata = data.get('metadata', {})
                has_ellipse_params = False

                if 'calibration_info' in metadata and metadata['calibration_info'].get('ellipse_params'):
                    has_ellipse_params = True
                    log_info("Parâmetros da elipse encontrados nos metadados TOML")
                elif 'ellipse_params' in metadata:
                    has_ellipse_params = True
                    log_info("Parâmetros da elipse encontrados nos metadados (formato antigo)")

                if has_ellipse_params:
                    log_info("Parâmetros da elipse disponíveis - iniciando demodulação automática...")
                    # Iniciar demodulação automaticamente
                    self.processing_controller.demodulate_data()
                elif self.processing_controller.has_calibration_data():
                    log_info("Usando calibração carregada para demodulação automática...")
                    self.processing_controller.demodulate_data()
                else:
                    log_info("Nenhum parâmetro de elipse disponível para demodulação automática")
            else:
                self.window.show_status_message("Erro ao carregar arquivo")
        except Exception as e:
            log_error(f"Erro ao carregar arquivo: {str(e)}")
            self.window.show_status_message(f"Erro ao carregar arquivo: {str(e)}")

    def _load_multiple_files(self, file_list):
        """Carrega múltiplos arquivos e processa cada um individualmente para demodulação"""
        log_info(f"Iniciando carregamento de {len(file_list)} arquivos múltiplos")

        # Listas para armazenar dados de todos os arquivos
        all_demodulated_data = []
        all_metadata = []

        for idx, filepath in enumerate(file_list):
            log_info(f"Processando arquivo {idx + 1}/{len(file_list)}: {os.path.basename(filepath)}")

            try:
                # Carregar dados usando o controlador de arquivos
                data = self.file_controller.load_file(filepath)
                if data:
                    # Verificar se há parâmetros da elipse para demodulação
                    metadata = data.get('metadata', {})
                    has_ellipse_params = False

                    if 'calibration_info' in metadata and metadata['calibration_info'].get('ellipse_params'):
                        has_ellipse_params = True
                        log_info(f"Arquivo {idx + 1}: Parâmetros da elipse encontrados nos metadados TOML")
                    elif 'ellipse_params' in metadata:
                        has_ellipse_params = True
                        log_info(f"Arquivo {idx + 1}: Parâmetros da elipse encontrados nos metadados (formato antigo)")

                    if has_ellipse_params or self.processing_controller.has_calibration_data():
                        log_info(f"Arquivo {idx + 1}: Iniciando demodulação...")

                        # Configurar dados no controlador de processamento
                        self.processing_controller.set_data(data)

                        # Criar uma flag para controlar quando a demodulação terminou
                        demodulation_completed = [False]
                        demod_data_collected = [None]

                        # Conectar ao sinal de demodulação terminada
                        def on_demodulation_finished(demod_data):
                            log_info(f"Arquivo {idx + 1}: Demodulação terminada, coletando dados...")
                            demodulation_completed[0] = True
                            demod_data_collected[0] = demod_data

                        # Conectar sinal temporariamente
                        self.processing_controller.demodulationFinished.connect(on_demodulation_finished)

                        try:
                            # Iniciar demodulação
                            self.processing_controller.demodulate_data()

                            # Aguardar até que a demodulação seja concluída (máximo 15 segundos)
                            import time
                            max_wait_time = 15.0
                            wait_time = 0.0
                            wait_interval = 0.1

                            while not demodulation_completed[0] and wait_time < max_wait_time:
                                time.sleep(wait_interval)
                                wait_time += wait_interval
                                # Processar eventos da GUI para manter responsividade
                                QApplication.processEvents()

                            if demodulation_completed[0] and demod_data_collected[0]:
                                demod_data = demod_data_collected[0]
                                if isinstance(demod_data, dict) and 'demodulated' in demod_data:
                                    # Criar cópia dos dados para evitar problemas de referência
                                    demod_data_copy = {
                                        'demodulated': demod_data['demodulated'].copy() if hasattr(demod_data['demodulated'], 'copy') else demod_data['demodulated'],
                                        't': demod_data['t'].copy() if hasattr(demod_data['t'], 'copy') else demod_data['t'],
                                        'waveforms': demod_data['waveforms'].copy() if hasattr(demod_data['waveforms'], 'copy') else demod_data['waveforms'],
                                        'sample_frequency': demod_data.get('sample_frequency'),
                                        'decimation': demod_data.get('decimation'),
                                        'sample_frequency_effective': demod_data.get('sample_frequency_effective'),
                                        'channels': demod_data.get('channels', [1, 2]),
                                        'ellipse_params': demod_data.get('ellipse_params'),
                                        'metadata': demod_data.get('metadata', {}),
                                        'bandpass_params': demod_data.get('bandpass_params', {}),
                                        'original_file': filepath
                                    }
                                    all_demodulated_data.append(demod_data_copy)
                                    log_info(f"Arquivo {idx + 1}: Dados demodulados coletados com sucesso")
                                else:
                                    log_warning(f"Arquivo {idx + 1}: Dados demodulados incompletos ou vazios")
                            else:
                                log_warning(f"Arquivo {idx + 1}: Demodulação não foi concluída no tempo esperado")

                        finally:
                            # Sempre desconectar o sinal
                            try:
                                self.processing_controller.demodulationFinished.disconnect(on_demodulation_finished)
                            except:
                                pass  # Ignorar erros de desconexão
                    else:
                        log_warning(f"Arquivo {idx + 1}: Nenhum parâmetro de elipse disponível")

                    # Coletar metadados
                    if 'metadata' in data:
                        file_metadata = data['metadata'].copy()
                        file_metadata['filename'] = filepath
                        all_metadata.append(file_metadata)

                else:
                    log_error(f"Erro ao carregar arquivo {idx + 1}: {filepath}")

            except Exception as e:
                log_error(f"Erro ao processar arquivo {idx + 1} ({filepath}): {str(e)}")

        # Log detalhado sobre os dados coletados
        log_info(f"Resumo do processamento múltiplo:")
        log_info(f"  - Total de arquivos processados: {len(file_list)}")
        log_info(f"  - Arquivos com dados demodulados: {len(all_demodulated_data)}")
        log_info(f"  - Arquivos com metadados: {len(all_metadata)}")

        for i, demod_data in enumerate(all_demodulated_data):
            log_info(f"  - Arquivo {i+1}: {os.path.basename(demod_data.get('original_file', 'desconhecido'))}")

        # Se temos dados demodulados de múltiplos arquivos, mostrar na interface
        if len(all_demodulated_data) > 1:
            log_info(f"Exibindo dados demodulados de {len(all_demodulated_data)} arquivos")

            # Preparar dados para plot múltiplo
            self.window.analysis_panel.multiple_demodulated_data = all_demodulated_data
            self.window.analysis_panel.multiple_metadata = all_metadata

            # Mostrar dados do primeiro arquivo como referência
            if all_demodulated_data:
                first_data = all_demodulated_data[0]
                if 't' in first_data and 'waveforms' in first_data:
                    channels = first_data.get('channels', [1, 2])
                    self.window.analysis_panel.show_raw_data(first_data['t'], first_data['waveforms'], channels)

                if 't' in first_data and 'demodulated' in first_data:
                    self.window.analysis_panel.show_demodulated(first_data['t'], first_data['demodulated'])

            # Plotar múltiplos sinais demodulados
            log_info(f"Preparando plot múltiplo com {len(all_demodulated_data)} dados demodulados")

            # Debug: verificar estrutura dos dados
            for i, data in enumerate(all_demodulated_data):
                log_debug(f"Dados {i+1}: keys={list(data.keys()) if isinstance(data, dict) else 'Não é dict'}")
                if 'demodulated' in data:
                    log_debug(f"Dados {i+1}: demodulated shape={data['demodulated'].shape if hasattr(data['demodulated'], 'shape') else 'Sem shape'}")

            try:
                self.window.analysis_panel.plot_demodulated_multiple()
                log_info("Plot múltiplo de sinais demodulados executado com sucesso")
            except Exception as e:
                log_error(f"Erro ao plotar sinais demodulados múltiplos: {e}")
                import traceback
                log_error(f"Traceback: {traceback.format_exc()}")

            try:
                self.window.analysis_panel.plot_spectrum_multiple()
                log_info("Plot múltiplo de espectros executado com sucesso")
            except Exception as e:
                log_error(f"Erro ao plotar espectros múltiplos: {e}")
                import traceback
                log_error(f"Traceback: {traceback.format_exc()}")

            try:
                self.window.analysis_panel.show_metadata_multiple(all_metadata)
                log_info("Metadados múltiplos exibidos com sucesso")
            except Exception as e:
                log_error(f"Erro ao exibir metadados múltiplos: {e}")
                import traceback
                log_error(f"Traceback: {traceback.format_exc()}")

            self.window.show_status_message(f"{len(all_demodulated_data)} arquivos processados com sucesso")

        elif len(all_demodulated_data) == 1:
            # Se só temos um arquivo com dados demodulados, mostrar normalmente
            log_info("Apenas um arquivo com dados demodulados - mostrando normalmente")
            single_data = all_demodulated_data[0]
            if 't' in single_data and 'demodulated' in single_data:
                self.window.analysis_panel.show_demodulated(single_data['t'], single_data['demodulated'])
            self.window.show_status_message("1 arquivo processado com sucesso")
        else:
            log_warning("Nenhum arquivo pôde ser demodulado")
            self.window.show_status_message("Nenhum arquivo pôde ser processado")
    
    def on_audio_file_loaded(self, data):
        """Manipula o carregamento de arquivo na aba de análise de áudio"""
        log_info("Arquivo carregado na aba de análise de áudio")
        
        # Atualizar o painel de áudio
        self.window.audio_analysis_panel.on_audio_loaded(data)
        
        # Calcular espectro automaticamente
        self.audio_controller.calculate_spectrum()
    
    def on_audio_generated_from_audio_panel(self, audio_path):
        """Manipula a geração de áudio na aba de análise de áudio"""
        log_info(f"Áudio gerado na aba de análise de áudio: {audio_path}")
        
        # Atualizar o painel de áudio
        self.window.audio_analysis_panel.on_audio_generated(audio_path)
    
    def on_play_audio_from_audio_panel(self):
        """Manipula a reprodução de áudio na aba de análise de áudio"""
        audio_path = self.audio_controller.get_current_audio_path()
        if audio_path:
            self.play_audio_file(audio_path)
        else:
            log_warning("Nenhum arquivo de áudio disponível para reprodução")
    
    def on_audio_error(self, error_message):
        """Manipula erros do controlador de áudio"""
        log_error(f"Erro no controlador de áudio: {error_message}")
        self.window.audio_analysis_panel.on_audio_error(error_message)
    
    def on_spectrum_calculated_for_audio(self, frequencies, magnitudes):
        """Manipula o cálculo de espectro para a aba de análise de áudio"""
        log_debug("Espectro calculado para aba de análise de áudio")
        self.window.audio_analysis_panel.show_spectrum(frequencies, magnitudes)
    
    def play_audio_file(self, audio_path):
        """Reproduz um arquivo de áudio usando o reprodutor padrão do sistema"""
        try:
            import os
            import subprocess
            import platform
            
            log_info(f"Reproduzindo arquivo de áudio: {audio_path}")
            
            system = platform.system()
            if system == "Windows":
                os.startfile(audio_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", audio_path])
            else:  # Linux
                subprocess.run(["xdg-open", audio_path])
                
        except Exception as e:
            error_msg = f"Erro ao reproduzir arquivo de áudio: {str(e)}"
            log_error(error_msg)
            self.window.show_error_message("Erro de Reprodução", error_msg)
    
    def on_ultra_hear_data_loaded(self, data):
        """Manipula o carregamento de dados no Ultra-Hear"""
        log_info("Dados carregados no Ultra-Hear")
        self.window.ultra_hear_panel.on_data_loaded(data)
    
    def on_ultra_hear_processing_finished(self, result):
        """Manipula o fim do processamento Ultra-Hear"""
        log_info("Processamento Ultra-Hear concluído")
        self.window.ultra_hear_panel.on_processing_finished(result)
    
    def on_ultra_hear_error(self, error_message):
        """Manipula erros do Ultra-Hear"""
        log_error(f"Erro no Ultra-Hear: {error_message}")
        self.window.ultra_hear_panel.on_error(error_message)
    
    def on_play_ultra_hear_audio(self):
        """Reproduz o áudio processado pelo Ultra-Hear"""
        audio_path = self.ultra_hear_controller.get_current_audio_path()
        if audio_path:
            self.play_audio_file(audio_path)
        else:
            log_warning("Nenhum arquivo de áudio Ultra-Hear disponível para reprodução")
    
    # Métodos para controle LoRa
    def on_lora_ligar_requested(self, port_name):
        """
        Manipula a solicitação para ligar equipamento via LoRa
        
        Args:
            port_name: Nome da porta serial
        """
        if port_name == "refresh_ports":
            # Atualizar lista de portas
            ports = self.lora_controller.get_available_ports()
            self.window.acquisition_panel.update_lora_ports(ports)
            log_info("Lista de portas LoRa atualizada")
        else:
            # Ligar equipamento
            log_info(f"Solicitação para ligar equipamento via LoRa na porta {port_name}")
            self.window.show_status_message(f"Ligando equipamento via LoRa...")
            success = self.lora_controller.ligar_equipamento(port_name)
            if success:
                log_info("Equipamento ligado com sucesso via LoRa")
                self.window.show_status_message("Equipamento ligado via LoRa")
            else:
                log_warning("Falha ao ligar equipamento via LoRa")
    
    def on_lora_desligar_requested(self, port_name):
        """
        Manipula a solicitação para desligar equipamento via LoRa
        
        Args:
            port_name: Nome da porta serial
        """
        log_info(f"Solicitação para desligar equipamento via LoRa na porta {port_name}")
        self.window.show_status_message(f"Desligando equipamento via LoRa...")
        success = self.lora_controller.desligar_equipamento(port_name)
        if success:
            log_info("Equipamento desligado com sucesso via LoRa")
            self.window.show_status_message("Equipamento desligado via LoRa")
        else:
            log_warning("Falha ao desligar equipamento via LoRa")
    
    # Métodos para aquisições automáticas
    def on_automatic_acquisition_requested(self, params):
        """
        Manipula o evento de solicitação de aquisições automáticas
        
        Args:
            params: Parâmetros das aquisições automáticas
        """
        log_info(f"Solicitação de aquisições automáticas recebida: {params}")
        
        # Verificar se é uma calibração
        is_calibration = params.get('is_calibration', False)
        if is_calibration:
            log_info("Modo de calibração selecionado para aquisições automáticas")
            self.window.show_status_message("Iniciando aquisições automáticas para calibração...")
        else:
            # Verificar se temos uma calibração válida
            if not self.processing_controller.has_calibration_data():
                log_warning("Tentativa de aquisições automáticas sem calibração prévia")
                if QMessageBox.question(
                    self.window, 
                    "Calibração não encontrada", 
                    "Não foi encontrada uma calibração válida. Deseja continuar com as aquisições automáticas sem calibração?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.No:
                    log_info("Aquisições automáticas canceladas pelo usuário devido à falta de calibração")
                    return
                log_info("Usuário optou por continuar sem calibração")
        
        # Resetar as configurações de filtro e espectrograma na interface
        self.window.analysis_panel.reset_bandpass_filter()
        self.window.analysis_panel.reset_spectrogram()
        
        # Obter metadados
        metadata = self.window.metadata_panel.get_metadata()
        
        # Iniciar aquisições automáticas
        self.acquisition_controller.start_acquisition(params, metadata)
    
    def on_cancel_automatic_acquisition_requested(self):
        """Manipula o evento de cancelamento de aquisições automáticas"""
        log_info("Solicitação de cancelamento de aquisições automáticas")
        self.acquisition_controller.cancel_automatic_acquisition()
    
    def on_automatic_acquisition_started(self, params):
        """
        Manipula o evento de início de aquisições automáticas
        
        Args:
            params: Parâmetros das aquisições automáticas
        """
        log_info("Aquisições automáticas iniciadas")
        self.window.acquisition_panel.set_enabled(False)
        self.window.show_status_message("Aquisições automáticas em andamento...")
    
    def on_automatic_acquisition_finished(self, data):
        """
        Manipula o evento de conclusão de aquisições automáticas
        
        Args:
            data: Dados das aquisições automáticas
        """
        if data.get('cancelled', False):
            log_info("Aquisições automáticas canceladas")
            self.window.show_status_message("Aquisições automáticas canceladas")
        else:
            total = data.get('total_acquisitions', 0)
            log_info(f"Aquisições automáticas concluídas: {total} aquisições")
            self.window.show_status_message(f"Aquisições automáticas concluídas: {total} aquisições")
        
        self.window.acquisition_panel.set_enabled(True)
    
    def on_automatic_acquisition_progress(self, current, total):
        """
        Manipula o evento de progresso das aquisições automáticas
        
        Args:
            current: Número da aquisição atual
            total: Total de aquisições
        """
        log_info(f"Progresso das aquisições automáticas: {current}/{total}")
        self.window.show_status_message(f"Aquisições automáticas: {current}/{total}")
    

    
    def run(self):
        """
        Executa a aplicação
        
        Returns:
            Código de retorno da aplicação
        """
        log_info("Iniciando aplicação OAS-GUI")
        self.window.show()
        return self.app.exec_()

def main():
    """Função principal"""
    app = Application()
    return app.run()

if __name__ == "__main__":
    sys.exit(main()) 