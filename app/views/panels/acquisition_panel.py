"""
Módulo com o painel de configurações de aquisição
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton,
                           QLabel, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
import os

class AcquisitionPanel(QWidget):
    """Painel de configurações para aquisição de dados"""
    
    # Sinais
    acquisitionRequested = pyqtSignal(dict)  # Emitido quando o usuário solicita aquisição
    calibrationFileSelected = pyqtSignal(str)  # Emitido quando um arquivo de calibração é selecionado
    calibrationFolderChanged = pyqtSignal(str)
    loraLigarRequested = pyqtSignal(str)  # Emitido quando o usuário solicita ligar equipamento LoRa
    loraDesligarRequested = pyqtSignal(str)  # Emitido quando o usuário solicita desligar equipamento LoRa
    sensorConnectRequested = pyqtSignal(str)  # Emitido quando o usuário solicita conectar ao sensor
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de aquisição
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do painel"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Grupo de status do sensor
        self.sensor_status_group = QGroupBox("Conexão com o Sensor")
        sensor_layout = QHBoxLayout()
        
        # Status da conexão
        sensor_layout.addWidget(QLabel("Status:"))
        self.sensor_status_label = QLabel("Desconectado")
        self.sensor_status_label.setStyleSheet("color: red;")
        sensor_layout.addWidget(self.sensor_status_label)
        
        # IP do sensor
        sensor_layout.addWidget(QLabel("IP RedPitaya:"))
        self.ip_edit = QLineEdit("rp-f0b916.local")
        self.ip_edit.setObjectName("mk_ip_edit")
        sensor_layout.addWidget(self.ip_edit)
        
        # Botão para conectar ao sensor
        self.connect_sensor_button = QPushButton("Conectar ao Sensor")
        self.connect_sensor_button.clicked.connect(self.connect_to_sensor)
        sensor_layout.addWidget(self.connect_sensor_button)
        
        self.sensor_status_group.setLayout(sensor_layout)
        layout.addWidget(self.sensor_status_group)
        
        # Grupo de configurações de aquisição
        self.acquisition_group = QGroupBox("Configurações de Aquisição")
        acquisition_form = QFormLayout()
        
        ## Duração da aquisição
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setObjectName("mk_acquisition_duration")       
        self.duration_spin.setRange(0.1, 60.0)
        self.duration_spin.setValue(5.0)
        self.duration_spin.setSingleStep(0.5)
        
        ## Aquisição em série
        self.series_acquisition_checkbox = QCheckBox("Aquisição em série")
        self.series_acquisition_checkbox.setObjectName("mk_series_acquisition")

        # parametro de tempo
        time_params = QHBoxLayout()
        time_params.addWidget(QLabel("Duração (s):"))
        time_params.addWidget(self.duration_spin)
        time_params.addWidget(self.series_acquisition_checkbox)
        time_params.addWidget(QLabel(""), stretch=1)  # Spacer with em
        acquisition_form.addRow(time_params)
        
        ## Decimação
        self.decimation_combo = QComboBox()
        self.decimation_combo.setObjectName("mk_decimation")
        for i in range(0, 17):  # Potências de 2 de 1 a 2^16
            self.decimation_combo.addItem(f"{2**i}", 2**i)
        self.decimation_combo.setCurrentIndex(6)  # 2^6 = 64
        self.decimation_combo.currentIndexChanged.connect(self.update_effective_rate)
        acquisition_form.addRow("Decimação:", self.decimation_combo)
        
        ## Taxa de amostragem efetiva
        self.effective_rate_label = QLabel()
        acquisition_form.addRow("Taxa efetiva:", self.effective_rate_label)
        self.update_effective_rate()  # Inicializa o rótulo
        
        ## Canais
        self.ch1_check = QCheckBox("Canal 1")
        self.ch1_check.setChecked(True)
        self.ch1_check.setObjectName("mk_channel_1")
        self.ch2_check = QCheckBox("Canal 2")
        self.ch2_check.setChecked(True)
        self.ch2_check.setObjectName("mk_channel_2")

        channels_layout = QHBoxLayout()
        channels_layout.addWidget(self.ch1_check)
        channels_layout.addWidget(self.ch2_check)
        channels_layout.addWidget(QLabel(""), stretch=1)
        acquisition_form.addRow("Canais:", channels_layout)
        
        # Grupo de configurações de calibração
        self.calibration_group = QGroupBox("Configurações de Calibração")
        calibration_form = QFormLayout()
        
        # Botão para selecionar a pasta de calibrações
        calib_folder_layout = QHBoxLayout()
        self.calib_folder_label = QLabel("Nenhuma pasta selecionada")
        self.calib_folder_label.setObjectName("mk_calibration_folder")
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
        self.calib_name_edit.setObjectName("mk_calibration_file_name")
        self.calib_name_edit.setPlaceholderText("Nome do arquivo de calibração")
        self.calib_name_layout.addWidget(self.calib_name_edit)
        
        self.calib_extension_label = QLabel(".pkl")
        self.calib_name_layout.addWidget(self.calib_extension_label)
        
        calibration_form.addRow("Nome do arquivo:", self.calib_name_layout)
        
        # Lista suspensa com calibrações disponíveis
        self.calib_selection_layout = QHBoxLayout()
        self.calib_combo = QComboBox()
        self.calib_combo.setObjectName("mk_calibration_file")
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
        self.lora_port_combo.setObjectName("mk_lora_port")
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
        
        # Botões de aquisição
        button_layout = QHBoxLayout()
        self.acquire_button = QPushButton("Adquirir Dados")
        self.acquire_button.clicked.connect(self.request_acquisition)
        button_layout.addWidget(self.acquire_button)
        
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
            formatted = f"{effective_rate/1e6:.2f} MSps"
        elif effective_rate >= 1e3:
            formatted = f"{effective_rate/1e3:.2f} kSps"
        else:
            formatted = f"{effective_rate:.2f} Sps"
        
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

        is_series = self.series_acquisition_checkbox.isChecked()
        
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
            'is_calibration': is_calibration,
            'is_series' : is_series
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
    
    # def stop_acquisition(self):
    #     # Request interruption of the acquisition thread
    #     self.acquisition_controller.stop_acquisition()
        
    #     # Update UI
    #     self.acquire_button.setText("Adquirir Dados")
    #     self.acquire_button.setStyleSheet("background-color: blue")
    #     self.acquire_button.clicked.connect(self.request_acquisition)

    def set_enabled(self, enabled):
        """
        Habilita ou desabilita os controles do painel
        
        Args:
            enabled: True para habilitar, False para desabilitar
        """
        self.acquisition_group.setEnabled(enabled)
        self.calibration_group.setEnabled(enabled)
        self.acquire_button.setEnabled(enabled)
    
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
    
    def connect_to_sensor(self):
        """Solicita conexão ao sensor Red Pitaya"""
        ip = self.ip_edit.text()
        if not ip:
            QMessageBox.warning(self, "IP inválido", "Por favor, insira um IP válido para o Red Pitaya.")
            return
        
        self.sensorConnectRequested.emit(ip)
    
    def update_sensor_status(self, connected=False, ip=None, error_message=None):
        """
        Atualiza o status da conexão com o sensor
        
        Args:
            connected: True se conectado, False se desconectado
            ip: IP do sensor, se disponível
            error_message: Mensagem de erro, se houve erro na conexão
        """
        if connected:
            self.sensor_status_label.setText("Conectado")
            self.sensor_status_label.setStyleSheet("color: green;")
            self.connect_sensor_button.setText("Reconectar ao Sensor")
<<<<<<< HEAD
            self.connect_sensor_button.setStyleSheet("background-color: lightblue;")
        else:
            if error_message:
                self.sensor_status_label.setText(f"Erro: {error_message}")
                self.sensor_status_label.setStyleSheet("color: red;")
            else:
                self.sensor_status_label.setText("Desconectado")
                self.sensor_status_label.setStyleSheet("color: red;")
            self.connect_sensor_button.setText("Conectar ao Sensor")
            self.connect_sensor_button.setStyleSheet("")
=======
            self.connect_sensor_button.setStyleSheet("background-color: lightblue;")
>>>>>>> db4e97fd2148c52ebfbb81570be8dfceb8b2e7e1
