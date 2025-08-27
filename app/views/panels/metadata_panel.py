"""
Módulo com o painel de metadados para informações do teste
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                           QComboBox, QLineEdit, QDoubleSpinBox, QLabel, QPushButton,
                           QFileDialog, QTextEdit, QCheckBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from typing import Dict, Any
import os
import json
from app.utils import log

from app.models.data_store import DataStore
from PyQt5.QtWidgets import QMessageBox, QInputDialog

class MetadataPanel(QWidget):
    """Painel para coleta de metadados sobre o teste"""
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de metadados
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.metadata : dict = {}
        self.metadata_widget_dict: dict = {}
        self.metadata_template: dict = {}
        self.metadata_template_file = "config/metadata_template.json"
        self.last_state_file = "config/last_state.json"

        self.setup_ui()
        self.load_metadata()
        self.get_metadata()
        
    def setup_ui(self):
        """Configura a interface do painel"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        metadata_group = QGroupBox("Informações para Treinamento de IA")
        metadata_form = QFormLayout()
        self.metadata_form = metadata_form
        
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

        # Labels Personalizados
        self.custom_labels_edit = QTextEdit()
        self.custom_labels_edit.setAcceptRichText(False)
        self.custom_labels_edit.setPlaceholderText('Exemplo:\n{"nome": "Temperatura", "valor": 25.3, "unidade": "C"}\n{"nome": "RPM", "valor": 1500, "unidade": "rpm"}')
        self.custom_labels_edit.setMinimumHeight(100)
        metadata_form.addRow("Labels Personalizados:", self.custom_labels_edit)
        # Texto explicativo
        self.custom_labels_help = QLabel(
            'Para criar novos labels, escreva um por linha no formato:\n'
            '{"nome": "Temperatura", "valor": 25.3, "unidade": "C"}\n'
            '{"nome": "RPM", "valor": 1500, "unidade": "rpm"}\n'
            'Você pode adicionar quantos quiser. Eles serão salvos nos metadados e carregados na próxima vez.'
        )
        self.custom_labels_help.setWordWrap(True)
        metadata_form.addRow("", self.custom_labels_help)

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
        
        self.new_entry_layout = QHBoxLayout()
        new_entry_label = QLineEdit()
        new_entry_label.setPlaceholderText("Nome do novo metadado")
        new_entry_type = QComboBox()
        new_entry_type.addItems([
            "text", 
            "text_area", 
            "float", 
            "int", 
            "filename",
            "combo",
        ])
        new_entry_button = QPushButton("Adicionar")
        self.new_entry_layout.addWidget(new_entry_label)
        self.new_entry_layout.addWidget(new_entry_type)  
        self.new_entry_layout.addWidget(new_entry_button)
        self.new_entry_layout.addWidget(QLabel(""), stretch=1)
        metadata_form.addRow("Adicionar novo metadado:", self.new_entry_layout)
        layout.addWidget(metadata_group)  
        
        # Informações adicionais
        info_label = QLabel("Estes metadados serão salvos junto com os dados de aquisição e podem ser usados posteriormente para treinar modelos de IA. Preencha os campos com as informações do teste antes de iniciar a aquisição.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Adicionar espaço vazio para expansão
        layout.addStretch(1)

        new_entry_button.clicked.connect(self.add_custom_metadata)

    def update_timestamp(self, timestamp_name: str):
        """
        Atualiza o timestamp do painel de metadados
        """
        
        def update_time():
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if timestamp_name in self.metadata_widget_dict:
                self.metadata_widget_dict[timestamp_name].setText(current_time)
        return update_time

    def add_metadata_form_row(self, metadata_name: str, metadata_type):
        """
        Adiciona uma nova linha de metadado ao formulário
        
        Args:
            metadata_name: Nome do metadado
            widget: Widget correspondente ao metadado (QLineEdit, QComboBox, etc.)
        """
        if metadata_name:
            # Create appropriate widget based on type
            log.debug(f"Adicionando metadado: {metadata_name} do tipo {metadata_type}")
            if metadata_type[0] == "text":
                widget = QLineEdit()
                widget.textChanged.connect(self.update_metadata_dict(metadata_name))
            elif metadata_type[0] == "text_area":
                widget = QTextEdit()
                widget.textChanged.connect(self.text_changed(metadata_name, widget))
            elif metadata_type[0] == "float":
                widget = QDoubleSpinBox()
                widget.setRange(-999999.0, 999999.0)
                widget.valueChanged.connect(self.update_metadata_dict(metadata_name))
            elif metadata_type[0] == "int":
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
                widget.valueChanged.connect(self.update_metadata_dict(metadata_name))
            elif metadata_type[0] == "filename":
                widget = QWidget()
                widget.setLayout(QHBoxLayout())
                line_edit = QLineEdit()
                browse_button = QPushButton("Selecionar Arquivos")
                widget.layout().addWidget(line_edit)
                widget.layout().addWidget(browse_button)
                browse_button.clicked.connect(self.on_select_clicked(line_edit))
            elif metadata_type[0] == "combo":
                widget = QComboBox()
                widget.addItems(metadata_type[1])
                widget.currentTextChanged.connect(self.update_metadata_dict(metadata_name))
            else:  # material, tipo de teste, or other combo types'
                pass

            self.metadata_widget_dict[metadata_name] = widget
            row_count = self.metadata_form.rowCount()

            metadata_layout = QHBoxLayout()
            metadata_layout.addWidget(widget, stretch = 2)
            remove_metadata_button = QPushButton("Remover")
            metadata_layout.addWidget(QLabel(""), stretch = 1)
            remove_metadata_button.clicked.connect(self.remove_metadata_row(metadata_layout))
            metadata_layout.addWidget(remove_metadata_button)
            self.metadata_form.insertRow(row_count - 1, metadata_name + ":", metadata_layout)

    def set_widget_value(self, metadata_name: str, value: Any):
        """
        Define o valor de um widget específico
        
        Args:
            widget: O widget a ser atualizado
            value: Valor a ser definido
        """

        widget = self.metadata_widget_dict[metadata_name]
        if isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value))
        elif isinstance(widget, QComboBox):
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)

    def remove_metadata_row(self, metadata_layout: QHBoxLayout):
        """
        Remove uma linha de metadado do formulário
        
        Args:
            metadata_layout: Layout da linha de metadado a ser removida
        """
        def remove(value):
            log.debug(f"Removing metadata row {metadata_layout}")
            widget = metadata_layout.itemAt(0).widget()  # Remove the widget
            for key, value in self.metadata_widget_dict.items():
                if value == widget:
                    metadata_name = key
                    break
            self.metadata_widget_dict.pop(metadata_name)
            self.metadata_template.pop(metadata_name)
            self.metadata.pop(metadata_name)
            self.metadata_form.removeRow(metadata_layout)

        return remove

    def add_custom_metadata(self):
        # Get reference to the widgets from the layout
        new_entry_label = self.new_entry_layout.itemAt(0).widget()
        new_entry_type = self.new_entry_layout.itemAt(1).widget()

        # Get the label name and type
        metadata_name = new_entry_label.text().strip()
        metadata_type = new_entry_type.currentText()

        if metadata_name in self.metadata_template.keys():
            QMessageBox.warning(self, "Metadado Duplicado", "Metadado com esse nome já existe")
            return
        
        self.metadata_template[metadata_name] = [metadata_type]
        if metadata_type == "combo":
            # create a text edit window to add options
            #is there an option of QInputDialog that is textbox instead of line edit?
            options, ok = QInputDialog.getText(self, "Opções do Combo", "Insira as opções separadas por vírgula:")
            if ok and options:
                options_list = list(set([opt.strip() for opt in options.split(',')]))
                self.metadata_template[metadata_name].append(options_list)
            elif not ok:
                del self.metadata_template[metadata_name]
                return

        default_matadata_values = {
            "text": "",
            "text_area": "",
            "float": 0.0,
            "int": 0,
            "filename": "",
            "combo": "",
        }
        self.add_metadata_form_row(metadata_name, self.metadata_template[metadata_name])
        self.metadata[metadata_name] = default_matadata_values[metadata_type]
        self.save_metadata_template()

    def on_select_clicked(self, line_edit: QLineEdit):
        def on_browse(self):
            """Abre um diálogo para selecionar arquivos manualmente (agora múltiplos)"""
            file_paths, ok = QFileDialog.getOpenFileNames(
                caption = "Selecionar arquivos",
                directory = os.path.expanduser("~"),
                filter = "Arquivos (*.*)"
            )
            if file_paths:
                filenames = [os.path.split(file_path)[-1] for file_path in file_paths]
                line_edit.setText(", ".join(filenames))
        return on_browse
            
    def update_metadata_dict(self, metadata_name: str):
        """
        Atualiza o dicionário de metadados com o valor do widget
        
        Args:
            metadata_name: Nome do metadado
        """
        def update_value(new_value):
            self.metadata[metadata_name] = new_value
            log.debug(f"Atualizando {metadata_name} para {new_value}")

        return update_value
    
    def text_changed(self, metadata_name: str, widget: QTextEdit):

        def update_metadata():
            self.metadata[metadata_name] = widget.toPlainText()
        return update_metadata

    def load_metadata(self):
        """Carrega as opções disponíveis do arquivo de configuração"""
        try:
            if os.path.exists(self.metadata_template_file):
                with open(self.metadata_template_file, 'r', encoding='utf-8') as f:
                    self.metadata_template.update(json.load(f))

                for key, value in self.metadata_template.items():
                    log.debug(f"Carregando metadado: {key} do tipo {value}")
                    self.add_metadata_form_row(key, value)

        except Exception as e:
            log.error(f"Erro ao carregar opções: {str(e)}")

        try:
            if os.path.exists(self.last_state_file):
                with open(self.last_state_file, 'r', encoding='utf-8') as f:
                    self.metadata.update(json.load(f)["metadata"])
                    log.debug(f"Último estado carregado: {self.metadata}")

            for key, value in self.metadata.items():
                if key in self.metadata_widget_dict:
                    self.set_widget_value(key, value)

        except Exception as e:
