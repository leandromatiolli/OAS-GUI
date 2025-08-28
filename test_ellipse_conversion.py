#!/usr/bin/env python
"""
Script para testar a conversão de parâmetros da elipse
"""

import numpy as np
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.controllers.processing_controller import ProcessingController

def test_ellipse_conversion():
    """Testa a conversão de parâmetros da elipse"""

    # Criar controlador de processamento
    controller = ProcessingController()

    print("=== Testando Conversão de Parâmetros da Elipse ===\n")

    # Teste 1: Formato antigo (lista de strings)
    print("1. Testando formato antigo (lista de strings):")
    old_format = ['2934.4418572023', '3037.7325018142537', '0.98829424', '2907.622462196902', '0.48561026982728484']
    result1 = controller._convert_ellipse_params(old_format)
    print(f"   Entrada: {old_format}")
    print(f"   Resultado: {result1}")
    print(f"   Tipo: {type(result1)}")
    if result1 is not None:
        print(f"   Shape: {result1.shape}")
        print("   ✅ Conversão bem-sucedida\n")
    else:
        print("   ❌ Conversão falhou\n")

    # Teste 2: Novo formato (dicionário)
    print("2. Testando novo formato (dicionário):")
    new_format = {
        'center_x': 2934.4418572023,
        'center_y': 3037.7325018142537,
        'width': 0.98829424,
        'height': 2907.622462196902,
        'angle': 0.48561026982728484
    }
    result2 = controller._convert_ellipse_params(new_format)
    print(f"   Entrada: {new_format}")
    print(f"   Resultado: {result2}")
    print(f"   Tipo: {type(result2)}")
    if result2 is not None:
        print(f"   Shape: {result2.shape}")
        print("   ✅ Conversão bem-sucedida\n")
    else:
        print("   ❌ Conversão falhou\n")

    # Teste 3: Array numpy
    print("3. Testando array numpy:")
    numpy_format = np.array([2934.4418572023, 3037.7325018142537, 0.98829424, 2907.622462196902, 0.48561026982728484])
    result3 = controller._convert_ellipse_params(numpy_format)
    print(f"   Entrada: {numpy_format}")
    print(f"   Resultado: {result3}")
    print(f"   Tipo: {type(result3)}")
    if result3 is not None:
        print(f"   Shape: {result3.shape}")
        print("   ✅ Conversão bem-sucedida\n")
    else:
        print("   ❌ Conversão falhou\n")

    # Teste 4: Lista de floats
    print("4. Testando lista de floats:")
    float_list = [2934.4418572023, 3037.7325018142537, 0.98829424, 2907.622462196902, 0.48561026982728484]
    result4 = controller._convert_ellipse_params(float_list)
    print(f"   Entrada: {float_list}")
    print(f"   Resultado: {result4}")
    print(f"   Tipo: {type(result4)}")
    if result4 is not None:
        print(f"   Shape: {result4.shape}")
        print("   ✅ Conversão bem-sucedida\n")
    else:
        print("   ❌ Conversão falhou\n")

    print("=== Teste Concluído ===")

if __name__ == "__main__":
    test_ellipse_conversion()
