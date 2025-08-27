"""
Módulo para configurações e constantes da aplicação
"""
import os
import json
from typing import Dict, Any, Optional, Callable, List, Type, Union
from PyQt5.QtWidgets import QWidget

# Configurações padrão da aplicação
DEFAULT_CONFIG = {
    "acquisition": {
        "default_ip": "rp-f0b916.local",
        "default_duration": 5.0,
        "default_decimation": 64,
        "base_sample_rate": 125e6
    },
    "processing": {
        "max_fit_points": 100000,
        "default_window": "blackman"
    },
    "display": {
        "max_plot_points": 10000,
        "theme": "light",
        "default_dpi": 100
    },
    "paths": {
        "data_dir": "data",
        "export_dir": "export"
    }
}

# Nome do arquivo de configuração
CONFIG_FILENAME = "oas_config.json"

class Config:
    """Classe para gerenciamento de configurações da aplicação"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Implementação de Singleton"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_last_state()
        return cls._instance
    
    def _load_last_state(self):
        """Carrega as configurações do arquivo"""
        # Inicializar com valores padrão
        self._config = DEFAULT_CONFIG.copy()
        
        # Tentar carregar do arquivo
        if os.path.exists(CONFIG_FILENAME):
            try:
                with open(CONFIG_FILENAME, 'r') as f:
                    user_config = json.load(f)
                    
                # Atualizar configurações com valores do arquivo
                self._update_config(self._config, user_config)
            except Exception as e:
                print(f"Erro ao carregar configurações: {str(e)}")
                
        # Garantir que diretórios existam
        self._ensure_directories()
    
    def _update_config(self, target: Dict[str, Any], source: Dict[str, Any]):
        """
        Atualiza as configurações recursivamente
        
        Args:
            target: Dicionário alvo
            source: Dicionário fonte
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value)
            else:
                target[key] = value
    
    def _ensure_directories(self):
        """Garante que os diretórios necessários existam"""
        for dir_name in self._config["paths"].values():
            os.makedirs(dir_name, exist_ok=True)
    
    def save(self):
        """Salva as configurações em arquivo"""
        try:
            with open(CONFIG_FILENAME, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configurações: {str(e)}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Obtém uma configuração
        
        Args:
            section: Seção da configuração
            key: Chave da configuração
            default: Valor padrão caso não encontrado
            
        Returns:
            Valor da configuração ou o valor padrão
        """
        try:
            return self._config[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """
        Define uma configuração
        
        Args:
            section: Seção da configuração
            key: Chave da configuração
            value: Valor da configuração
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtém uma seção de configuração
        
        Args:
            section: Nome da seção
            
        Returns:
            Dicionário com as configurações da seção
        """
        return self._config.get(section, {}).copy()

# Funções de acesso fácil às configurações
def get_config(section: str, key: str, default: Any = None) -> Any:
    """
    Função para acessar configurações facilmente
    
    Args:
        section: Seção da configuração
        key: Chave da configuração
        default: Valor padrão caso não encontrado
        
    Returns:
        Valor da configuração
    """
    return Config().get(section, key, default)

def set_config(section: str, key: str, value: Any):
    """
    Função para definir configurações facilmente
    
    Args:
        section: Seção da configuração
        key: Chave da configuração
        value: Valor da configuração
    """
    Config().set(section, key, value)
    Config().save() 


# Widget traversal utilities
def traverse_widgets(
    widget: QWidget, 
    apply_function: Callable[[QWidget], None], 
    widget_types: Optional[Union[Type, List[Type]]] = None,
    recursive: bool = True
) -> List[QWidget]:
    """
    Traverses all child widgets of a given widget and applies a function to them.
    
    Args:
        widget: The parent widget to traverse
        apply_function: Function to apply to each matching widget
        widget_types: Type or list of types to filter by (e.g., QPushButton, QLabel).
                     If None, applies to all QWidget instances.
        recursive: If True, traverses recursively through all child widgets
        
    Returns:
        List of widgets that were processed
    """
    processed_widgets = []
    if widget_types is None:
        widget_types = [QWidget]
    elif not isinstance(widget_types, list):
        widget_types = [widget_types]
    
    def _traverse_recursive(current_widget: QWidget):
        """Internal recursive function"""
        # Check if current widget matches any of the desired types
        if any(isinstance(current_widget, widget_type) for widget_type in widget_types):
            try:
                apply_function(current_widget)
                processed_widgets.append(current_widget)
            except Exception as e:
                print(f"Error applying function to widget {current_widget}: {e}")
        
        # Traverse children if recursive is enabled
        if recursive:
            for child in current_widget.children():
                if isinstance(child, QWidget):
                    _traverse_recursive(child)
    
    # Start traversal
    _traverse_recursive(widget)
    return processed_widgets


def find_widgets_by_type(widget: QWidget, widget_types: Union[Type, List[Type]]) -> List[QWidget]:
    """
    Find all child widgets of specific type(s).
    
    Args:
        widget: The parent widget to search in
        widget_types: Type or list of types to search for
        
    Returns:
        List of widgets matching the specified types
    """
    found_widgets = []
    
    def collect_widget(w: QWidget):
        found_widgets.append(w)
    
    traverse_widgets(widget, collect_widget, widget_types, recursive=True)
    return found_widgets


def apply_to_widget_type(
    widget: QWidget, 
    widget_type: Type, 
    apply_function: Callable[[QWidget], None]
) -> int:
    """
    Apply a function to all widgets of a specific type.
    
    Args:
        widget: The parent widget to search in
        widget_type: The type of widget to apply the function to
        apply_function: Function to apply to each matching widget
        
    Returns:
        Number of widgets processed
    """
    processed = traverse_widgets(widget, apply_function, widget_type, recursive=True)
    return len(processed)


    