<<<<<<< HEAD
            log_error(f"Erro ao carregar último estado: {str(e)}")
            
        for key, value in self.metadata.items():
            pass
            #self.set_widget_value(key, value)
=======
            log.error(f"Erro ao carregar último estado: {str(e)}")

>>>>>>> db4e97fd2148c52ebfbb81570be8dfceb8b2e7e1

    def save_metadata_template(self):
        """Salva os metadados atuais no arquivo de configuração"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.metadata_template_file), exist_ok=True)
            # Salvar os metadados no arquivo
            with open(self.metadata_template_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_template, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log.error(f"Erro ao salvar opções: {str(e)}")
                
    def get_metadata(self) -> Dict[str, Any]:
        """
        Coleta os metadados do painel
        
        Returns:
            Dicionário com os metadados
        """
        checked_status = [cb.text() for cb in self.status_checkboxes if cb.isChecked()]
        # Parse custom labels
        custom_labels_raw = self.custom_labels_edit.toPlainText().strip()
        custom_labels = []
        if custom_labels_raw:
            for line in custom_labels_raw.splitlines():
                line = line.strip()
                if line:
                    try:
                        label = json.loads(line)
                        custom_labels.append(label)
                    except Exception:
                        pass  # Ignora linhas inválidas
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "save_directory": self.save_directory
        }
        # Adicionar labels personalizados no mesmo nível
        for label in custom_labels:
            if isinstance(label, dict) and 'nome' in label:
                nome = label['nome']
                valor = label.get('valor', None)
                unidade = label.get('unidade', None)
                metadata[nome] = valor
                if unidade is not None:
                    metadata[f"{nome}_unit"] = unidade
        # Adicionar fotos se existirem
        if hasattr(self, 'setup_photos'):
            metadata['setup_photos'] = self.setup_photos
        return metadata
        
    def select_save_directory(self):
        """Abre um diálogo para selecionar a pasta de salvamento"""
        directory = QFileDialog.getExistingDirectory(self, "Selecione a Pasta de Destino", self.save_directory)
        if directory:
            self.save_directory = directory
            self.save_dir_button.setText(directory)
            # Salvar nas configurações
            config = DataStore.load_config()
            config['save_directory'] = directory
            DataStore.save_config(config)
    
    def load_setup_photos(self):
        """Abre um diálogo para carregar fotos do setup"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Selecionar Fotos do Setup", 
            "", 
            "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if files:
            self.setup_photos = files
            self.setup_photos_label.setText(f"{len(files)} foto(s) carregada(s)")
        else:
            self.setup_photos_label.setText("Nenhuma foto carregada")
        
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