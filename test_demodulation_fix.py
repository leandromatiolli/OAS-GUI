#!/usr/bin/env python
"""
Script para testar se a correção do erro de demodulação funcionou
"""

import os
import sys
import numpy as np

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.controllers.processing_controller import ProcessingController

def test_demodulation_fix():
    """Testa se o erro de verificação booleana foi corrigido"""

    print("=== Testando Correção do Erro de Demodulação ===\n")

    # Criar controlador de processamento
    controller = ProcessingController()

    # Criar dados de teste simulados
    test_data = {
        'waveforms': np.random.randn(2, 10000).astype(np.float64),
        't': np.linspace(0, 1, 10000),
        'sample_frequency': 125000000.0,
        'decimation': 64,
        'channels': [1, 2],
        'metadata': {
            'calibration_info': {
                'ellipse_params': ['2934.4418572023', '3037.7325018142537', '0.98829424', '2907.622462196902', '0.48561026982728484']
            }
        }
    }

    print("1. Testando carregamento de dados com parâmetros da elipse no formato antigo (lista)...")

    # Configurar dados
    controller.set_data(test_data)

    print("   ✅ Dados configurados sem erro")

    print("2. Testando verificação de parâmetros da elipse...")

    # Tentar acessar os parâmetros (isso deve funcionar agora)
    metadata = test_data.get('metadata', {})
    if isinstance(metadata, dict) and 'calibration_info' in metadata:
        ellipse_params_raw = metadata['calibration_info'].get('ellipse_params', {})
        print(f"   Parâmetros brutos: {ellipse_params_raw}")

        # Esta verificação não deve mais causar erro
        if ellipse_params_raw is not None and ellipse_params_raw != {} and ellipse_params_raw != []:
            print("   ✅ Verificação booleana funcionou sem erro")
            converted = controller._convert_ellipse_params(ellipse_params_raw)
            print(f"   Parâmetros convertidos: {converted}")
            if converted is not None:
                print("   ✅ Conversão bem-sucedida")
            else:
                print("   ❌ Conversão falhou")
        else:
            print("   ❌ Verificação booleana falhou")

    print("\n3. Testando demodulação completa...")

    try:
        # Tentar demodular (isso deve funcionar agora)
        controller.demodulate_data()
        print("   ✅ Demodulação iniciada sem erro")
    except Exception as e:
        print(f"   ❌ Erro na demodulação: {e}")

    print("\n=== Teste Concluído ===")

if __name__ == "__main__":
    test_demodulation_fix()
