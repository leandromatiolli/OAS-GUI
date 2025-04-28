"""
Módulo para gerenciamento de recursos da aplicação
"""
import os
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QFile, QTextStream, QSettings

def get_resource_path(path):
    """
    Obtém o caminho para um recurso
    
    Args:
        path: Caminho relativo para o recurso
        
    Returns:
        Caminho absoluto para o recurso
    """
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, path)

def load_stylesheet(filename):
    """
    Carrega um arquivo de estilo CSS
    
    Args:
        filename: Nome do arquivo CSS
        
    Returns:
        Conteúdo do arquivo CSS
    """
    path = get_resource_path(os.path.join("resources", "styles", filename))
    
    if not os.path.exists(path):
        print(f"Arquivo de estilo não encontrado: {path}")
        return ""
        
    file = QFile(path)
    if not file.open(QFile.ReadOnly | QFile.Text):
        print(f"Não foi possível abrir arquivo de estilo: {path}")
        return ""
        
    stream = QTextStream(file)
    stylesheet = stream.readAll()
    file.close()
    
    return stylesheet

def get_icon(name):
    """
    Obtém um ícone da pasta de recursos
    
    Args:
        name: Nome do arquivo de ícone (sem extensão)
        
    Returns:
        Objeto QIcon
    """
    path = get_resource_path(os.path.join("resources", "icons", f"{name}.svg"))
    
    if not os.path.exists(path):
        print(f"Ícone não encontrado: {path}")
        return QIcon()
        
    return QIcon(path)

def apply_stylesheet(app, filename=None):
    """
    Aplica estilo CSS ao aplicativo
    
    Args:
        app: Instância do QApplication
        filename: Nome do arquivo CSS, se nenhum for fornecido, 
                 usa a configuração salva ou o padrão
    """
    # Carregar configurações
    settings = QSettings("OAS", "OAS-GUI")
    
    # Se nenhum nome de arquivo for fornecido, usar o tema salvo ou o padrão
    if filename is None:
        theme = settings.value("theme", "main")
        filename = f"{theme}.css"
    else:
        # Atualizar tema nas configurações
        theme = filename.replace(".css", "")
        settings.setValue("theme", theme)
    
    # Carregar e aplicar o estilo
    stylesheet = load_stylesheet(filename)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        print(f"Estilo aplicado: {filename}")
    else:
        print(f"Não foi possível aplicar estilo: {filename}")
        
    return theme
    
def toggle_theme(app):
    """
    Alterna entre os temas claro e escuro
    
    Args:
        app: Instância do QApplication
        
    Returns:
        Nome do tema aplicado
    """
    # Carregar configurações
    settings = QSettings("OAS", "OAS-GUI")
    current_theme = settings.value("theme", "main")
    
    # Alternar tema
    if current_theme == "main":
        new_theme = "dark"
    else:
        new_theme = "main"
    
    # Aplicar novo tema
    theme = apply_stylesheet(app, f"{new_theme}.css")
    return theme 