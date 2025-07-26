#!/usr/bin/env python
"""
OAS - Interface de Aquisição e Análise
Programa principal para detecção e análise de vazamentos ...
"""
import sys
import os
import traceback
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox
import numpy as np
from app.utils.config import traverse_widgets

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

        self.app.aboutToQuit.connect(self.on_about_to_quit)
    
    def setup_logging(self):
        """Configurar sistema de logging"""
        # Definir o manipulador para atualizar o log na GUI
        set_gui_log_handler(self.window.log_panel.append_log)
        log_info("Sistema de logging inicializado")
    
    def init_controllers(self):
        """Inicializa os controladores da aplicação"""
        self.acquisition_controller = AcquisitionController()
        self.processing_controller = ProcessingController()
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
        self.window.acquisition_panel.sensorConnectRequested.connect(self.acquisition_controller.connect_to_sensor)
        self.acquisition_controller.acquisitionStarted.connect(self.on_acquisition_started)
        self.acquisition_controller.acquisitionFinished.connect(self.on_acquisition_finished)
        #self.acquisition_controller.calibrationFinished.connect(self.on_calibration_finished)
        self.acquisition_controller.acquisitionProgress.connect(self.window.show_status_message)
        self.acquisition_controller.acquisitionError.connect(self.on_acquisition_error)
        self.acquisition_controller.sensorConnected.connect(self.on_sensor_connected)
        self.acquisition_controller.acquisitionDataAcquired.connect(self.on_new_data)
        

        
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
        self.processing_controller.plotCalibrationDataRequested.connect(self.window.analysis_panel.plot_calibration_data)
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
                
        # Carregar configuração da pasta de calibração
        config = DataStore.load_config()


        calib_folder = config.get('calibration_directory')
        self.window.acquisition_panel.set_calibration_folder(calib_folder)

        # Carregar lista de arquivos
        self.file_controller.refresh_file_list()
        
        # Inicializar lista de portas LoRa
        ports = self.lora_controller.get_available_ports()
        self.window.acquisition_panel.update_lora_ports(ports)
        log_info("Lista de portas LoRa inicializada")
        set_all_input_values(self.window, config)
        
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
        
        if params['is_series']:
            log_info("Iniciando aquisição em série")
            self.window.acquisition_panel.acquire_button.setText("Parar Aquisição")
            self.window.acquisition_panel.acquire_button.setStyleSheet("background-color: red")
            self.window.acquisition_panel.acquire_button.clicked.disconnect(self.window.acquisition_panel.request_acquisition)
            self.window.acquisition_panel.acquire_button.clicked.connect(self.stop_acquisition)
            

        # Iniciar aquisição
        self.acquisition_controller.start_acquisition(params, metadata)
    
    def on_acquisition_started(self):
        """Manipula o evento de início de aquisição"""
        log_info("Aquisição iniciada")
        #self.window.acquisition_panel.set_enabled(False)
        self.window.show_status_message("Aquisição em andamento...")
    
    def stop_acquisition(self):
        # Request interruption of the acquisition thread
        log_info("Solicitando interrupção da thread de aquisição")
        self.acquisition_controller.stop_acquisition()
        
        # Update UI
        self.window.acquisition_panel.acquire_button.setText("Adquirir Dados")
        self.window.acquisition_panel.acquire_button.setStyleSheet("")
        self.window.acquisition_panel.acquire_button.clicked.disconnect(self.stop_acquisition)
        self.window.acquisition_panel.acquire_button.clicked.connect(self.window.acquisition_panel.request_acquisition)


    def on_acquisition_finished(self, message):
        log_info("Aquisição concluída")
        self.window.acquisition_panel.set_enabled(True)

        if self.processing_controller.data['is_calibration']:
            calibration_file = self.processing_controller.data.get('calibration_file')
            self.processing_controller.calibration_data = self.processing_controller.data
            # Processar os dados de calibração
            self.processing_controller.set_calibration_data(self.processing_controller.calibration_data)

            # Salvar dados de calibração
            log_info(f"Salvando arquivo de calibração: {calibration_file or 'padrão'}...")
            DataStore.save_calibration_data(self.processing_controller.calibration_data, calibration_file)


                
    
    def on_new_data(self, data):
        """
        Manipula o evento de novos dados
        
        Args:
            data: Dados adquiridos
        """
        log_info("Novos dados")
        self.window.show_status_message("Aquisição concluída")
        
        data['metadata'] = self.window.metadata_panel.get_metadata()
        self.processing_controller.set_data(data)
        
        
        self.file_controller

        
        directory = self.window.analysis_panel.dir_label.text()
        log_debug(f"Salvando dados adquiridos no diretório: {directory}")
        DataStore.save_data(data, prefix="", directory=directory)

        if self.window.analysis_panel.autoshow_waveform.isChecked():
            self.window.acquisition_panel.set_enabled(True)
            self.window.switch_to_tab(2) 
            # Selecionar a aba de dados brutos no painel de análise
            self.window.analysis_panel.analysis_tabs.setCurrentIndex(0)

            if 'waveforms' in data and 't' in data:
                channels = data.get('channels', [1, 2])
                log_info(f"Exibindo dados brutos: canais {channels}")
                
                # Obter formas de onda processadas (com ou sem média móvel)
                waveforms = self.processing_controller.get_waveforms_for_processing()
                self.window.analysis_panel.show_raw_data(data['t'], waveforms, channels)
                
                # Verificar se temos dois canais para a elipse
                if waveforms.shape[0] >= 2:
                    ellipse_params = data.get('ellipse_params', None)
                    log_info("Exibindo elipse")
                    self.window.analysis_panel.show_ellipse(waveforms, ellipse_params)
            else:
                log_warning("Não foi possível exibir dados brutos: waveforms ou vetor de tempo ausentes")
        
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
            
            
        except Exception as e:
            log_error(f"Erro ao exibir dados brutos: {str(e)}")
            self.window.show_status_message(f"Erro ao exibir dados brutos: {str(e)}")
        
        # ETAPA 2: Processar dados automaticamente
        if self.window.analysis_panel.autodemodulate.isChecked():
            try:
                log_debug("Iniciando processamento automático...")
                # Armazenar dados no controlador de processamento desde o início
                self.window.show_status_message("Realizando processamento automático...")
                demodulated_succeed = self.processing_controller.auto_demodulate(data)

            except Exception as e:
                log_error(f"Erro no processamento automático: {str(e)}")
                self.window.show_status_message(f"Erro no processamento automático: {str(e)}")
            
        if self.window.analysis_panel.autosave_demodulated_checkbox.isChecked() and demodulated_succeed:
            try:
                filename = self.processing_controller.save_demodulated_data()
                log_info(f"Dados processados salvos com sucesso em {filename}")
                self.window.show_status_message(f"Dados processados salvos em {filename}")
            except Exception as e:
                log_error(f"Erro ao salvar dados processados: {str(e)}")
                self.window.show_status_message(f"Erro ao salvar dados processados: {str(e)}")
    
        # ETAPA 3: Atualizar lista de arquivos
        if not self.window.acquisition_panel.series_acquisition_checkbox.isChecked():   
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
    
    def on_sensor_connected(self, connected, ip, error_message):
        """
        Manipula o evento de conexão do sensor
        
        Args:
            connected: True se conectado, False se desconectado
            ip: IP do sensor
            error_message: Mensagem de erro, se houver
        """
        if connected:
            log_info(f"Sensor conectado com sucesso: {ip}")
            self.window.show_status_message(f"Sensor conectado: {ip}")
        else:
            log_error(f"Erro ao conectar sensor {ip}: {error_message}")
            self.window.show_status_message(f"Erro na conexão do sensor: {error_message}")
        
        # Atualizar status do sensor no painel
        self.window.acquisition_panel.update_sensor_status(connected, ip, error_message)
    
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
                
            # Verificar se temos dados demodulados
            if 'demodulated' in data and 't' in data:
                log_debug("Exibindo dados demodulados do arquivo")
                self.window.analysis_panel.show_demodulated(data['t'], data['demodulated'])
                
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
            # Mostrar sinal filtrado na aba correspondente
            if 't' in data and 'filtered_demodulated' in data and 'bandpass_params' in data:
                log_debug(f"on_bandpass_filter_applied: Tamanho do sinal filtrado: {len(data['filtered_demodulated'])}")
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
            else:
                log_warning(f"on_bandpass_filter_applied: Dados incompletos para exibir sinal filtrado")
                if 't' not in data:
                    log_warning("  - Vetor de tempo não encontrado")
                if 'filtered_demodulated' not in data:
                    log_warning("  - Sinal filtrado não encontrado")
                if 'bandpass_params' not in data:
                    log_warning("  - Parâmetros do filtro não encontrados")
            
            self.window.show_status_message("Filtro passa-banda aplicado aos dados")
                
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
        # Carregar o primeiro arquivo através do file_controller para garantir 
        # que os dados sejam passados corretamente para o processing_controller
        if file_list:
            log_info(f"Carregando arquivo selecionado: {file_list[0]}")
            self.file_controller.load_file(file_list[0])
            
            # Se há múltiplos arquivos, também usar o método original para exibição múltipla
            if len(file_list) > 1:
                log_info(f"Carregando visualização múltipla para {len(file_list)} arquivos")
                self.window.analysis_panel.load_selected_file_from_list(file_list)
    
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
    
    def on_about_to_quit(self):
        """
        Manipula o evento de fechamento da aplicação
        """
        log_info("Aplicação OAS-GUI está sendo fechada")
        
        config = get_all_input_values(self.window)
        metadata = self.window.metadata_panel.get_metadata()
        self.window.metadata_panel.save_metadata_template()
        config['metadata'] = metadata
        DataStore.save_config(config)
    
    def run(self):
        """
        Executa a aplicação
        
        Returns:
            Código de retorno da aplicação
        """
        log_info("Iniciando aplicação OAS-GUI")
        self.window.show()
        return self.app.exec_()
    
