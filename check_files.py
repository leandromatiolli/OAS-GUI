#!/usr/bin/env python
"""
Script para verificar arquivos disponíveis e seus formatos
"""
import os
import pickle
import numpy as np

def check_file_content(file_path):
    """Verifica o conteúdo de um arquivo PKL"""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"\nArquivo: {file_path}")
        print(f"Tamanho: {os.path.getsize(file_path)} bytes")
        print(f"Chaves: {list(data.keys())}")
        
        # Verificar dados específicos
        if 'demodulated' in data:
            demod = data['demodulated']
            print(f"✓ Dados demodulados: {len(demod)} pontos")
            if len(demod) > 0:
                print(f"  - Min: {np.min(demod):.6f}")
                print(f"  - Max: {np.max(demod):.6f}")
                print(f"  - Média: {np.mean(demod):.6f}")
        else:
            print("✗ Dados demodulados não encontrados")
        
        if 'waveforms' in data:
            waveforms = data['waveforms']
            print(f"✓ Waveforms: shape {waveforms.shape}")
        
        if 't' in data:
            t = data['t']
            print(f"✓ Vetor tempo: {len(t)} pontos")
            if len(t) > 0:
                print(f"  - Duração: {t[-1] - t[0]:.3f}s")
        
        if 'sample_frequency_effective' in data:
            fs = data['sample_frequency_effective']
            print(f"✓ Taxa de amostragem efetiva: {fs} Hz")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao ler {file_path}: {e}")
        return False

def main():
    """Função principal"""
    print("=== VERIFICAÇÃO DE ARQUIVOS ===\n")
    
    # Listar todos os arquivos PKL
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
    
    # Verificar no diretório data/Dados para treinamento
    training_dir = "data/Dados para treinamento"
    if os.path.exists(training_dir):
        for file in os.listdir(training_dir):
            if file.endswith('.pkl'):
                pkl_files.append(os.path.join(training_dir, file))
    
    print(f"Arquivos PKL encontrados: {len(pkl_files)}")
    
    if not pkl_files:
        print("Nenhum arquivo PKL encontrado!")
        return
    
    # Verificar cada arquivo
    valid_files = []
    for file_path in pkl_files:
        if check_file_content(file_path):
            valid_files.append(file_path)
    
    print(f"\n=== RESUMO ===")
    print(f"Arquivos válidos: {len(valid_files)}/{len(pkl_files)}")
    
    # Encontrar arquivos com dados demodulados
    files_with_demod = []
    for file_path in valid_files:
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            if 'demodulated' in data:
                files_with_demod.append(file_path)
        except:
            pass
    
    print(f"Arquivos com dados demodulados: {len(files_with_demod)}")
    for file_path in files_with_demod:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()
