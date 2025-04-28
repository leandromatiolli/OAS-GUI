"""
Módulo que encapsula a comunicação com o Red Pitaya
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any

# Importar bibliotecas para comunicação com RedPitaya
try:
    import redpitaya_scpi as scpi
    from OAS_Acquire_Continuous import bring_up_scpi_server, acquire_continuous_data, save_data
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("Módulos de aquisição não encontrados. Funcionalidade de aquisição será desabilitada.")

class RedPitayaClient:
    """Cliente para comunicação com o hardware Red Pitaya"""
    
    @staticmethod
    def is_available() -> bool:
        """Verifica se o hardware está disponível"""
        return HARDWARE_AVAILABLE
    
    @staticmethod
    def acquire_data(ip: str, 
                    duration: float, 
                    sample_rate: float, 
                    decimation: int, 
                    channels: List[int],
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Adquire dados do Red Pitaya
        
        Args:
            ip: Endereço IP do Red Pitaya
            duration: Duração da aquisição em segundos
            sample_rate: Taxa de amostragem em Hz
            decimation: Fator de decimação
            channels: Lista de canais para adquirir (1 ou 2)
            metadata: Metadados opcionais para incluir nos dados
            
        Returns:
            Dicionário com os dados adquiridos
        """
        if not HARDWARE_AVAILABLE:
            raise RuntimeError("Hardware não disponível")
            
        # Adquirir dados
        data = acquire_continuous_data(
            ip, 
            duration=duration,
            sample_rate=sample_rate,
            decimation=decimation,
            channels=channels
        )
        
        # Adicionar metadados
        if metadata:
            data['metadata'] = metadata
            
        return data
    
    @staticmethod
    def save_data(data: Dict[str, Any]) -> str:
        """
        Salva os dados adquiridos em um arquivo
        
        Args:
            data: Dicionário com os dados adquiridos
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        if not HARDWARE_AVAILABLE:
            raise RuntimeError("Hardware não disponível")
            
        return save_data(data) 