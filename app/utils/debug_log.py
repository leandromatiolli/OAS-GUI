"""
Módulo para logging de debug
"""
import sys
import datetime
import os

# Cores para o terminal (Windows e outros)
RESET = '\033[0m'
DEBUG_COLOR = '\033[36m'  # Ciano
INFO_COLOR = '\033[32m'   # Verde
WARNING_COLOR = '\033[33m' # Amarelo
ERROR_COLOR = '\033[31m'  # Vermelho

# Verificar se estamos no Windows e ativar suporte a cores
if os.name == 'nt':
    os.system('color')

def log_debug(message):
    """
    Registra uma mensagem de debug tanto no terminal quanto na GUI
    
    Args:
        message: Mensagem de debug a ser registrada
    """
    # Adicionar timestamp
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted_message = f"[DEBUG] {timestamp} - {message}\n"
    terminal_message = f"{DEBUG_COLOR}[DEBUG] {timestamp} - {message}{RESET}\n"
    
    # Imprimir no terminal
    print(terminal_message, file=sys.stdout, end='')
    sys.stdout.flush()  # Forçar flush para garantir que apareça imediatamente

def log_info(message):
    """
    Registra uma mensagem informativa tanto no terminal quanto na GUI
    
    Args:
        message: Mensagem informativa a ser registrada
    """
    # Adicionar timestamp
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted_message = f"[INFO] {timestamp} - {message}\n"
    terminal_message = f"{INFO_COLOR}[INFO] {timestamp} - {message}{RESET}\n"
    
    # Imprimir no terminal
    print(terminal_message, file=sys.stdout, end='')
    sys.stdout.flush()  # Forçar flush para garantir que apareça imediatamente

def log_warning(message):
    """
    Registra uma mensagem de aviso tanto no terminal quanto na GUI
    
    Args:
        message: Mensagem de aviso a ser registrada
    """
    # Adicionar timestamp
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted_message = f"[AVISO] {timestamp} - {message}\n"
    terminal_message = f"{WARNING_COLOR}[AVISO] {timestamp} - {message}{RESET}\n"
    
    # Imprimir no terminal
    print(terminal_message, file=sys.stdout, end='')
    sys.stdout.flush()  # Forçar flush para garantir que apareça imediatamente

def log_error(message):
    """
    Registra uma mensagem de erro tanto no terminal quanto na GUI
    
    Args:
        message: Mensagem de erro a ser registrada
    """
    # Adicionar timestamp
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted_message = f"[ERRO] {timestamp} - {message}\n"
    terminal_message = f"{ERROR_COLOR}[ERRO] {timestamp} - {message}{RESET}\n"
    
    # Imprimir no terminal
    print(terminal_message, file=sys.stderr, end='')
    sys.stderr.flush()  # Forçar flush para garantir que apareça imediatamente
