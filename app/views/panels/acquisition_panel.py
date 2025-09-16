"""
Módulo com o painel de configurações de aquisição
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton,
                           QLabel, QMessageBox, QFileDialog, QSpinBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import os

class AcquisitionPanel(QWidget):
    """Painel de configurações para aquisição de dados"""
    
    # Sinais
    acquisitionRequested = pyqtSignal(dict)  # Emitido quando o usuário solicita aquisição
    calibrationFileSelected = pyqtSignal(str)  # Emitido quando um arquivo de calibração é selecionado
    calibrationFolderChanged = pyqtSignal(str)
    loraLigarRequested = pyqtSignal(str)  # Emitido quando o usuário solicita ligar equipamento LoRa
    loraDesligarRequested = pyqtSignal(str)  # Emitido quando o usuário solicita desligar equipamento LoRa
    automaticAcquisitionRequested = pyqtSignal(dict)  # Emitido quando o usuário solicita aquisições automáticas
    cancelAutomaticAcquisitionRequested = pyqtSignal()  # Emitido quando o usuário cancela aquisições automáticas
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de aquisição
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        
        # Variáveis para aquisições automáticas
        self.automatic_acquisition_timer = QTimer()
        self.automatic_acquisition_timer.timeout.connect(self.execute_automatic_acquisition)
        self.automatic_acquisition_params = None
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = 0
        self.is_automatic_acquisition_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do painel"""
        # Layout principal
        layout = QVBoxLayout(self)
        
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
        self.decimation_combo.currentIndexChanged.connect(self.update_effective_rate)
        acquisition_form.addRow("Decimação:", self.decimation_combo)
        
        # Taxa de amostragem efetiva
        self.effective_rate_label = QLabel()
        acquisition_form.addRow("Taxa efetiva:", self.effective_rate_label)
        self.update_effective_rate()  # Inicializa o rótulo
        
        # Canais
        self.ch1_check = QCheckBox("Canal 1")
        self.ch1_check.setChecked(True)
        self.ch2_check = QCheckBox("Canal 2")
        self.ch2_check.setChecked(True)
        
        channels_layout = QHBoxLayout()
        channels_layout.addWidget(self.ch1_check)
        channels_layout.addWidget(self.ch2_check)
        acquisition_form.addRow("Canais:", channels_layout)
        
        # Grupo de configurações de calibração
        self.calibration_group = QGroupBox("Configurações de Calibração")
        calibration_form = QFormLayout()
        
        # Botão para selecionar a pasta de calibrações
        calib_folder_layout = QHBoxLayout()
        self.calib_folder_label = QLabel("Nenhuma pasta selecionada")
        self.calib_folder_label.setToolTip("Pasta contendo os arquivos de calibração")
        self.select_calib_folder_button = QPushButton("Selecionar Pasta")
        self.select_calib_folder_button.clicked.connect(self.select_calibration_folder)
        calib_folder_layout.addWidget(self.calib_folder_label, 1)
        calib_folder_layout.addWidget(self.select_calib_folder_button)
        calibration_form.addRow("Pasta de Calibração:", calib_folder_layout)
        
        # Adicionar checkbox de calibração
        self.calibration_check = QCheckBox("Modo Calibração")
        self.calibration_check.setToolTip("Marque para adquirir dados de calibração para o fit da elipse")
        self.calibration_check.stateChanged.connect(self.update_calibration_mode)
        calibration_form.addRow("Modo:", self.calibration_check)
        
        # Campo para nome de arquivo de calibração
        self.calib_name_layout = QHBoxLayout()
        self.calib_name_edit = QLineEdit("calibracao_sensor")
        self.calib_name_edit.setPlaceholderText("Nome do arquivo de calibração")
        self.calib_name_layout.addWidget(self.calib_name_edit)
        
        self.calib_extension_label = QLabel(".pkl")
        self.calib_name_layout.addWidget(self.calib_extension_label)
        
        calibration_form.addRow("Nome do arquivo:", self.calib_name_layout)
        
        # Lista suspensa com calibrações disponíveis
        self.calib_selection_layout = QHBoxLayout()
        self.calib_combo = QComboBox()
        self.calib_combo.setToolTip("Selecione um arquivo de calibração para usar")
        self.calib_combo.currentIndexChanged.connect(self.on_calibration_selected)
        self.calib_selection_layout.addWidget(self.calib_combo, 1)
        
        # Botão para atualizar a lista de calibrações
        self.refresh_calib_button = QPushButton("↻")
        self.refresh_calib_button.setToolTip("Atualizar lista de calibrações")
        self.refresh_calib_button.setMaximumWidth(25)
        self.refresh_calib_button.clicked.connect(self.on_refresh_calibration_list)
        self.calib_selection_layout.addWidget(self.refresh_calib_button)
        
        calibration_form.addRow("Calibração atual:", self.calib_selection_layout)
        
        # Indicador de calibração
        self.calibration_status = QLabel("Sem arquivo de calibração")
        self.calibration_status.setStyleSheet("color: orange;")
        calibration_form.addRow("Status:", self.calibration_status)
        
        self.calibration_group.setLayout(calibration_form)
        
        # Adicionar grupos ao layout principal
        self.acquisition_group.setLayout(acquisition_form)
        layout.addWidget(self.acquisition_group)
        layout.addWidget(self.calibration_group)
        
        # Grupo de controles LoRa
        self.lora_group = QGroupBox("Controle Remoto LoRa")
        lora_form = QFormLayout()
        
        # Seleção de porta serial
        port_layout = QHBoxLayout()
        self.lora_port_combo = QComboBox()
        self.lora_port_combo.setToolTip("Selecione a porta serial do módulo LoRa")
        self.refresh_lora_ports_button = QPushButton("↻")
        self.refresh_lora_ports_button.setToolTip("Atualizar lista de portas")
        self.refresh_lora_ports_button.setMaximumWidth(25)
        self.refresh_lora_ports_button.clicked.connect(self.refresh_lora_ports)
        port_layout.addWidget(self.lora_port_combo, 1)
        port_layout.addWidget(self.refresh_lora_ports_button)
        lora_form.addRow("Porta Serial:", port_layout)
        
        # Botões de controle
        lora_buttons_layout = QHBoxLayout()
        self.lora_ligar_button = QPushButton("Ligar Equipamento")
        self.lora_ligar_button.setStyleSheet("background-color: lightgreen")
        self.lora_ligar_button.clicked.connect(self.ligar_equipamento_lora)
        lora_buttons_layout.addWidget(self.lora_ligar_button)
        
        self.lora_desligar_button = QPushButton("Desligar Equipamento")
        self.lora_desligar_button.setStyleSheet("background-color: #ff7f7f")
        self.lora_desligar_button.clicked.connect(self.desligar_equipamento_lora)
        lora_buttons_layout.addWidget(self.lora_desligar_button)
        lora_form.addRow("Controle:", lora_buttons_layout)
        
        # Status do equipamento
        self.lora_status_label = QLabel("Status: Desconhecido")
        self.lora_status_label.setStyleSheet("color: orange;")
        lora_form.addRow("Status:", self.lora_status_label)
        
        self.lora_group.setLayout(lora_form)
        layout.addWidget(self.lora_group)
        
        # Grupo de aquisições automáticas
        self.automatic_group = QGroupBox("Aquisições Automáticas")
        automatic_form = QFormLayout()
        
        # Número de aquisições
        self.num_acquisitions_spin = QSpinBox()
        self.num_acquisitions_spin.setRange(1, 100)
        self.num_acquisitions_spin.setValue(5)
        self.num_acquisitions_spin.setToolTip("Número de aquisições a serem realizadas em sequência")
        automatic_form.addRow("Número de aquisições:", self.num_acquisitions_spin)
        
        # Intervalo entre aquisições
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(1.0, 3600.0)  # De 1 segundo a 1 hora
        self.interval_spin.setValue(10.0)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setToolTip("Intervalo de tempo entre cada aquisição")
        automatic_form.addRow("Intervalo entre aquisições:", self.interval_spin)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        automatic_form.addRow("Progresso:", self.progress_bar)
        
        # Label de status das aquisições automáticas
        self.automatic_status_label = QLabel("Pronto para aquisições automáticas")
        self.automatic_status_label.setStyleSheet("color: blue;")
        automatic_form.addRow("Status:", self.automatic_status_label)
        
        self.automatic_group.setLayout(automatic_form)
        layout.addWidget(self.automatic_group)
        
        # Botões de aquisição
        button_layout = QHBoxLayout()
        self.acquire_button = QPushButton("Adquirir Dados")
        self.acquire_button.clicked.connect(self.request_acquisition)
        button_layout.addWidget(self.acquire_button)
        
        self.automatic_acquire_button = QPushButton("Iniciar Aquisições Automáticas")
        self.automatic_acquire_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.automatic_acquire_button.clicked.connect(self.request_automatic_acquisition)
        button_layout.addWidget(self.automatic_acquire_button)
        
        self.cancel_automatic_button = QPushButton("Cancelar Aquisições")
        self.cancel_automatic_button.setStyleSheet("background-color: #f44336; color: white;")
        self.cancel_automatic_button.clicked.connect(self.cancel_automatic_acquisition)
        self.cancel_automatic_button.setVisible(False)
        button_layout.addWidget(self.cancel_automatic_button)
        
        layout.addLayout(button_layout)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)
        
        # Inicializar estado
        self.update_calibration_mode(self.calibration_check.checkState())
    
    def update_effective_rate(self):
        """Atualiza o rótulo da taxa de amostragem efetiva"""
        base_rate = 125e6  # Taxa base do Red Pitaya em Hz
        decimation = self.decimation_combo.currentData()
        effective_rate = base_rate / decimation
        
        # Formatação inteligente baseada no valor
        if effective_rate >= 1e6:
            formatted = f"{effective_rate/1e6:.2f} MHz"
        elif effective_rate >= 1e3:
            formatted = f"{effective_rate/1e3:.2f} kHz"
        else:
            formatted = f"{effective_rate:.2f} Hz"
        
        # Exibir e calcular Nyquist
        nyquist = effective_rate / 2
        nyquist_formatted = f"{nyquist/1e3:.1f} kHz" if nyquist >= 1e3 else f"{nyquist:.1f} Hz"
        
        self.effective_rate_label.setText(f"{formatted} (Nyquist: {nyquist_formatted})")
        
        # Mudar cor se a taxa for muito baixa
        if effective_rate < 100e3:  # Abaixo de 100 kHz
            self.effective_rate_label.setStyleSheet("color: orange;")
        elif effective_rate < 20e3:  # Abaixo de 20 kHz
            self.effective_rate_label.setStyleSheet("color: red;")
        else:
            self.effective_rate_label.setStyleSheet("")
    
    def select_calibration_folder(self):
        """Abre um diálogo para selecionar a pasta de calibrações"""
        current_dir = self.calib_folder_label.text()
        if not os.path.isdir(current_dir):
            current_dir = os.getcwd() # default to current dir if not set
            
        directory = QFileDialog.getExistingDirectory(self, "Selecione a Pasta de Calibrações", current_dir)
        if directory:
            self.set_calibration_folder(directory) # use a new method
            self.calibrationFolderChanged.emit(directory)

    def set_calibration_folder(self, folder_path: str):
        """Atualiza a label da pasta de calibração"""
        if folder_path and os.path.isdir(folder_path):
            self.calib_folder_label.setText(folder_path)
            self.calib_folder_label.setStyleSheet("")
        else:
            self.calib_folder_label.setText("Nenhuma pasta selecionada")
            self.calib_folder_label.setStyleSheet("color: orange;")
    
    def update_calibration_mode(self, state):
        """
        Atualiza a interface com base no modo de calibração
        
        Args:
            state: Estado do checkbox de calibração
        """
        is_calibration_mode = (state == Qt.Checked)
        self.calib_name_edit.setEnabled(is_calibration_mode)
        self.calib_extension_label.setEnabled(is_calibration_mode)
        self.calib_combo.setEnabled(not is_calibration_mode)
        self.refresh_calib_button.setEnabled(not is_calibration_mode)
    
    def update_calibration_list(self, calibration_files):
        """
        Atualiza a lista de arquivos de calibração disponíveis
        
        Args:
            calibration_files: Lista de arquivos de calibração
        """
        self.calib_combo.clear()
        
        if not calibration_files:
            self.calib_combo.addItem("Nenhuma calibração disponível", None)
            return
            
        self.calib_combo.addItem("Selecione uma calibração", None)
        
        for calib_file in calibration_files:
            # Extrair apenas o nome do arquivo sem o caminho
            filename = os.path.basename(calib_file)
            self.calib_combo.addItem(filename, calib_file)
    
    def on_calibration_selected(self, index):
        """
        Manipula a seleção de um arquivo de calibração
        
        Args:
            index: Índice selecionado na lista
        """
        if index <= 0:  # Ignorar a primeira opção (Selecione uma calibração)
            return
        
        selected_file = self.calib_combo.currentData()
        if selected_file:
            self.calibrationFileSelected.emit(selected_file)
    
    def on_refresh_calibration_list(self):
        """Solicita atualização da lista de calibrações"""
        # Este sinal será conectado ao sistema para solicitar atualização da lista
        # Vamos usar o mesmo sinal de seleção com None para indicar refresh
        self.calibrationFileSelected.emit(None)
    
    def update_calibration_status(self, has_calibration=False, calibration_file=None):
        """
        Atualiza o indicador de status da calibração
        
        Args:
            has_calibration: Se existe calibração válida
            calibration_file: Nome do arquivo de calibração, se disponível
        """
        if has_calibration:
            filename = os.path.basename(calibration_file) if calibration_file else "calibração"
            self.calibration_status.setText(f"Calibração disponível: {filename}")
            self.calibration_status.setStyleSheet("color: green;")
            
            # Selecionar o arquivo na lista suspensa
            if calibration_file:
                index = self.calib_combo.findData(calibration_file)
                if index > 0:
                    self.calib_combo.setCurrentIndex(index)
        else:
            self.calibration_status.setText("Sem arquivo de calibração")
            self.calibration_status.setStyleSheet("color: orange;")
    
    def request_acquisition(self):
        """Coleta os parâmetros e emite o sinal de solicitação de aquisição"""
        # Obter parâmetros
        ip = self.ip_edit.text()
        duration = self.duration_spin.value()
        decimation = self.decimation_combo.currentData()
        sample_rate = 125e6  # Taxa fixa do Red Pitaya
        
        # Verificar canais selecionados
        channels = []
        if self.ch1_check.isChecked():
            channels.append(1)
        if self.ch2_check.isChecked():
            channels.append(2)
        
        if not channels:
            QMessageBox.warning(self, "Canais não selecionados", "Por favor, selecione pelo menos um canal.")
            return
        
        # Verificar se é uma calibração
        is_calibration = self.calibration_check.isChecked()
        
        # Obter parâmetros
        params = {
            'ip': ip,
            'duration': duration,
            'decimation': decimation,
            'sample_rate': sample_rate,
            'channels': channels,
            'is_calibration': is_calibration
        }
        
        # Adicionar nome do arquivo de calibração se estiver no modo de calibração
        if is_calibration:
            calib_name = self.calib_name_edit.text().strip()
            if not calib_name:
                QMessageBox.warning(self, "Nome de arquivo inválido", "Por favor, insira um nome para o arquivo de calibração.")
                return
            params['calibration_file'] = f"{calib_name}.pkl"
            
        self.acquisitionRequested.emit(params)
        
    def get_acquisition_params(self):
        """Retorna os parâmetros de aquisição atuais"""
        return self.request_acquisition() # Reutiliza a lógica para obter os parâmetros
        
    def set_enabled(self, enabled):
        """
        Habilita ou desabilita os controles do painel
        
        Args:
            enabled: True para habilitar, False para desabilitar
        """
        self.acquisition_group.setEnabled(enabled)
        self.calibration_group.setEnabled(enabled)
        self.automatic_group.setEnabled(enabled)
        self.acquire_button.setEnabled(enabled)
        self.automatic_acquire_button.setEnabled(enabled)
    
    # Métodos para controle LoRa
    def refresh_lora_ports(self):
        """Atualiza a lista de portas seriais disponíveis para LoRa"""
        # Este método será conectado ao controlador LoRa
        # Por enquanto, apenas emite um sinal para solicitar atualização
        self.loraLigarRequested.emit("refresh_ports")
    
    def ligar_equipamento_lora(self):
        """Solicita ligar o equipamento via LoRa"""
        port_name = self.lora_port_combo.currentText()
        if not port_name or "Nenhuma" in port_name:
            QMessageBox.warning(self, "Porta não selecionada", "Por favor, selecione uma porta serial para o LoRa.")
            return
        
        self.loraLigarRequested.emit(port_name)
    
    def desligar_equipamento_lora(self):
        """Solicita desligar o equipamento via LoRa"""
        port_name = self.lora_port_combo.currentText()
        if not port_name or "Nenhuma" in port_name:
            QMessageBox.warning(self, "Porta não selecionada", "Por favor, selecione uma porta serial para o LoRa.")
            return
        
        self.loraDesligarRequested.emit(port_name)
    
    def update_lora_ports(self, ports):
        """
        Atualiza a lista de portas seriais disponíveis
        
        Args:
            ports: Lista de nomes de portas seriais
        """
        self.lora_port_combo.clear()
        if not ports:
            self.lora_port_combo.addItem("Nenhuma porta encontrada")
        else:
            for port in ports:
                self.lora_port_combo.addItem(port)
    
    def update_lora_status(self, status):
        """
        Atualiza o status do equipamento LoRa
        
        Args:
            status: String com o status do equipamento
        """
        self.lora_status_label.setText(f"Status: {status}")
        if "LIGADO" in status:
            self.lora_status_label.setStyleSheet("color: green;")
        elif "DESLIGADO" in status:
            self.lora_status_label.setStyleSheet("color: red;")
        else:
            self.lora_status_label.setStyleSheet("color: orange;")
    
    # Métodos para aquisições automáticas
    def request_automatic_acquisition(self):
        """Inicia o processo de aquisições automáticas"""
        if self.is_automatic_acquisition_running:
            QMessageBox.warning(self, "Aquisições em andamento", "Já existe uma sequência de aquisições automáticas em execução.")
            return
        
        # Obter parâmetros básicos de aquisição
        params = self._get_basic_acquisition_params()
        if not params:
            return
        
        # Adicionar parâmetros específicos das aquisições automáticas
        params.update({
            'is_automatic': True,
            'num_acquisitions': self.num_acquisitions_spin.value(),
            'interval_seconds': self.interval_spin.value()
        })
        
        # Inicializar estado das aquisições automáticas
        self.automatic_acquisition_params = params
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = params['num_acquisitions']
        self.is_automatic_acquisition_running = True
        
        # Atualizar interface
        self._update_automatic_acquisition_ui(True)
        
        # Emitir sinal para iniciar aquisições automáticas
        self.automaticAcquisitionRequested.emit(params)
    
    def cancel_automatic_acquisition(self):
        """Cancela as aquisições automáticas em andamento"""
        if not self.is_automatic_acquisition_running:
            return
        
        # Parar timer
        self.automatic_acquisition_timer.stop()
        
        # Resetar estado
        self.is_automatic_acquisition_running = False
        self.automatic_acquisition_params = None
        self.automatic_acquisition_count = 0
        self.automatic_acquisition_total = 0
        
        # Atualizar interface
        self._update_automatic_acquisition_ui(False)
        
        # Emitir sinal de cancelamento
        self.cancelAutomaticAcquisitionRequested.emit()
        
        # Atualizar status
        self.automatic_status_label.setText("Aquisições automáticas canceladas")
        self.automatic_status_label.setStyleSheet("color: orange;")
    
    def execute_automatic_acquisition(self):
        """Executa uma aquisição individual no modo automático"""
        if not self.is_automatic_acquisition_running or not self.automatic_acquisition_params:
            return
        
        # Incrementar contador
        self.automatic_acquisition_count += 1
        
        # Atualizar progresso
        progress = int((self.automatic_acquisition_count / self.automatic_acquisition_total) * 100)
        self.progress_bar.setValue(progress)
        self.automatic_status_label.setText(f"Aquisição {self.automatic_acquisition_count}/{self.automatic_acquisition_total}")
        
        # Executar aquisição individual
        self.acquisitionRequested.emit(self.automatic_acquisition_params)
        
        # Verificar se é a última aquisição
        if self.automatic_acquisition_count >= self.automatic_acquisition_total:
            # Finalizar aquisições automáticas
            self._finish_automatic_acquisition()
        else:
            # Programar próxima aquisição
            interval_ms = int(self.automatic_acquisition_params['interval_seconds'] * 1000)
            self.automatic_acquisition_timer.start(interval_ms)
    
    def _finish_automatic_acquisition(self):
        """Finaliza a sequência de aquisições automáticas"""
        self.is_automatic_acquisition_running = False
        self.automatic_acquisition_params = None
        
        # Atualizar interface
        self._update_automatic_acquisition_ui(False)
        
        # Atualizar status
        self.automatic_status_label.setText("Aquisições automáticas concluídas")
        self.automatic_status_label.setStyleSheet("color: green;")
        
        # Mostrar mensagem de conclusão
        QMessageBox.information(self, "Aquisições Concluídas", 
                               f"Sequência de {self.automatic_acquisition_total} aquisições foi concluída com sucesso!")
    
    def _update_automatic_acquisition_ui(self, is_running):
        """Atualiza a interface durante aquisições automáticas"""
        self.automatic_acquire_button.setVisible(not is_running)
        self.cancel_automatic_button.setVisible(is_running)
        self.progress_bar.setVisible(is_running)
        
        # Desabilitar controles durante aquisições automáticas
        self.acquisition_group.setEnabled(not is_running)
        self.calibration_group.setEnabled(not is_running)
        self.automatic_group.setEnabled(not is_running)
        self.acquire_button.setEnabled(not is_running)
    
    def _get_basic_acquisition_params(self):
        """Obtém os parâmetros básicos de aquisição (reutiliza lógica do request_acquisition)"""
        # Obter parâmetros
        ip = self.ip_edit.text()
        duration = self.duration_spin.value()
        decimation = self.decimation_combo.currentData()
        sample_rate = 125e6  # Taxa fixa do Red Pitaya
        
        # Verificar canais selecionados
        channels = []
        if self.ch1_check.isChecked():
            channels.append(1)
        if self.ch2_check.isChecked():
            channels.append(2)
        
        if not channels:
            QMessageBox.warning(self, "Canais não selecionados", "Por favor, selecione pelo menos um canal.")
            return None
        
        # Verificar se é uma calibração
        is_calibration = self.calibration_check.isChecked()
        
        # Obter parâmetros
        params = {
            'ip': ip,
            'duration': duration,
            'decimation': decimation,
            'sample_rate': sample_rate,
            'channels': channels,
            'is_calibration': is_calibration
        }
        
        # Adicionar nome do arquivo de calibração se estiver no modo de calibração
        if is_calibration:
            calib_name = self.calib_name_edit.text().strip()
            if not calib_name:
                QMessageBox.warning(self, "Nome de arquivo inválido", "Por favor, insira um nome para o arquivo de calibração.")
                return None
            params['calibration_file'] = f"{calib_name}.pkl"
        
        return params
    
    def start_automatic_acquisition_sequence(self):
        """Inicia a sequência de aquisições automáticas (chamado externamente)"""
        if not self.is_automatic_acquisition_running:
            return
        
        # Configurar barra de progresso
        self.progress_bar.setRange(0, self.automatic_acquisition_total)
        self.progress_bar.setValue(0)
        
        # Iniciar primeira aquisição imediatamente
        self.execute_automatic_acquisition()
    
    def on_automatic_acquisition_finished(self):
        """Chamado quando uma aquisição individual é concluída"""
        if not self.is_automatic_acquisition_running:
            return
        
        # Se ainda há aquisições pendentes, aguardar o intervalo
        if self.automatic_acquisition_count < self.automatic_acquisition_total:
            interval_ms = int(self.automatic_acquisition_params['interval_seconds'] * 1000)
            self.automatic_acquisition_timer.start(interval_ms)
        else:
            # Todas as aquisições foram concluídas
            self._finish_automatic_acquisition() 