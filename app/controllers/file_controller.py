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
        except Exception as e:
            self.fileError.emit(f"Erro ao listar arquivos: {str(e)}")
            
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