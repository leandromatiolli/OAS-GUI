"""
Módulo com o painel de configurações de aquisição
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton,
                           QLabel, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

class AcquisitionPanel(QWidget):
    """Painel de configurações para aquisição de dados"""
    
    # Sinais
    acquisitionRequested = pyqtSignal(dict)  # Emitido quando o usuário solicita aquisição
    
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
        
        self.acquisition_group.setLayout(acquisition_form)
        layout.addWidget(self.acquisition_group)
        
        # Botões de aquisição
        button_layout = QHBoxLayout()
        self.acquire_button = QPushButton("Adquirir Dados")
        self.acquire_button.clicked.connect(self.request_acquisition)
        button_layout.addWidget(self.acquire_button)
        
        layout.addLayout(button_layout)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)
    
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
            QMessageBox.warning(self, "Erro", "Selecione pelo menos um canal")
            return
        
        # Emitir sinal com os parâmetros de aquisição
        params = {
            'ip': ip,
            'duration': duration,
            'sample_rate': sample_rate,
            'decimation': decimation,
            'channels': channels
        }
        
        self.acquisitionRequested.emit(params)
    
    def set_enabled(self, enabled):
        """
        Habilita ou desabilita o painel
        
        Args:
            enabled: Estado de habilitação
        """
        self.acquisition_group.setEnabled(enabled)
        self.acquire_button.setEnabled(enabled) 