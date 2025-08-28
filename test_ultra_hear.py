#!/usr/bin/env python
"""
Script de teste para verificar as funcionalidades do UltraHear
"""
import sys
import os
import traceback

# Adicionar o diretório atual ao path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa as importações necessárias"""
    print("Testando importações...")
    
    try:
        import numpy as np
        print("✓ NumPy importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar NumPy: {e}")
        return False
    
    try:
        from scipy import signal
        print("✓ SciPy signal importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar SciPy signal: {e}")
        return False
    
    try:
        from scipy.fft import fft, fftfreq, ifft
        print("✓ SciPy FFT importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar SciPy FFT: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print("✓ Matplotlib importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar Matplotlib: {e}")
        return False
    
    try:
        from matplotlib.widgets import SpanSelector
        print("✓ Matplotlib widgets importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar Matplotlib widgets: {e}")
        return False
    
    try:
        from PyQt5.QtWidgets import QApplication
        print("✓ PyQt5 importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar PyQt5: {e}")
        return False
    
    return True

def test_ultra_hear_controller():
    """Testa o controlador UltraHear"""
    print("\nTestando controlador UltraHear...")
    
    try:
        from app.controllers.ultra_hear_controller import UltraHearController
        controller = UltraHearController()
        print("✓ Controlador UltraHear criado com sucesso")
        return controller
    except Exception as e:
        print(f"✗ Erro ao criar controlador: {e}")
        traceback.print_exc()
        return None

def test_ultra_hear_panel():
    """Testa o painel UltraHear"""
    print("\nTestando painel UltraHear...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from app.views.panels.ultra_hear_panel import UltraHearPanel
        panel = UltraHearPanel()
        print("✓ Painel UltraHear criado com sucesso")
        return panel
    except Exception as e:
        print(f"✗ Erro ao criar painel: {e}")
        traceback.print_exc()
        return None

def test_file_loading():
    """Testa o carregamento de arquivos"""
    print("\nTestando carregamento de arquivos...")
    
    # Verificar se existem arquivos PKL
    pkl_files = []
    
    # Verificar no diretório temp
    temp_dir = "temp"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            if file.endswith('.pkl'):
                pkl_files.append(os.path.join(temp_dir, file))
    
    # Verificar no diretório data/Calibracoes
    calib_dir = "data/Calibracoes"
    if os.path.exists(calib_dir):
        for file in os.listdir(calib_dir):
            if file.endswith('.pkl'):
                pkl_files.append(os.path.join(calib_dir, file))
    
    print(f"Arquivos PKL encontrados: {len(pkl_files)}")
    for file in pkl_files:
        print(f"  - {file}")
    
    if not pkl_files:
        print("✗ Nenhum arquivo PKL encontrado para teste")
        return False
    
    # Testar carregamento do primeiro arquivo
    try:
        import pickle
        with open(pkl_files[0], 'rb') as f:
            data = pickle.load(f)
        
        print(f"✓ Arquivo carregado: {pkl_files[0]}")
        print(f"  - Chaves: {list(data.keys())}")
        
        if 'demodulated' in data:
            print(f"  - Dados demodulados: {len(data['demodulated'])} pontos")
        else:
            print("  - ⚠️ Dados demodulados não encontrados")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao carregar arquivo: {e}")
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("=== TESTE DO ULTRA-HEAR ===\n")
    
    # Testar importações
    if not test_imports():
        print("\n❌ Falha nos testes de importação")
        return
    
    # Testar controlador
    controller = test_ultra_hear_controller()
    if controller is None:
        print("\n❌ Falha no teste do controlador")
        return
    
    # Testar painel
    panel = test_ultra_hear_panel()
    if panel is None:
        print("\n❌ Falha no teste do painel")
        return
    
    # Testar carregamento de arquivos
    if not test_file_loading():
        print("\n❌ Falha no teste de carregamento de arquivos")
        return
    
    print("\n✅ Todos os testes básicos passaram!")
    print("\nPara testar a interface completa, execute: python main.py")

if __name__ == "__main__":
    main()
