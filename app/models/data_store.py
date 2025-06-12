"""
Módulo para gerenciamento e armazenamento de dados
"""
import os
import glob
import numpy as np
import pickle
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any
import json

class DataStore:
    """Classe para gerenciamento de dados de aquisição e análise"""
    
    # Constantes
    DEFAULT_CALIBRATION_FILE = "calibracao_sistema.pkl"
    CONFIG_FILE = "config/data_store_config.json"
    
    @staticmethod
    def save_config(config: Dict[str, Any]) -> None:
        """
        Salva as configurações em arquivo
        
        Args:
            config: Dicionário com as configurações
        """
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(DataStore.CONFIG_FILE), exist_ok=True)
        
        # Salvar configurações
        with open(DataStore.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Carrega as configurações do arquivo
        
        Returns:
            Dicionário com as configurações
        """
        # Se o arquivo não existe, retornar configurações padrão
        if not os.path.exists(DataStore.CONFIG_FILE):
            return {}
            
        # Carregar configurações
        try:
            with open(DataStore.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações: {str(e)}")
            return {}
    
    @staticmethod
    def save_data(data: Dict[str, Any], prefix: str = "vazamento_continuo", directory: str = None) -> str:
        """
        Salva dados em arquivo pickle
        
        Args:
            data: Dicionário contendo os dados
            prefix: Prefixo para o nome do arquivo
            directory: Diretório onde salvar o arquivo
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        # Se não foi especificado um diretório, tentar carregar das configurações
        if directory is None:
            directory = DataStore.load_config().get('save_directory')
            
        # Se ainda não temos diretório, usar o atual
        if directory is None:
            directory = os.getcwd()
            
        # Garantir que o diretório existe
        os.makedirs(directory, exist_ok=True)
        
        # Criar nome do arquivo com timestamp e labels
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata = data.get('metadata', {})
        
        # Extrair labels principais (sempre incluir, mesmo se zero ou vazio)
        sensor_sn = metadata.get('sensor_sn', '')
        test_type = metadata.get('test_type', '')
        material = metadata.get('material', '')
        distance = metadata.get('distance', 0)
        pressure = metadata.get('pressure', 0)
        flow = metadata.get('flow', 0)
        
        # Montar string de labels
        label_str = f"_SN{sensor_sn}_Tipo{test_type}_Material{material}_Dist{distance}cm_Press{pressure}bar_Fluxo{flow}Lmin"
        # Limpar caracteres inválidos
        label_str = label_str.replace(' ', '_').replace('/', '-').replace(':', '-')
        
        filename = f"{prefix}_{timestamp}{label_str}.pkl"
        
        # Adicionar metadados ao arquivo
        if 'metadata' not in data:
            data['metadata'] = {}
        data['metadata']['timestamp'] = timestamp
        
        # Salvar arquivo
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        return filepath
    
    @staticmethod
    def save_demodulated_data(data: Dict[str, Any]) -> str:
        """
        Salva dados demodulados em arquivo pickle
        
        Args:
            data: Dicionário contendo os dados demodulados
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        # Obter diretório das configurações
        directory = DataStore.load_config().get('save_directory')
        return DataStore.save_data(data, prefix="vazamento_demodulado", directory=directory)
    
    @staticmethod
    def save_calibration_data(data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Salva dados de calibração em arquivo pickle
        
        Args:
            data: Dicionário contendo os dados de calibração
            filename: Nome do arquivo de calibração ou None para usar o padrão
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        # Se não foi especificado um nome de arquivo, usar o padrão
        if filename is None:
            filename = DataStore.DEFAULT_CALIBRATION_FILE
            
        # Obter diretório das configurações
        directory = DataStore.load_config().get('save_directory')
        
        # Garantir que o diretório existe
        if directory:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
        else:
            filepath = filename
            
        # Salvar arquivo
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
            
        return filepath
    
    @staticmethod
    def load_calibration_data(filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados de calibração do sistema, se disponíveis
        
        Args:
            filename: Nome do arquivo de calibração para carregar (opcional)
            
        Returns:
            Dicionário contendo os dados de calibração ou None se não existir
        """
        # Determinar nome do arquivo
        calibration_file = filename if filename else DataStore.DEFAULT_CALIBRATION_FILE
        
        if not os.path.exists(calibration_file):
            return None
            
        try:
            with open(calibration_file, 'rb') as f:
                calibration_data = pickle.load(f)
                
            # Verificar se é um arquivo de calibração válido
            if not calibration_data.get('is_calibration', False) or 'ellipse_params' not in calibration_data:
                return None
                
            return calibration_data
        except Exception:
            return None
    
    @staticmethod
    def has_valid_calibration(filename: Optional[str] = None) -> bool:
        """
        Verifica se existe um arquivo de calibração válido
        
        Args:
            filename: Nome do arquivo de calibração para verificar (opcional)
            
        Returns:
            True se existe um arquivo de calibração válido, False caso contrário
        """
        return DataStore.load_calibration_data(filename) is not None
    
    @staticmethod
    def get_available_calibration_files() -> List[str]:
        """
        Obtém a lista de arquivos de calibração disponíveis
        
        Returns:
            Lista de caminhos para os arquivos de calibração disponíveis
        """
        calibration_files = []
        
        # Procurar arquivos de calibração com padrão calibracao_*.pkl
        calibration_files.extend(glob.glob("calibracao_*.pkl"))
        
        # Incluir o arquivo padrão de calibração se existir
        if os.path.exists(DataStore.DEFAULT_CALIBRATION_FILE):
            calibration_files.append(DataStore.DEFAULT_CALIBRATION_FILE)
        
        # Ordenar por data de modificação (mais recente primeiro)
        calibration_files.sort(key=os.path.getmtime, reverse=True)
        
        return calibration_files
    
    @staticmethod
    def load_data(filename: str) -> Dict[str, Any]:
        """
        Carrega dados de um arquivo pickle
        
        Args:
            filename: Nome do arquivo a ser carregado
            
        Returns:
            Dicionário contendo os dados carregados
        """
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            
        # Converter para dicionário se não for
        if not isinstance(data, dict):
            temp_dict = {}
            for key in dir(data):
                if not key.startswith('__') and not callable(getattr(data, key)):
                    temp_dict[key] = getattr(data, key)
            data = temp_dict
            
        # Verificar se temos dados de tempo e criar se não existir
        if 'waveforms' in data and 't' not in data:
            if 'sample_frequency_effective' in data:
                fs = data['sample_frequency_effective']
                wf_len = data['waveforms'].shape[1]
                data['t'] = np.arange(wf_len) / fs
                
        return data
    
    @staticmethod
    def get_available_files(include_all: bool = True) -> List[str]:
        """
        Obtém a lista de arquivos de dados disponíveis
        
        Args:
            include_all: Se deve incluir todos os tipos de arquivo ou apenas os brutos
            
        Returns:
            Lista de caminhos para os arquivos disponíveis
        """
        pkl_files = []
        
        # Procurar arquivos .pkl
        pkl_files.extend(glob.glob("vazamento_sensor_*.pkl"))
        pkl_files.extend(glob.glob("vazamento_continuo_*.pkl"))
        
        if include_all:
            pkl_files.extend(glob.glob("vazamento_demodulado_*.pkl"))
        
        # Ordenar por data de modificação (mais recente primeiro)
        pkl_files.sort(key=os.path.getmtime, reverse=True)
        
        return pkl_files 