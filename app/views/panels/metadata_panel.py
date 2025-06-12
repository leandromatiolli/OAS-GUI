"""
Módulo com o painel de metadados para informações do teste
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QLabel, QPushButton,
                           QFileDialog, QTextEdit)
from PyQt5.QtCore import Qt
from datetime import datetime
from typing import Dict, Any
import os
import json

class MetadataPanel(QWidget):
    """Painel para coleta de metadados sobre o teste"""
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de metadados
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.config_file = "config/metadata_options.json"
        self.last_state_file = "config/last_metadata_state.json"
        self.setup_ui()
        self.load_options()
        self.load_last_state()
        
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
        
        # Localização
        self.location_edit = QLineEdit()
        metadata_form.addRow("Localização:", self.location_edit)
        
        # Pressão
        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(0.0, 100.0)
        self.pressure_spin.setValue(0.0)
        self.pressure_spin.setSuffix(" bar")
        metadata_form.addRow("Pressão:", self.pressure_spin)
        
        # Fluxo
        self.flow_spin = QDoubleSpinBox()
        self.flow_spin.setRange(0.0, 100.0)
        self.flow_spin.setValue(0.0)
        self.flow_spin.setSuffix(" L/min")
        metadata_form.addRow("Fluxo:", self.flow_spin)
        
        # Distância
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.0, 1000.0)
        self.distance_spin.setValue(0.0)
        self.distance_spin.setSuffix(" cm")
        metadata_form.addRow("Distância:", self.distance_spin)
        
        # Botão para carregar fotos do setup
        self.setup_photo_button = QPushButton("Carregar Fotos")
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
        info_label = QLabel("Estes metadados serão salvos junto com os dados de aquisição e podem ser usados posteriormente para treinar modelos de IA. Preencha os campos com as informações do teste antes de iniciar a aquisição.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)
        
    def load_options(self):
        """Carrega as opções disponíveis do arquivo de configuração"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Atualizar opções do tipo de teste
                if 'test_types' in config:
                    self.test_type_combo.clear()
                    self.test_type_combo.addItems(config['test_types'])
                    
                # Atualizar opções de material
                if 'materials' in config:
                    self.material_combo.clear()
                    self.material_combo.addItems(config['materials'])
        except Exception as e:
            print(f"Erro ao carregar opções: {str(e)}")
            
    def save_options(self):
        """Salva as opções atuais no arquivo de configuração"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config = {
                'test_types': [self.test_type_combo.itemText(i) for i in range(self.test_type_combo.count())],
                'materials': [self.material_combo.itemText(i) for i in range(self.material_combo.count())]
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar opções: {str(e)}")
            
    def load_last_state(self):
        """Carrega o último estado usado"""
        try:
            if os.path.exists(self.last_state_file):
                with open(self.last_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    
                # Restaurar valores
                if 'sensor_sn' in state:
                    self.sensor_sn_edit.setText(state['sensor_sn'])
                if 'test_type' in state:
                    index = self.test_type_combo.findText(state['test_type'])
                    if index >= 0:
                        self.test_type_combo.setCurrentIndex(index)
                if 'material' in state:
                    index = self.material_combo.findText(state['material'])
                    if index >= 0:
                        self.material_combo.setCurrentIndex(index)
                if 'location' in state:
                    self.location_edit.setText(state['location'])
                if 'pressure' in state:
                    self.pressure_spin.setValue(state['pressure'])
                if 'flow' in state:
                    self.flow_spin.setValue(state['flow'])
                if 'distance' in state:
                    self.distance_spin.setValue(state['distance'])
                if 'comments' in state:
                    self.comments_edit.setPlainText(state['comments'])
        except Exception as e:
            print(f"Erro ao carregar último estado: {str(e)}")
            
    def save_last_state(self):
        """Salva o estado atual para uso futuro"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.last_state_file), exist_ok=True)
            
            state = {
                'sensor_sn': self.sensor_sn_edit.text(),
                'test_type': self.test_type_combo.currentText(),
                'material': self.material_combo.currentText(),
                'location': self.location_edit.text(),
                'pressure': self.pressure_spin.value(),
                'flow': self.flow_spin.value(),
                'distance': self.distance_spin.value(),
                'comments': self.comments_edit.toPlainText()
            }
            
            with open(self.last_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar último estado: {str(e)}")
        
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
            
        # Salvar último estado
        self.save_last_state()
            
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