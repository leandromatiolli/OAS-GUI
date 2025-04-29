"""
Módulo com o painel de metadados para informações do teste
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QLabel, QPushButton,
                           QFileDialog, QTextEdit)
from PyQt5.QtCore import Qt
from datetime import datetime
from typing import Dict, Any

class MetadataPanel(QWidget):
    """Painel para coleta de metadados sobre o teste"""
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de metadados
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do painel"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Grupo principal de metadados
        metadata_group = QGroupBox("Informações para Treinamento de IA")
        metadata_form = QFormLayout()
        
        # Número de série do sensor
        self.sensor_sn_edit = QLineEdit()
        metadata_form.addRow("SN do Sensor:", self.sensor_sn_edit)
        
        # Tipo de teste
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems([
            "Vazamento de Água", 
            "Vazamento de Ar", 
            "Vazamento de Gás", 
            "Descarga Elétrica", 
            "Ruído Mecânico", 
            "Controle (Sem Vazamento)", 
            "Outro"
        ])
        metadata_form.addRow("Tipo de Teste:", self.test_type_combo)
        
        # Material do sensor
        self.material_combo = QComboBox()
        self.material_combo.addItems([
            "PVC", 
            "Aço", 
            "Cobre", 
            "Polietileno", 
            "Polipropileno", 
            "Ferro Fundido", 
            "Outro"
        ])
        metadata_form.addRow("Material:", self.material_combo)
        
        
        # Pressão do teste
        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(0, 100.0)
        self.pressure_spin.setValue(0.0)
        self.pressure_spin.setSingleStep(0.5)
        self.pressure_spin.setSuffix(" bar")
        metadata_form.addRow("Pressão:", self.pressure_spin)
        
        # Fluxo do vazamento
        self.flow_spin = QDoubleSpinBox()
        self.flow_spin.setRange(0, 50.0)
        self.flow_spin.setValue(0.0)
        self.flow_spin.setSingleStep(0.1)
        self.flow_spin.setSuffix(" L/min")
        metadata_form.addRow("Fluxo:", self.flow_spin)
        
        # Distância do vazamento
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0, 1000.0)
        self.distance_spin.setValue(0.0)
        self.distance_spin.setSingleStep(10.0)
        self.distance_spin.setSuffix(" cm")
        metadata_form.addRow("Distância:", self.distance_spin)

        #temperatura da água
        self.water_temperature_spin = QDoubleSpinBox()
        self.water_temperature_spin.setRange(0, 100.0)
        self.water_temperature_spin.setValue(30.0)
        self.water_temperature_spin.setSingleStep(1.0)
        self.water_temperature_spin.setSuffix(" °C")
        metadata_form.addRow("Temperatura da Água:", self.water_temperature_spin)

        # localização do vazamento
        self.location_edit = QLineEdit()
        metadata_form.addRow("Localização:", self.location_edit)

        #configuração do setup
        self.setup_config_edit = QTextEdit()
        self.setup_config_edit.setPlaceholderText("Digite mais detalhes do experimento aqui...")
        self.setup_config_edit.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setup_config_edit.setMinimumHeight(40)
        metadata_form.addRow("Configuração do Setup:", self.setup_config_edit)

        # Foto do setup
        self.setup_photo_button = QPushButton("Carregar Foto do Setup")
        self.setup_photo_button.clicked.connect(self.load_setup_photos)
        metadata_form.addRow("Foto do Setup:", self.setup_photo_button)
        
        # Lista de fotos carregadas
        self.setup_photos_label = QLabel("Nenhuma foto carregada")
        metadata_form.addRow("Fotos:", self.setup_photos_label)

        # Comentários
        self.comments_edit = QTextEdit()
        self.comments_edit.setAcceptRichText(False)  # Desabilitar formatação rica
        self.comments_edit.setPlaceholderText("Digite seus comentários aqui...")
        self.comments_edit.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.comments_edit.setMinimumHeight(400)
        metadata_form.addRow("Comentários:", self.comments_edit)
        metadata_group.setLayout(metadata_form)
        layout.addWidget(metadata_group)  
        



        
        # Informações adicionais
        info_label = QLabel("Estes metadados serão salvos junto compermitir os dados de aquisição e podem ser usados posteriormente para treinar modelos de IA. Preencha os campos com as informações do teste antes de iniciar a aquisição.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)
        
    def load_setup_photos(self):
        """Abre um diálogo para selecionar fotos do setup"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Imagens (*.png *.jpg *.jpeg *.bmp)")
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.setup_photos = selected_files
                self.setup_photos_label.setText(f"{len(selected_files)} foto(s) selecionada(s)")
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Coleta os metadados do painel
        
        Returns:
            Dicionário com os metadados
        """
        metadata = {
            "sensor_sn": self.sensor_sn_edit.text(),
            "test_type": self.test_type_combo.currentText(),
            "material": self.material_combo.currentText(),
            "location": self.location_edit.text(),
            "pressure": self.pressure_spin.value(),
            "flow": self.flow_spin.value(),
            "distance": self.distance_spin.value(),
            "comments": self.comments_edit.toPlainText(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Adicionar fotos se existirem
        if hasattr(self, 'setup_photos'):
            metadata['setup_photos'] = self.setup_photos
            
        return metadata
        
    def clear_fields(self):
        """Limpa todos os campos do formulário"""
        self.sensor_sn_edit.clear()
        self.test_type_combo.setCurrentIndex(0)
        self.material_combo.setCurrentIndex(0)
        self.location_edit.clear()
        self.pressure_spin.setValue(0.0)
        self.flow_spin.setValue(0.0)
        self.distance_spin.setValue(0.0)
        self.comments_edit.clear()
        if hasattr(self, 'setup_photos'):
            delattr(self, 'setup_photos')
        self.setup_photos_label.setText("Nenhuma foto carregada") 