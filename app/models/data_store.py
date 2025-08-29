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
import toml
import unicodedata
from app.utils.time_utils import get_formatted_internet_timestamp, get_brasilia_timestamp

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
    def save_data(data: Dict[str, Any], prefix: str = None, directory: str = None, calibration_data: Dict[str, Any] = None) -> str:
        """
        Salva dados brutos em arquivo pickle e metadados em TOML
        
        Args:
            data: Dicionário contendo os dados
            prefix: Prefixo para o nome do arquivo
            directory: Diretório onde salvar o arquivo
            calibration_data: Dados de calibração opcionais para incluir nos metadados
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        def clean(s):
            # Remove acentos, espaços e caracteres especiais
            s = ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')
            s = s.replace(' ', '').replace('/', '-').replace(':', '-')
            return s
            
        # Dicionário de abreviações para status
        status_abbr = {
            'Água Circulante': 'AgC',
            'Água Estática': 'AgE',
            'Oxigênio Ligado': 'OxL',
            'Oxigênio Desligado': 'OxD',
            'Ligado': 'Lig',
            'Desligado': 'Des',
            'Válvula Aberta': 'VAb',
            'Válvula Fechada': 'VFe',
            'Com Vazamento': 'CVaz',
            'Sem Vazamento': 'SVaz',
        }
        
        # Abreviações para campos principais
        field_abbr = {
            'sensor_sn': 'SN',
            'test_type': 'Tipo',
            'material': 'Mat',
            'distance': 'Dist',
            'pressure': 'Press',
            'flow': 'Flux',
            'equipment_type': 'Equip',
            'equipment_status': 'Status',
            'location': 'Local',
        }
        
        if directory is None:
            directory = DataStore.load_config().get('save_directory')
        if directory is None:
            directory = os.getcwd()
        os.makedirs(directory, exist_ok=True)
        
        timestamp = get_brasilia_timestamp("%Y%m%d_%H%M%S")
        metadata = data.get('metadata', {})
        
        # Extrair e abreviar campos
        sensor_sn = clean(metadata.get('sensor_sn', ''))
        test_type = clean(metadata.get('test_type', ''))
        material = clean(metadata.get('material', ''))
        distance = clean(metadata.get('distance', 0))
        pressure = clean(metadata.get('pressure', 0))
        flow = clean(metadata.get('flow', 0))
        equipment_type = clean(metadata.get('equipment_type', ''))
        equipment_status = metadata.get('equipment_status', [])
        if isinstance(equipment_status, list):
            status_str = '_'.join([status_abbr.get(s, clean(s)) for s in equipment_status])
        else:
            status_str = status_abbr.get(str(equipment_status), clean(equipment_status))
        location = clean(metadata.get('location', ''))
        
        # Procurar informação de vazamento/não vazamento nos metadados
        vazamento_info = ''
        for key in metadata:
            if 'vazamento' in key.lower():
                val = str(metadata[key]).lower()
                if 'nao' in val or 'não' in val:
                    vazamento_info = '_NaoVazamento'
                    break
                elif 'sim' in val or 'com' in val:
                    vazamento_info = '_ComVazamento'
                    break
                elif 'sem' in val:
                    vazamento_info = '_SemVazamento'
                    break
                elif 'vazamento' in val:
                    vazamento_info = '_Vazamento'
                    break
                    
        # Determinar o prefixo correto baseado no tipo de teste
        if prefix is not None:
            file_prefix = prefix
        else:
            test_type_lower = test_type.lower()
            if 'vazamento' in test_type_lower:
                if 'agua' in test_type_lower or 'água' in test_type_lower:
                    file_prefix = "vazamento_agua"
                elif 'ar' in test_type_lower:
                    file_prefix = "vazamento_ar"
                elif 'gas' in test_type_lower or 'gás' in test_type_lower:
                    file_prefix = "vazamento_gas"
                else:
                    file_prefix = "vazamento"
            elif 'descarga' in test_type_lower or 'eletrica' in test_type_lower or 'elétrica' in test_type_lower:
                file_prefix = "descarga_eletrica"
            elif 'ruido' in test_type_lower or 'ruído' in test_type_lower or 'mecanico' in test_type_lower or 'mecânico' in test_type_lower:
                file_prefix = "ruido_mecanico"
            elif 'controle' in test_type_lower or 'sem vazamento' in test_type_lower:
                file_prefix = "controle_sem_vazamento"
            else:
                file_prefix = "teste"
        
        # Montar string de labels abreviados
        label_str = f"_{field_abbr['sensor_sn']}{sensor_sn}_{field_abbr['test_type']}{test_type}_{field_abbr['material']}{material}_{field_abbr['distance']}{distance}cm_{field_abbr['pressure']}{pressure}b_{field_abbr['flow']}{flow}L_{field_abbr['equipment_type']}{equipment_type}_{field_abbr['equipment_status']}{status_str}_{field_abbr['location']}{location}{vazamento_info}"
        filename = f"{file_prefix}_{timestamp}{label_str}.pkl"
        
        # Preparar dados brutos para salvar (sem dados demodulados)
        raw_data = {
            'waveforms': data.get('waveforms'),
            't': data.get('t'),
            'channels': data.get('channels'),
            'sample_frequency': data.get('sample_frequency'),
            'decimation': data.get('decimation'),
            'acquisition_time': data.get('acquisition_time'),
            'ip_address': data.get('ip_address')
        }
        
        # Adicionar timestamp aos metadados
        if 'metadata' not in data:
            data['metadata'] = {}
        data['metadata']['timestamp'] = timestamp
        
        # Incluir parâmetros da elipse do arquivo de calibração se disponível
        if calibration_data and 'ellipse_params' in calibration_data:
            data['metadata']['ellipse_params'] = calibration_data['ellipse_params']
            data['metadata']['calibration_file_used'] = calibration_data.get('calibration_file', '')
            data['metadata']['calibration_timestamp_used'] = calibration_data.get('calibration_timestamp', '')
        
        # Salvar dados brutos em pickle
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(raw_data, f)
            
        # Criar estrutura TOML para metadados
        toml_metadata = {
            'acquisition_info': {
                'timestamp': timestamp,
                'sample_frequency': data.get('sample_frequency'),
                'decimation': data.get('decimation'),
                'effective_sample_rate': data.get('sample_frequency', 0) / data.get('decimation', 1),
                'acquisition_time': data.get('acquisition_time'),
                'channels': data.get('channels', [])
            },
            'hardware_info': {
                'redpitaya_model': 'STEMlab 125-14',
                'firmware_version': '1.04',
                'ip_address': data.get('ip_address', '')
            },
            'calibration_info': {
                'calibration_file': metadata.get('calibration_file', ''),
                'ellipse_params': DataStore._ensure_ellipse_params_numeric(metadata.get('ellipse_params', {})),
                'calibration_timestamp': metadata.get('calibration_timestamp', ''),
                'calibration_file_used': metadata.get('calibration_file_used', ''),
                'calibration_timestamp_used': metadata.get('calibration_timestamp_used', '')
            },
            'test_metadata': {
                'sensor_sn': metadata.get('sensor_sn', ''),
                'test_type': metadata.get('test_type', ''),
                'material': metadata.get('material', ''),
                'location': metadata.get('location', ''),
                'pressure': metadata.get('pressure', 0.0),
                'pressure_unit': metadata.get('pressure_unit', 'bar'),
                'flow': metadata.get('flow', 0.0),
                'flow_unit': metadata.get('flow_unit', 'L/min'),
                'distance': metadata.get('distance', 0.0),
                'distance_unit': metadata.get('distance_unit', 'cm'),
                'equipment_type': metadata.get('equipment_type', ''),
                'equipment_status': metadata.get('equipment_status', []),
                'comments': metadata.get('comments', ''),
                'timestamp': metadata.get('timestamp', ''),
                'timestamp_iso': metadata.get('timestamp_iso', ''),
                'save_directory': metadata.get('save_directory', '')
            },
            'file_info': {
                'data_shape': list(data.get('waveforms', np.array([])).shape) if data.get('waveforms') is not None else [],
                'data_type': str(data.get('waveforms', np.array([])).dtype) if data.get('waveforms') is not None else 'float64',
                'file_size_bytes': os.path.getsize(filepath) if os.path.exists(filepath) else 0
            }
        }
        
        # Adicionar variáveis personalizadas se existirem
        custom_variables = {}
        for key, value in metadata.items():
            if key not in ['sensor_sn', 'test_type', 'material', 'location', 'pressure', 'pressure_unit',
                          'flow', 'flow_unit', 'distance', 'distance_unit', 'equipment_type',
                          'equipment_status', 'comments', 'timestamp', 'timestamp_iso', 'save_directory',
                          'calibration_file', 'ellipse_params', 'calibration_timestamp', 'calibration_file_used',
                          'calibration_timestamp_used', 'calibration_ellipse_params', 'setup_photos']:
                custom_variables[key] = value
        
        if custom_variables:
            toml_metadata['custom_variables'] = custom_variables
        
        # Adicionar informações de fotos se existirem
        if 'setup_photos' in metadata:
            toml_metadata['setup_info'] = {
                'setup_photos': metadata['setup_photos']
            }
        
        # Salvar metadados em TOML
        toml_filename = os.path.splitext(filepath)[0] + '.toml'
        with open(toml_filename, 'w', encoding='utf-8') as ftoml:
            toml.dump(toml_metadata, ftoml)
            
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
    def _ensure_ellipse_params_numeric(ellipse_params: Any) -> Dict[str, float]:
        """
        Garante que os parâmetros da elipse sejam números, convertendo strings se necessário

        Args:
            ellipse_params: Parâmetros da elipse em qualquer formato

        Returns:
            Dicionário com parâmetros numéricos
        """
        if not ellipse_params:
            return {}

        # Se já é um dicionário com valores numéricos, retornar como está
        if isinstance(ellipse_params, dict):
            try:
                # Tentar converter para float
                result = {}
                for key, value in ellipse_params.items():
                    if isinstance(value, str):
                        result[key] = float(value)
                    else:
                        result[key] = float(value)
                return result
            except (ValueError, TypeError):
                # Se não conseguir converter, tentar formato alternativo
                pass

        # Se é uma lista/tupla, converter para dicionário
        if isinstance(ellipse_params, (list, tuple)) and len(ellipse_params) >= 5:
            try:
                return {
                    'center_x': float(ellipse_params[0]),
                    'center_y': float(ellipse_params[1]),
                    'width': float(ellipse_params[2]),
                    'height': float(ellipse_params[3]),
                    'angle': float(ellipse_params[4])
                }
            except (ValueError, TypeError, IndexError):
                pass

        # Se é um array numpy, converter
        try:
            import numpy as np
            if isinstance(ellipse_params, np.ndarray) and ellipse_params.shape[0] >= 5:
                return {
                    'center_x': float(ellipse_params[0]),
                    'center_y': float(ellipse_params[1]),
                    'width': float(ellipse_params[2]),
                    'height': float(ellipse_params[3]),
                    'angle': float(ellipse_params[4])
                }
        except ImportError:
            pass

        # Fallback: retornar dicionário vazio
        return {}

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
            
        # Obter diretório de calibração das configurações
        directory = DataStore.load_config().get('calibration_directory')
        
        # Se não houver diretório, salvar no diretório de dados padrão.
        if not directory:
             directory = DataStore.load_config().get('save_directory')

        # Garantir que o diretório existe
        if directory:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
        else:
            filepath = filename
        
        # Garantir que os parâmetros da elipse sejam numéricos antes de salvar
        if 'ellipse_params' in data:
            data['ellipse_params'] = DataStore._ensure_ellipse_params_numeric(data['ellipse_params'])

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

            # Garantir que os parâmetros da elipse sejam numéricos
            if 'ellipse_params' in calibration_data:
                calibration_data['ellipse_params'] = DataStore._ensure_ellipse_params_numeric(calibration_data['ellipse_params'])

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
        
        # Obter diretório de calibração das configurações
        config = DataStore.load_config()
        calib_dir = config.get('calibration_directory')

        # Se não houver diretório configurado, não procurar por arquivos.
        if not calib_dir or not os.path.isdir(calib_dir):
            return []

        # Procurar arquivos de calibração com padrão calibracao_*.pkl no diretório
        search_path = os.path.join(calib_dir, "calibracao_*.pkl")
        calibration_files.extend(glob.glob(search_path))
        
        # Incluir o arquivo padrão de calibração se existir no diretório
        default_calib_path = os.path.join(calib_dir, DataStore.DEFAULT_CALIBRATION_FILE)
        if os.path.exists(default_calib_path):
            if default_calib_path not in calibration_files:
                calibration_files.append(default_calib_path)
        
        # Ordenar por data de modificação (mais recente primeiro)
        if calibration_files:
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
    def load_data_with_metadata(filepath: str) -> Dict[str, Any]:
        """
        Carrega dados brutos e metadados TOML
        
        Args:
            filepath: Caminho para o arquivo .pkl
            
        Returns:
            Dicionário com dados brutos e metadados
        """
        try:
            # Carregar dados brutos
            data = DataStore.load_data(filepath)
            
            # Carregar metadados TOML
            toml_filepath = os.path.splitext(filepath)[0] + '.toml'
            if os.path.exists(toml_filepath):
                with open(toml_filepath, 'r', encoding='utf-8') as f:
                    metadata = toml.load(f)
                data['metadata'] = metadata
            else:
                # Fallback para JSON se TOML não existir
                json_filepath = os.path.splitext(filepath)[0] + '.json'
                if os.path.exists(json_filepath):
                    with open(json_filepath, 'r', encoding='utf-8') as f:
                        data['metadata'] = json.load(f)
                else:
                    data['metadata'] = {}
                    
            return data
        except Exception as e:
            print(f"Erro ao carregar dados com metadados: {str(e)}")
            return {}
    
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