def set_all_input_values(root_widget: QtWidgets, config: dict):

    def set_values(widget):
        object_name :str = widget.objectName()
        if not object_name.startswith("mk_") and (object_name[3:] not in config):
            return
        
        value = config[object_name[3:]]
        if isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(float(value))
        elif isinstance(widget, QtWidgets.QComboBox):
            index = widget.findText(value)
            if index != -1:
                widget.setCurrentIndex(index)
            else:
                widget.addItem(value)
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QtWidgets.QLabel):
            widget.setText(str(value))


    traverse_widgets(root_widget, set_values)
    
def get_all_input_values(self) -> dict:
    """
    Get all input values from the panel using widget traversal
    
    Returns:
        Dictionary with widget object names as keys and their values
    """
    values = {}
    
    def collect_values(widget):

        object_name = widget.objectName()
        if not object_name.startswith("mk_"):
            return
        key = object_name[3:]  # Remove "mk_" prefix
        if isinstance(widget, QtWidgets.QLineEdit):
            values[key] = widget.text()
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            values[key] = widget.value()
        elif isinstance(widget, QtWidgets.QSpinBox):
            values[key] = widget.value()
        elif isinstance(widget, QtWidgets.QComboBox):
            values[key] = widget.currentText()
        elif isinstance(widget, QtWidgets.QCheckBox):
            values[key] = widget.isChecked()
        elif isinstance(widget, QtWidgets.QLabel):
            values[key] = widget.text()
        else:
            print(f"Widget {object_name} não suportado para coleta de valores ({widget.__class__.__name__})")

    traverse_widgets(self, collect_values, recursive=True)
    
    return values

def main():
    """Função principal"""
    app = Application()
    return app.run()

if __name__ == "__main__":
    sys.exit(main()) 