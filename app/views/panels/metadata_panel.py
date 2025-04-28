"""
Módulo com o painel de metadados para informações do teste
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QLabel)
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
        
        # Posição do sensor
        self.position_edit = QLineEdit()
        metadata_form.addRow("Posição (cm):", self.position_edit)
        
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
        
        # Comentários
        self.comments_edit = QLineEdit()
        metadata_form.addRow("Comentários:", self.comments_edit)
        
        metadata_group.setLayout(metadata_form)
        layout.addWidget(metadata_group)
        
        # Informações adicionais
        info_label = QLabel("Estes metadados serão salvos junto com os dados de aquisição e podem ser usados posteriormente para treinar modelos de IA.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Coleta os metadados do painel
        
        Returns:
            Dicionário com os metadados
        """
        return {
            "sensor_sn": self.sensor_sn_edit.text(),
            "test_type": self.test_type_combo.currentText(),
            "material": self.material_combo.currentText(),
            "position": self.position_edit.text(),
            "pressure": self.pressure_spin.value(),
            "flow": self.flow_spin.value(),
            "distance": self.distance_spin.value(),
            "comments": self.comments_edit.text(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    def clear_fields(self):
        """Limpa todos os campos do formulário"""
        self.sensor_sn_edit.clear()
        self.test_type_combo.setCurrentIndex(0)
        self.material_combo.setCurrentIndex(0)
        self.position_edit.clear()
        self.pressure_spin.setValue(0.0)
        self.flow_spin.setValue(0.0)
        self.distance_spin.setValue(0.0)
        self.comments_edit.clear() 