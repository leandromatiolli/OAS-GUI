#!/usr/bin/env python
"""
Script de teste para verificar se a configuração está funcionando
"""
import sys
import os

# Adicionar o diretório atual ao path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.data_store import DataStore

def test_config():
    """Testa se a configuração está funcionando corretamente"""
    print("Testando configuração do DataStore...")
    
    try:
        # Carregar configuração
        config = DataStore.load_config()
        print(f"Configuração carregada: {config}")
        
        # Verificar diretórios
        save_dir = config.get('save_directory')
        calib_dir = config.get('calibration_directory')
        
        print(f"Diretório de salvamento: {save_dir}")
        print(f"Diretório de calibração: {calib_dir}")
        
        # Verificar se os diretórios existem
        if save_dir and os.path.exists(save_dir):
            print(f"✓ Diretório de salvamento existe: {save_dir}")
        else:
            print(f"✗ Diretório de salvamento não existe: {save_dir}")
            
        if calib_dir and os.path.exists(calib_dir):
            print(f"✓ Diretório de calibração existe: {calib_dir}")
        else:
            print(f"✗ Diretório de calibração não existe: {calib_dir}")
        
        # Testar criação de um arquivo de teste
        test_data = {'test': 'data', 'metadata': {'test': True}}
        try:
            filename = DataStore.save_data(test_data, prefix="teste", directory=save_dir)
            print(f"✓ Arquivo de teste criado com sucesso: {filename}")
            
            # Limpar arquivo de teste
            if os.path.exists(filename):
                os.remove(filename)
                print("✓ Arquivo de teste removido")
                
        except Exception as e:
            print(f"✗ Erro ao criar arquivo de teste: {str(e)}")
            
        print("\nTeste concluído!")
        
    except Exception as e:
        print(f"✗ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config()
