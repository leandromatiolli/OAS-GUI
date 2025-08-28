#!/usr/bin/env python
"""
Script para testar se os novos arquivos salvos têm os parâmetros da elipse no formato correto
"""

import os
import toml
import pickle
import numpy as np
from app.models.data_store import DataStore

def test_new_file_format():
    """Testa se os novos arquivos têm os parâmetros da elipse salvos corretamente"""

    # Criar dados de teste simulados
    test_data = {
        'waveforms': np.random.randn(2, 1000).astype(np.float64),
        't': np.linspace(0, 1, 1000),
        'sample_frequency': 125000000.0,
        'decimation': 64,
        'channels': [1, 2],
        'metadata': {
            'sensor_sn': 'TEST01',
            'test_type': 'teste_unitario',
            'material': 'Teste',
            'location': 'Lab Teste',
            'pressure': 1.0,
            'pressure_unit': 'bar',
            'flow': 0.5,
            'flow_unit': 'L/min',
            'distance': 100.0,
            'distance_unit': 'cm',
            'equipment_type': 'teste',
            'equipment_status': ['teste'],
            'comments': 'Arquivo de teste para verificar formato',
            'ellipse_params': {
                'center_x': 1500.0,
                'center_y': 1600.0,
                'width': 100.0,
                'height': 80.0,
                'angle': 0.1
            }
        }
    }

    # Salvar arquivo de teste
    test_filename = DataStore.save_data(test_data, prefix="teste_format")

    print(f"Arquivo de teste salvo: {test_filename}")

    # Verificar se o arquivo TOML foi criado
    toml_file = test_filename.replace('.pkl', '.toml')
    if os.path.exists(toml_file):
        print(f"Arquivo TOML encontrado: {toml_file}")

        # Carregar e verificar conteúdo TOML
        with open(toml_file, 'r', encoding='utf-8') as f:
            metadata = toml.load(f)

        print("\nConteúdo da seção calibration_info:")
        if 'calibration_info' in metadata:
            calib_info = metadata['calibration_info']
            print(f"  ellipse_params: {calib_info.get('ellipse_params', 'NÃO ENCONTRADO')}")

            # Verificar se não há duplicatas
            if 'calibration_ellipse_params' in calib_info:
                print("  ❌ ERRO: Ainda há campo duplicado 'calibration_ellipse_params'")
            else:
                print("  ✅ OK: Não há campo duplicado")

        # Verificar se conseguimos carregar os dados com metadados
        print("\nTestando carregamento com metadados...")
        loaded_data = DataStore.load_data_with_metadata(test_filename)

        if 'metadata' in loaded_data:
            print("✅ Metadados carregados com sucesso")
            if 'calibration_info' in loaded_data['metadata']:
                ellipse_params = loaded_data['metadata']['calibration_info'].get('ellipse_params', {})
                if ellipse_params:
                    print(f"✅ Parâmetros da elipse encontrados: {ellipse_params}")
                else:
                    print("❌ Parâmetros da elipse não encontrados")
        else:
            print("❌ Metadados não carregados")

    else:
        print(f"❌ Arquivo TOML não encontrado: {toml_file}")

    # Limpar arquivos de teste
    if os.path.exists(test_filename):
        os.remove(test_filename)
    if os.path.exists(toml_file):
        os.remove(toml_file)

    print("\nTeste concluído!")

if __name__ == "__main__":
    test_new_file_format()
