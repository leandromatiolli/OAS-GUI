#!/usr/bin/env python
"""
Script para iniciar a aplicação OAS-GUI
"""
import sys
import os
import platform

def ensure_directories():
    """Cria os diretórios necessários caso não existam"""
    dirs = ['data', 'export', 'app/models', 'app/views', 'app/controllers']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import PyQt5
        import numpy
        import matplotlib
        import scipy
        return True
    except ImportError as e:
        print(f"Erro ao importar dependência: {e}")
        print("Instale as dependências com: pip install -r requirements.txt")
        return False

def main():
    """Função principal"""
    # Verificar se estamos no diretório certo
    if not os.path.exists('main.py'):
        print("ERRO: Execute este script do diretório raiz do projeto")
        return 1
        
    # Garantir que diretórios existam
    ensure_directories()
    
    # Verificar dependências
    if not check_dependencies():
        return 1
    
    # Executar a aplicação
    print("Iniciando OAS-GUI...")
    if platform.system() == 'Windows':
        os.system('python main.py')
    else:
        os.system('python3 main.py')
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 