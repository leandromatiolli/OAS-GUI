import pickle
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

def carregar_arquivo_pkl(caminho=None):
    """Carrega o arquivo de dados mais recente ou o especificado"""
    if caminho is None:
        # Encontrar o arquivo .pkl mais recente na pasta atual
        arquivos = glob.glob("vazamento_sensor_*.pkl")
        if not arquivos:
            print("Nenhum arquivo de dados encontrado!")
            return None
        caminho = max(arquivos, key=os.path.getctime)
    
    print(f"Carregando arquivo: {caminho}")
    with open(caminho, 'rb') as f:
        dados = pickle.load(f)
    
    return dados

def decimar_sinal(dados, fator_decimacao=10):
    """Reduz a quantidade de pontos do sinal aplicando decimação"""
    formas_onda = dados['waveforms']
    tempo = dados['t']
    
    # Aplicar decimação
    formas_onda_decimadas = formas_onda[:, ::fator_decimacao]
    tempo_decimado = tempo[::fator_decimacao]
    
    return tempo_decimado, formas_onda_decimadas

def plotar_dados(dados, fator_decimacao=10):
    """Plota os sinais adquiridos com decimação"""
    # Decimar os dados
    tempo, formas_onda = decimar_sinal(dados, fator_decimacao)
    
    # Informações sobre os dados
    n_canais = formas_onda.shape[0]
    taxa_amostragem = dados['sample_frequency_effective'] / 1e6  # MHz
    duracao = dados['acquisition_time']
    
    # Plotar os sinais
    plt.figure(figsize=(12, 8))
    cores = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
    
    for i in range(n_canais):
        plt.subplot(n_canais, 1, i+1)
        plt.plot(tempo, formas_onda[i], color=cores[i % len(cores)])
        plt.title(f'Canal {dados["channels"][i]}')
        plt.ylabel('Amplitude')
        
        if i == n_canais-1:  # Apenas no último gráfico
            plt.xlabel('Tempo (s)')
        
    plt.suptitle(f'Dados do Sensor - Taxa: {taxa_amostragem:.2f} MHz, Duração: {duracao}s\n'
                f'Arquivo: {dados.get("timestamp", "Desconhecido")}')
    plt.tight_layout()
    
    # Mostrar o gráfico
    plt.show()

def main():
    # Carregar o arquivo de dados
    dados = carregar_arquivo_pkl()
    if dados is None:
        return
    
    # Mostrar informações sobre os dados
    print("\nInformações sobre os dados:")
    print(f"Timestamp: {dados.get('timestamp', 'Desconhecido')}")
    print(f"Canais: {dados['channels']}")
    print(f"Forma de onda: {dados['waveforms'].shape}")
    print(f"Taxa de amostragem: {dados['sample_frequency_effective']/1e6:.2f} MHz")
    print(f"Duração: {dados['acquisition_time']} segundos")
    
    # Calcular fator de decimação adequado
    tamanho_sinal = dados['waveforms'].shape[1]
    fator_decimacao = max(1, tamanho_sinal // 10000)  # Limitar a ~10000 pontos
    print(f"Fator de decimação usado: {fator_decimacao} (1:{fator_decimacao})")
    
    # Plotar os dados
    plotar_dados(dados, fator_decimacao)

if __name__ == "__main__":
    main()