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
    calibrationListUpdated = pyqtSignal(list)  # Lista de calibrações disponíveis
    
    def __init__(self, parent=None):
        """
        Inicializa o controlador de arquivos
        
        Args:
            parent: Objeto pai
        """
        super().__init__(parent)
        self.current_calibration_file = None
        
    @pyqtSlot()
    def refresh_file_list(self):
        """Atualiza a lista de arquivos disponíveis"""
        try:
            files = DataStore.get_available_files()
            self.fileListUpdated.emit(files)
            
            # Atualizar também a lista de calibrações
            self.refresh_calibration_list()
            
        except Exception as e:
            self.fileError.emit(f"Erro ao listar arquivos: {str(e)}")
    
    @pyqtSlot()
    def refresh_calibration_list(self):
        """Atualiza a lista de arquivos de calibração disponíveis"""
        try:
            calibration_files = DataStore.get_available_calibration_files()
            self.calibrationListUpdated.emit(calibration_files)
            
            # Verificar status da calibração atual
            self.check_calibration_status()
        except Exception as e:
            self.fileError.emit(f"Erro ao listar calibrações: {str(e)}")
    
    def check_calibration_status(self):
        """Verifica se existe um arquivo de calibração válido e emite o sinal de status"""
        try:
            has_calibration = False
            if self.current_calibration_file:
                has_calibration = DataStore.has_valid_calibration(self.current_calibration_file)
            else:
                # Verificar se existe alguma calibração disponível
                calibration_files = DataStore.get_available_calibration_files()
                if calibration_files:
                    # Usar a primeira calibração disponível
                    self.current_calibration_file = calibration_files[0]
                    has_calibration = DataStore.has_valid_calibration(self.current_calibration_file)
            
            self.calibrationStatusChanged.emit(has_calibration, self.current_calibration_file)
        except Exception as e:
            self.fileError.emit(f"Erro ao verificar calibração: {str(e)}")
    
    @pyqtSlot(str)
    def set_current_calibration(self, calibration_file: Optional[str]):
        """
        Define o arquivo de calibração atual
        
        Args:
            calibration_file: Nome do arquivo de calibração ou None para atualizar a lista
        """
        if calibration_file is None:
            # None indica solicitação de atualização da lista
            self.refresh_calibration_list()
            return
            
        try:
            # Verificar se o arquivo existe e é uma calibração válida
            if not os.path.exists(calibration_file):
                self.fileError.emit(f"Arquivo de calibração não encontrado: {calibration_file}")
                return
                
            if not DataStore.has_valid_calibration(calibration_file):
                self.fileError.emit(f"Arquivo de calibração inválido: {calibration_file}")
                return
                
            # Definir como calibração atual
            self.current_calibration_file = calibration_file
            
            # Carregar a calibração
            calibration_data = self.load_calibration_data(calibration_file)
            
            # Atualizar status
            self.calibrationStatusChanged.emit(calibration_data is not None, calibration_file)
            
        except Exception as e:
            self.fileError.emit(f"Erro ao definir calibração atual: {str(e)}")
            
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
    
    def load_calibration_data(self, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados de calibração se disponíveis
        
        Args:
            filename: Nome do arquivo de calibração ou None para usar o atual
            
        Returns:
            Dicionário com os dados de calibração ou None se não existir
        """
        try:
            # Se não foi especificado um arquivo, usar o atual
            calibration_file = filename if filename else self.current_calibration_file
            
            # Se ainda não temos um arquivo de calibração definido, retornar None
            if not calibration_file:
                return None
                
            return DataStore.load_calibration_data(calibration_file)
        except Exception as e:
            self.fileError.emit(f"Erro ao carregar calibração: {str(e)}")
            return None
            
    def save_calibration_data(self, data: Dict[str, Any], filename: Optional[str] = None) -> bool:
        """
        Salva os dados de calibração
        
        Args:
            data: Dados de calibração a serem salvos
            filename: Nome do arquivo de calibração ou None para usar o padrão
            
        Returns:
            True se a operação for bem-sucedida, False caso contrário
        """
        try:
            saved_file = DataStore.save_calibration_data(data, filename)
            
            # Definir como calibração atual
            self.current_calibration_file = saved_file
            
            # Atualizar listas e status
            self.refresh_calibration_list()
            
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