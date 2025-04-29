"""
Módulo para gerenciamento e armazenamento de dados
"""
import os
import glob
import numpy as np
import pickle
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any

class DataStore:
    """Classe para gerenciamento de dados de aquisição e análise"""
    
    # Constantes
    DEFAULT_CALIBRATION_FILE = "calibracao_sistema.pkl"
    
    @staticmethod
    def save_data(data: Dict[str, Any], prefix: str = "vazamento_continuo") -> str:
        """
        Salva dados em arquivo pickle
        
        Args:
            data: Dicionário contendo os dados
            prefix: Prefixo para o nome do arquivo
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extrair metadados se disponíveis
        metadata_str = ""
        if 'metadata' in data and isinstance(data['metadata'], dict):
            metadata = data['metadata']
            # Adicionar informações relevantes ao nome do arquivo
            if metadata.get('sensor_sn'):
                metadata_str += f"_SN{metadata['sensor_sn']}"
            if metadata.get('test_type'):
                metadata_str += f"_{metadata['test_type']}"
            if metadata.get('material'):
                metadata_str += f"_{metadata['material']}"
            if metadata.get('distance') and float(metadata.get('distance', 0)) > 0:
                metadata_str += f"_Dist{float(metadata['distance']):.1f}cm"
            if metadata.get('pressure') and float(metadata.get('pressure', 0)) > 0:
                metadata_str += f"_Press{float(metadata['pressure']):.1f}bar"
            if metadata.get('flow') and float(metadata.get('flow', 0)) > 0:
                metadata_str += f"_Fluxo{float(metadata['flow']):.1f}Lpm"
        
        # Criar nome do arquivo com timestamp e metadados
        filename = f"{prefix}_{timestamp}{metadata_str}.pkl"
        
        # Limpar caracteres inválidos no nome do arquivo
        filename = filename.replace(" ", "_").replace("/", "-").replace(":", "-")
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
            
        return filename
    
    @staticmethod
    def save_demodulated_data(data: Dict[str, Any]) -> str:
        """
        Salva dados demodulados em arquivo pickle
        
        Args:
            data: Dicionário contendo os dados demodulados
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        return DataStore.save_data(data, prefix="vazamento_demodulado")
    
    @staticmethod
    def save_calibration_data(data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Salva dados de calibração do sistema
        
        Args:
            data: Dicionário contendo os dados de calibração (parâmetros da elipse)
            filename: Nome do arquivo para salvar a calibração (opcional)
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        # Criar uma cópia do dicionário para não modificar o original
        calibration_data = data.copy()
        
        # Adicionar timestamp à calibração
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        calibration_data['timestamp'] = datetime.now().isoformat()
        calibration_data['is_calibration'] = True
        
        # Verificar se os dados de calibração contêm os parâmetros da elipse
        if 'ellipse_params' not in calibration_data:
            raise ValueError("Os dados não contêm os parâmetros da elipse necessários para calibração")
        
        # Determinar nome do arquivo
        if filename is None:
            # Extrair metadados se disponíveis
            metadata_str = ""
            if 'metadata' in calibration_data and isinstance(calibration_data['metadata'], dict):
                metadata = calibration_data['metadata']
                # Adicionar informações relevantes ao nome do arquivo
                if metadata.get('sensor_sn'):
                    metadata_str += f"_SN{metadata['sensor_sn']}"
                if metadata.get('material'):
                    metadata_str += f"_{metadata['material']}"
                if metadata.get('test_type'):
                    metadata_str += f"_{metadata['test_type']}"
            
            # Criar nome do arquivo com metadados se disponíveis
            calibration_file = f"calibracao_{timestamp}{metadata_str}.pkl"
            # Limpar caracteres inválidos no nome do arquivo
            calibration_file = calibration_file.replace(" ", "_").replace("/", "-").replace(":", "-")
        else:
            calibration_file = filename
        
        with open(calibration_file, 'wb') as f:
            pickle.dump(calibration_data, f)
            
        return calibration_file
    
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