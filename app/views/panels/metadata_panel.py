"""
Módulo com o painel de metadados para informações do teste
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QLabel, QPushButton,
                           QFileDialog, QTextEdit, QCheckBox, QSpinBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from typing import Dict, Any, List
import os
import json

from app.models.data_store import DataStore
from app.utils.time_utils import get_formatted_internet_timestamp, get_iso_brasilia_timestamp, get_brasilia_timestamp

class VariableInputWidget(QWidget):
    """Widget para entrada de uma variável personalizada"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do widget"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Campo para nome da variável
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nome da variável")
        self.name_edit.setMinimumWidth(120)
        
        # Campo para valor
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Valor")
        self.value_edit.setMinimumWidth(100)
        
        # Campo para unidade
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Unidade")
        self.unit_edit.setMinimumWidth(80)
        

        
        # Botão para remover esta variável
        self.remove_button = QPushButton("X")
        self.remove_button.setMaximumWidth(30)
        self.remove_button.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; border: none; border-radius: 3px; }")
        
        layout.addWidget(QLabel("Nome:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Valor:"))
        layout.addWidget(self.value_edit)
        layout.addWidget(QLabel("Unidade:"))
        layout.addWidget(self.unit_edit)
        layout.addWidget(self.remove_button)
        layout.addStretch(1)
        
    def get_data(self) -> Dict[str, Any]:
        """Retorna os dados da variável"""
        return {
            'nome': self.name_edit.text().strip(),
            'valor': self.value_edit.text().strip(),
            'unidade': self.unit_edit.text().strip()
        }
        
    def set_data(self, data: Dict[str, Any]):
        """Define os dados da variável"""
        self.name_edit.setText(str(data.get('nome', '')))
        self.value_edit.setText(str(data.get('valor', '')))
        self.unit_edit.setText(str(data.get('unidade', '')))

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
        self.variable_widgets: List[VariableInputWidget] = []
        self.setup_ui()
        # Timer de auto-salvamento (debounce)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(600)
        self._autosave_timer.timeout.connect(self.save_last_state)
        # Conectar sinais para auto-salvar quando campos mudarem
        self._connect_autosave_signals()
        self.load_options()
        self.load_last_state()
        
        # Inicializar base de tempo uma única vez e atualizar a partir dela
        from app.utils.time_utils import time_sync
        try:
            time_sync.initialize_base_time()
        except Exception:
            pass
        self.timestamp_timer = QTimer()
        self.timestamp_timer.timeout.connect(self.update_timestamp)
        self.timestamp_timer.start(1000)  # Atualizar a cada segundo
        
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

        # Timestamp atual
        self.timestamp_label = QLabel()
        self.timestamp_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 3px; }")
        self.update_timestamp()
        metadata_form.addRow("Timestamp Atual:", self.timestamp_label)
        
        # Comentários
        self.comments_edit = QTextEdit()
        self.comments_edit.setAcceptRichText(False)  # Desabilitar formatação rica
        self.comments_edit.setPlaceholderText("Digite seus comentários aqui...")
        self.comments_edit.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.comments_edit.setMinimumHeight(200)
        metadata_form.addRow("Comentários:", self.comments_edit)

        # Variáveis Personalizadas
        variables_group = QGroupBox("Variáveis Personalizadas")
        variables_layout = QVBoxLayout()
        
        # Área de scroll para as variáveis
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.variables_container = QWidget()
        self.variables_container_layout = QVBoxLayout(self.variables_container)
        
        scroll_area.setWidget(self.variables_container)
        variables_layout.addWidget(scroll_area)
        
        # Botão para adicionar nova variável
        self.add_variable_button = QPushButton("+ Adicionar Nova Variável")
        self.add_variable_button.clicked.connect(self.add_variable_widget)
        self.add_variable_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; padding: 8px; border-radius: 4px; }")
        variables_layout.addWidget(self.add_variable_button)
        
        # Texto explicativo
        variables_help = QLabel(
            'Adicione variáveis personalizadas para incluir nos metadados.\n'
            'Para cada variável, especifique: Nome, Valor e Unidade.\n'
            'Clique no botão "+" para adicionar mais variáveis.'
        )
        variables_help.setWordWrap(True)
        variables_layout.addWidget(variables_help)
        
        variables_group.setLayout(variables_layout)
        metadata_form.addRow("", variables_group)

        # Botão para selecionar pasta de salvamento
        self.save_dir_button = QPushButton("Selecionar Pasta de Destino")
        self.save_dir_button.clicked.connect(self.select_save_directory)
        self.save_directory = DataStore.load_config().get('save_directory', os.getcwd())  # Carregar das configurações
        self.save_dir_button.setText(self.save_directory)  # Mostrar pasta atual
        metadata_form.addRow("Pasta de Destino:", self.save_dir_button)

        # Tipo de Equipamento
        self.equipment_type_combo = QComboBox()
        metadata_form.addRow("Tipo de Equipamento:", self.equipment_type_combo)
        # Grupo de status do equipamento (checkboxes)
        self.status_options = [
            "Água Circulante", "Água Estática","Oxigênio Ligado", "Oxigênio Desligado", "Ligado", "Desligado",
            "Válvula Aberta", "Válvula Fechada", "Com Vazamento", "Sem Vazamento"
        ]
        self.status_checkboxes = []
        status_layout = QHBoxLayout()
        for opt in self.status_options:
            cb = QCheckBox(opt)
            self.status_checkboxes.append(cb)
            status_layout.addWidget(cb)
        status_group = QGroupBox()
        status_group.setLayout(status_layout)
        metadata_form.addRow("Status do Equipamento:", status_group)

        metadata_group.setLayout(metadata_form)
        layout.addWidget(metadata_group)  
        
        # Informações adicionais
        info_label = QLabel("Estes metadados serão salvos junto com os dados de aquisição e podem ser usados posteriormente para treinar modelos de IA. Preencha os campos com as informações do teste antes de iniciar a aquisição.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)
        
        # Adicionar uma variável inicial
        self.add_variable_widget()
        
    def add_variable_widget(self):
        """Adiciona um novo widget de variável"""
        variable_widget = VariableInputWidget()
        variable_widget.remove_button.clicked.connect(lambda: self.remove_variable_widget(variable_widget))
        
        self.variable_widgets.append(variable_widget)
        self.variables_container_layout.addWidget(variable_widget)
        # Conectar sinais de edição para auto-salvar
        try:
            variable_widget.name_edit.textChanged.connect(self.schedule_auto_save)
            variable_widget.value_edit.textChanged.connect(self.schedule_auto_save)
            variable_widget.unit_edit.textChanged.connect(self.schedule_auto_save)
        except Exception:
            pass
        
    def remove_variable_widget(self, widget):
        """Remove um widget de variável"""
        if len(self.variable_widgets) > 1:  # Manter pelo menos um widget
            self.variable_widgets.remove(widget)
            widget.deleteLater()
        
    def get_variables_data(self) -> List[Dict[str, Any]]:
        """Retorna os dados de todas as variáveis"""
        variables = []
        for widget in self.variable_widgets:
            data = widget.get_data()
            if data['nome']:  # Só incluir se tiver nome
                variables.append(data)
        return variables
        
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
                    
                # Novo: opções de equipamento
                self.equipment_types = config.get('equipment_types', [])
                self.equipment_type_combo.clear()
                self.equipment_type_combo.addItems(self.equipment_types)
        except Exception as e:
            print(f"Erro ao carregar opções: {str(e)}")
            
    def save_options(self):
        """Salva as opções atuais no arquivo de configuração"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config = {
                'test_types': [self.test_type_combo.itemText(i) for i in range(self.test_type_combo.count())],
                'materials': [self.material_combo.itemText(i) for i in range(self.material_combo.count())],
                'equipment_types': self.equipment_types
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
                if 'equipment_type' in state:
                    index = self.equipment_type_combo.findText(state['equipment_type'])
                    if index >= 0:
                        self.equipment_type_combo.setCurrentIndex(index)
                if 'equipment_status' in state:
                    # Novo: restaurar checkboxes
                    checked_status = state['equipment_status'] if isinstance(state['equipment_status'], list) else []
                    for cb in self.status_checkboxes:
                        cb.setChecked(cb.text() in checked_status)
                if 'comments' in state:
                    self.comments_edit.setPlainText(state['comments'])
                if 'save_directory' in state and isinstance(state['save_directory'], str) and state['save_directory']:
                    self.save_directory = state['save_directory']
                    self.save_dir_button.setText(self.save_directory)
                if 'setup_photos' in state and isinstance(state['setup_photos'], list):
                    self.setup_photos = state['setup_photos']
                    self.setup_photos_label.setText(f"{len(self.setup_photos)} foto(s) selecionada(s)")
                if 'custom_labels' in state:
                    # Carregar variáveis personalizadas do estado salvo
                    custom_labels = state['custom_labels']
                    if isinstance(custom_labels, list) and custom_labels:
                        # Limpar widgets existentes (exceto o primeiro)
                        while len(self.variable_widgets) > 1:
                            widget = self.variable_widgets.pop()
                            widget.deleteLater()
                        
                        # Configurar o primeiro widget
                        if len(custom_labels) > 0:
                            self.variable_widgets[0].set_data(custom_labels[0])
                        
                        # Adicionar widgets adicionais se necessário
                        for i in range(1, len(custom_labels)):
                            self.add_variable_widget()
                            self.variable_widgets[-1].set_data(custom_labels[i])
        except Exception as e:
            print(f"Erro ao carregar último estado: {str(e)}")
            
    def save_last_state(self):
        """Salva o estado atual para uso futuro"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.last_state_file), exist_ok=True)
            checked_status = [cb.text() for cb in self.status_checkboxes if cb.isChecked()]
            state = {
                'sensor_sn': self.sensor_sn_edit.text(),
                'test_type': self.test_type_combo.currentText(),
                'material': self.material_combo.currentText(),
                'location': self.location_edit.text(),
                'pressure': self.pressure_spin.value(),
                'flow': self.flow_spin.value(),
                'distance': self.distance_spin.value(),
                'equipment_type': self.equipment_type_combo.currentText(),
                'equipment_status': checked_status,
                'comments': self.comments_edit.toPlainText(),
                'custom_labels': self.get_variables_data(),
                'save_directory': getattr(self, 'save_directory', ''),
                'setup_photos': getattr(self, 'setup_photos', [])
            }
            
            with open(self.last_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar último estado: {str(e)}")
    
    def _connect_autosave_signals(self):
        """Conecta sinais dos widgets para auto-salvar ao alterar valores"""
        try:
            self.sensor_sn_edit.textChanged.connect(self.schedule_auto_save)
            self.test_type_combo.currentIndexChanged.connect(self.schedule_auto_save)
            self.material_combo.currentIndexChanged.connect(self.schedule_auto_save)
            self.location_edit.textChanged.connect(self.schedule_auto_save)
            self.pressure_spin.valueChanged.connect(self.schedule_auto_save)
            self.flow_spin.valueChanged.connect(self.schedule_auto_save)
            self.distance_spin.valueChanged.connect(self.schedule_auto_save)
            self.equipment_type_combo.currentIndexChanged.connect(self.schedule_auto_save)
            self.comments_edit.textChanged.connect(self.schedule_auto_save)
            for cb in self.status_checkboxes:
                cb.toggled.connect(self.schedule_auto_save)
        except Exception:
            pass
    
    def schedule_auto_save(self):
        """Agenda um auto-salvamento com debounce"""
        try:
            self._autosave_timer.start()
        except Exception:
            # Fallback: salvar diretamente se timer não estiver disponível
            self.save_last_state()
        
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
        
    def select_save_directory(self):
        """Abre um diálogo para selecionar a pasta de destino dos arquivos"""
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a pasta para salvar os dados", self.save_directory)
        if dir_path:
            self.save_directory = dir_path
            self.save_dir_button.setText(dir_path)
            
            # Salvar a pasta escolhida nas configurações
            config = DataStore.load_config()
            config['save_directory'] = dir_path
            DataStore.save_config(config)
            # Persistir também no último estado
            self.save_last_state()
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Coleta os metadados do painel
        
        Returns:
            Dicionário com os metadados
        """
        checked_status = [cb.text() for cb in self.status_checkboxes if cb.isChecked()]
        # Obter variáveis personalizadas
        custom_labels = self.get_variables_data()
        metadata = {
            "sensor_sn": self.sensor_sn_edit.text(),
            "test_type": self.test_type_combo.currentText(),
            "material": self.material_combo.currentText(),
            "location": self.location_edit.text(),
            "pressure": self.pressure_spin.value(),
            "pressure_unit": "bar",
            "flow": self.flow_spin.value(),
            "flow_unit": "L/min",
            "distance": self.distance_spin.value(),
            "distance_unit": "cm",
            "equipment_type": self.equipment_type_combo.currentText(),
            "equipment_status": checked_status,
            "comments": self.comments_edit.toPlainText(),
            "timestamp": get_brasilia_timestamp(),
            "timestamp_iso": get_iso_brasilia_timestamp(),
            "save_directory": self.save_directory
        }
        
        # Adicionar variáveis personalizadas no mesmo nível
        for label in custom_labels:
            if isinstance(label, dict) and 'nome' in label:
                nome = label['nome']
                valor = label.get('valor', None)
                unidade = label.get('unidade', None)
                
                # Adicionar a variável principal
                metadata[nome] = valor
                
                # Adicionar unidade se especificada
                if unidade is not None:
                    metadata[f"{nome}_unit"] = unidade
        
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
        
        # Limpar variáveis personalizadas
        for widget in self.variable_widgets:
            widget.name_edit.clear()
            widget.value_edit.clear()
            widget.unit_edit.clear()
        
        if hasattr(self, 'setup_photos'):
            delattr(self, 'setup_photos')
        self.setup_photos_label.setText("Nenhuma foto carregada")
    
    def update_timestamp(self):
        """Atualiza o timestamp exibido na interface"""
        try:
            # Tentar obter horário da internet
            utc_timestamp = get_formatted_internet_timestamp()
            brasilia_timestamp = get_brasilia_timestamp()
            self.timestamp_label.setText(f"{brasilia_timestamp} (Brasília - Internet)")
        except Exception as e:
            # Fallback para timestamp local se não conseguir internet
            local_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.timestamp_label.setText(f"{local_timestamp} (PC Local)") 