"""
Módulo controlador para gerenciamento de arquivos
"""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import os

from app.models.data_store import DataStore
from typing import Dict, List, Any, Optional

class FileController(QObject):
    """Controlador para gerenciamento de arquivos de dados"""
    
    # Sinais
    fileListUpdated = pyqtSignal(list)  # Lista de arquivos disponíveis
    fileLoaded = pyqtSignal(dict)  # Dados carregados
    fileError = pyqtSignal(str)  # Erro ao carregar arquivo
    calibrationStatusChanged = pyqtSignal(bool, str)  # Status da calibração (disponível, nome do arquivo)
    
    def __init__(self, parent=None):
        """
        Inicializa o controlador de arquivos
        
        Args:
            parent: Objeto pai
        """
        super().__init__(parent)
        
    @pyqtSlot()
    def refresh_file_list(self):
        """Atualiza a lista de arquivos disponíveis"""
        try:
            files = DataStore.get_available_files()
            self.fileListUpdated.emit(files)
            
            # Verificar status da calibração
            self.check_calibration_status()
            
        except Exception as e:
            self.fileError.emit(f"Erro ao listar arquivos: {str(e)}")
    
    def check_calibration_status(self):
        """Verifica se existe um arquivo de calibração válido e emite o sinal de status"""
        try:
            has_calibration = DataStore.has_valid_calibration()
            calibration_file = DataStore.CALIBRATION_FILE if has_calibration else None
            self.calibrationStatusChanged.emit(has_calibration, calibration_file)
        except Exception as e:
            self.fileError.emit(f"Erro ao verificar calibração: {str(e)}")
            
    @pyqtSlot(str)
    def load_file(self, filename: str):
        """
        Carrega um arquivo
        
        Args:
            filename: Nome do arquivo a ser carregado
        """
        try:
            if not os.path.exists(filename):
                self.fileError.emit(f"Arquivo não encontrado: {filename}")
                return
                
            data = DataStore.load_data(filename)
            self.fileLoaded.emit(data)
            
        except Exception as e:
            self.fileError.emit(f"Erro ao carregar arquivo: {str(e)}")
    
    def load_calibration_data(self) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados de calibração se disponíveis
        
        Returns:
            Dicionário com os dados de calibração ou None se não existir
        """
        try:
            return DataStore.load_calibration_data()
        except Exception as e:
            self.fileError.emit(f"Erro ao carregar calibração: {str(e)}")
            return None
            
    def save_calibration_data(self, data: Dict[str, Any]) -> bool:
        """
        Salva os dados de calibração
        
        Args:
            data: Dados de calibração a serem salvos
            
        Returns:
            True se a operação for bem-sucedida, False caso contrário
        """
        try:
            filename = DataStore.save_calibration_data(data)
            self.check_calibration_status()  # Atualizar status após salvar
            return True
        except Exception as e:
            self.fileError.emit(f"Erro ao salvar calibração: {str(e)}")
            return False
            
    def save_demodulated_data(self, data: Dict[str, Any]) -> str:
        """
        Salva dados demodulados
        
        Args:
            data: Dados demodulados a serem salvos
            
        Returns:
            Nome do arquivo onde os dados foram salvos
        """
        try:
            filename = DataStore.save_demodulated_data(data)
            self.refresh_file_list()  # Atualizar lista após salvar
            return filename
        except Exception as e:
            self.fileError.emit(f"Erro ao salvar dados: {str(e)}")
            raise 