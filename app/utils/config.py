"""
Módulo para configurações e constantes da aplicação
"""
import os
import json
from typing import Dict, Any, Optional

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
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
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