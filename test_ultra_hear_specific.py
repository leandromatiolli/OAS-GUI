#!/usr/bin/env python
"""
Script de teste específico para o UltraHear com arquivo conhecido
"""
import sys
import os
import pickle
import numpy as np
from PyQt5.QtWidgets import QApplication

# Adicionar o diretório atual ao path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_with_specific_file():
    """Testa o UltraHear com um arquivo específico que sabemos que funciona"""
    
    # Arquivo de teste (um dos arquivos demodulados)
    test_file = "data/Dados para treinamento/vazamento_demodulado_20250827_155206_SN01_TipoVazamentodeAgua_MatEpoxy_Dist250.0cm_Press10.0b_Flux1.0L_EquipValvula_StatusAgE_SVaz_LocalMKFotonicaLabs.pkl"
    
    if not os.path.exists(test_file):
        print(f"❌ Arquivo de teste não encontrado: {test_file}")
        return False
    
    print(f"📁 Testando com arquivo: {test_file}")
    
    try:
        # Carregar dados
        with open(test_file, 'rb') as f:
            data = pickle.load(f)
        
        print(f"✅ Arquivo carregado com sucesso")
        print(f"   - Dados demodulados: {len(data['demodulated'])} pontos")
        print(f"   - Taxa de amostragem: {data['sample_frequency_effective']} Hz")
        print(f"   - Duração: {data['t'][-1] - data['t'][0]:.3f}s")
        
        # Testar controlador
        from app.controllers.ultra_hear_controller import UltraHearController
        controller = UltraHearController()
        
        # Simular carregamento
        controller.load_audio_file(test_file)
        
        if controller.current_data is not None:
            print("✅ Controlador carregou dados com sucesso")
        else:
            print("❌ Controlador falhou ao carregar dados")
            return False
        
        # Testar processamento básico
        params = {
            'file_path': test_file,
            'frequency_bands': [(20000, 100000)],  # 20-100 kHz
            'freq_min': 20000,
            'freq_max': 100000,
            'selection_mode': "Seleção Manual",
            'enable_transpose': True,
            'transpose_method': "Divisão de Frequência",
            'division_factor': 10,
            'target_freq': 1000,
            'maintain_speed': True,
            'amplitude_min': -60,
            'amplitude_max': -10,
            'normalization_type': "Peak Normalization",
            'gain_db': 0
        }
        
        print("🔄 Testando processamento...")
        controller.process_ultrasonic_audio(params)
        
        print("✅ Processamento concluído com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_panel_creation():
    """Testa a criação do painel UltraHear"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from app.views.panels.ultra_hear_panel import UltraHearPanel
        panel = UltraHearPanel()
        
        print("✅ Painel UltraHear criado com sucesso")
        
        # Testar carregamento de arquivo no painel
        test_file = "data/Dados para treinamento/vazamento_demodulado_20250827_155206_SN01_TipoVazamentodeAgua_MatEpoxy_Dist250.0cm_Press10.0b_Flux1.0L_EquipValvula_StatusAgE_SVaz_LocalMKFotonicaLabs.pkl"
        
        if os.path.exists(test_file):
            # Simular seleção de arquivo
            panel.current_file = test_file
            panel.file_label.setText(os.path.basename(test_file))
            
            # Carregar dados
            with open(test_file, 'rb') as f:
                data = pickle.load(f)
            
            # Simular carregamento de dados
            panel.on_data_loaded(data)
            
            print("✅ Painel carregou dados com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar painel: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("=== TESTE ESPECÍFICO DO ULTRA-HEAR ===\n")
    
    # Testar com arquivo específico
    if not test_with_specific_file():
        print("\n❌ Falha no teste com arquivo específico")
        return
    
    # Testar criação do painel
    if not test_panel_creation():
        print("\n❌ Falha no teste de criação do painel")
        return
    
    print("\n✅ Todos os testes específicos passaram!")
    print("\nO UltraHear está funcionando corretamente.")
    print("Para usar:")
    print("1. Execute: python main.py")
    print("2. Vá para a aba 'Ultra-Hear'")
    print("3. Clique em 'Selecionar Arquivo'")
    print("4. Escolha um arquivo com 'demodulado' no nome")
    print("5. Configure os filtros e processe o áudio")

if __name__ == "__main__":
    main()
