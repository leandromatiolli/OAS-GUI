#!/usr/bin/env python
"""
OAS - Interface de Aquisição e Análise
Programa principal para detecção e análise de vazamentos
"""
import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
import numpy as np

# Certificar-se de que os pacotes estão no path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes da aplicação
from app.views.main_window import MainWindow
from app.controllers.acquisition_controller import AcquisitionController
from app.controllers.processing_controller import ProcessingController
from app.controllers.file_controller import FileController
from app.models.hardware.redpitaya_client import RedPitayaClient
# Importar módulo de recursos
from app.utils.resources import apply_stylesheet
# Importar módulo de logging
from app.utils.debug_log import set_gui_log_handler, log_debug, log_info, log_warning, log_error

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
        self.acquisition_controller.calibrationFinished.connect(self.on_calibration_finished)
        self.acquisition_controller.acquisitionProgress.connect(self.window.show_status_message)
        self.acquisition_controller.acquisitionError.connect(self.on_acquisition_error)
        
        # Conexões do controlador de arquivos
        self.window.analysis_panel.fileSelected.connect(self.file_controller.load_file)
        self.window.analysis_panel.refreshFilesRequested.connect(self.file_controller.refresh_file_list)
        self.file_controller.fileListUpdated.connect(self.window.analysis_panel.update_file_list)
        self.file_controller.fileLoaded.connect(self.on_file_loaded)
        self.file_controller.fileError.connect(self.on_file_error)
        self.file_controller.calibrationStatusChanged.connect(self.window.acquisition_panel.update_calibration_status)
        
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
    
    def initialize_state(self):
        """Inicializa o estado da aplicação"""
        # Verificar disponibilidade de hardware
        hardware_available = RedPitayaClient.is_available()
        self.window.acquisition_panel.set_enabled(hardware_available)
        
        if not hardware_available:
            log_warning("Hardware de aquisição não disponível")
            self.window.show_status_message("Hardware de aquisição não disponível")
        
        # Carregar lista de arquivos
        self.file_controller.refresh_file_list()
        
        # Verificar e carregar calibração existente
        calibration_data = self.file_controller.load_calibration_data()
        if calibration_data:
            log_info("Arquivo de calibração encontrado e carregado")
            self.processing_controller.set_calibration_data(calibration_data)
        else:
            log_info("Nenhum arquivo de calibração encontrado")
    
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
        
        # Resetar as configurações de filtro na interface
        self.window.analysis_panel.reset_bandpass_filter()
        
        # Obter metadados
        metadata = self.window.metadata_panel.get_metadata()
        
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
        
        # Processar os dados de calibração
        success = self.processing_controller.process_calibration_data(data)
        
        if success:
            log_info("Calibração processada com sucesso")
            self.window.show_status_message("Calibração concluída com sucesso")
            
            # Atualizar status de calibração na interface
            self.file_controller.check_calibration_status()
            
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
                        self.window.analysis_panel.show_ellipse(waveforms, ellipse_params)
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
        
        # Armazenar dados no controlador de processamento desde o início
        self.processing_controller.set_data(data)
        
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
                
            # Selecionar a aba de dados brutos no painel de análise
            self.window.analysis_panel.analysis_tabs.setCurrentIndex(0)
            
        except Exception as e:
            log_error(f"Erro ao exibir dados brutos: {str(e)}")
            self.window.show_status_message(f"Erro ao exibir dados brutos: {str(e)}")
        
        # ETAPA 2: Processar dados automaticamente
        try:
            log_info("Iniciando processamento automático...")
            self.window.show_status_message("Realizando processamento automático...")
            success = self.processing_controller.auto_demodulate(data)
            
            if success:
                try:
                    filename = self.processing_controller.save_demodulated_data()
                    log_info(f"Dados processados salvos com sucesso em {filename}")
                    self.window.show_status_message(f"Dados processados salvos em {filename}")
                except Exception as e:
                    log_error(f"Erro ao salvar dados processados: {str(e)}")
                    self.window.show_status_message(f"Erro ao salvar dados processados: {str(e)}")
            else:
                log_warning("Processamento automático não teve sucesso")
        except Exception as e:
            log_error(f"Erro no processamento automático: {str(e)}")
            self.window.show_status_message(f"Erro no processamento automático: {str(e)}")
        
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