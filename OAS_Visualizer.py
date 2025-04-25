import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
import glob
from scipy import signal

def carregar_arquivo_pkl(caminho=None, tipo="demodulado"):
    """Carrega o arquivo de dados mais recente ou o especificado"""
    if caminho is None:
        # Encontrar o arquivo .pkl mais recente na pasta atual
        if tipo == "demodulado":
            arquivos = glob.glob("vazamento_demodulado_*.pkl")
        else:
            arquivos = glob.glob("vazamento_sensor_*.pkl")
            
        if not arquivos:
            print(f"Nenhum arquivo de dados '{tipo}' encontrado!")
            return None
        caminho = max(arquivos, key=os.path.getctime)
    
    print(f"Carregando arquivo: {caminho}")
    with open(caminho, 'rb') as f:
        dados = pickle.load(f)
    
    return dados

def decimar_sinal(dados, fator_decimacao=10):
    """Reduz a quantidade de pontos do sinal aplicando decimação"""
    if isinstance(dados, np.ndarray):
        # Caso seja um array diretamente
        return dados[::fator_decimacao]
    else:
        # Para dicionário de dados
        tempo = dados['t']
        decimado = {}
        decimado['t'] = tempo[::fator_decimacao]
        
        # Decimar formas de onda
        if 'waveforms' in dados:
            decimado['waveforms'] = dados['waveforms'][:, ::fator_decimacao]
        
        # Decimar dados demodulados
        if 'demodulated' in dados:
            decimado['demodulated'] = dados['demodulated'][::fator_decimacao]
            
        return decimado

def plotar_dados_brutos(dados, fator_decimacao=10):
    """Plota os sinais brutos adquiridos com decimação"""
    # Decimar os dados para visualização
    tempo = dados['t'][::fator_decimacao]
    formas_onda = dados['waveforms'][:, ::fator_decimacao]
    
    # Informações sobre os dados
    n_canais = formas_onda.shape[0]
    taxa_amostragem = dados['sample_frequency_effective'] / 1e6  # MHz
    duracao = dados['acquisition_time']
    
    # Plotar os sinais brutos
    plt.figure(figsize=(12, 8))
    cores = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
    
    for i in range(n_canais):
        plt.subplot(n_canais, 1, i+1)
        plt.plot(tempo, formas_onda[i], color=cores[i % len(cores)])
        plt.title(f'Canal {dados["channels"][i]} - Sinal Bruto')
        plt.ylabel('Amplitude')
        
        if i == n_canais-1:  # Apenas no último gráfico
            plt.xlabel('Tempo (s)')
        
    plt.suptitle(f'Dados Brutos do Sensor - Taxa: {taxa_amostragem:.2f} MHz, Duração: {duracao}s\n'
                f'Arquivo: {dados.get("timestamp", "Desconhecido")}')
    plt.tight_layout()

def plotar_dados_demodulados(dados, fator_decimacao=10):
    """Plota o sinal demodulado"""
    if 'demodulated' not in dados:
        print("Este arquivo não contém dados demodulados!")
        return
    
    # Decimar os dados para visualização
    tempo = dados['t'][::fator_decimacao]
    sinal_demodulado = dados['demodulated'][::fator_decimacao]
    
    # Plotar o sinal demodulado
    plt.figure(figsize=(12, 6))
    plt.plot(tempo, sinal_demodulado)
    plt.title('Sinal Demodulado')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Fase (rad)')
    plt.grid(True)
    
    # Adicionar informações sobre o arquivo
    plt.suptitle(f'Dados Demodulados - Duração: {dados["acquisition_time"]}s\n'
                f'Arquivo: {dados.get("timestamp", "Desconhecido")}')
    plt.tight_layout()

def plotar_espectro(dados, fator_decimacao=10, janela='hann'):
    """Plota o espectro de frequências do sinal demodulado"""
    if 'demodulated' not in dados:
        print("Este arquivo não contém dados demodulados!")
        return
    
    # Obter sinal demodulado
    sinal = dados['demodulated'][::fator_decimacao]
    fs = dados['sample_frequency_effective'] / fator_decimacao
    
    # Calcular o espectro
    f, Pxx = signal.welch(sinal, fs, window=janela, nperseg=min(8192, len(sinal)//10), 
                         scaling='spectrum')
    
    # Converter para dB
    Pxx_db = 10 * np.log10(Pxx)
    
    # Plotar o espectro
    plt.figure(figsize=(12, 6))
    plt.semilogy(f, Pxx)
    plt.title('Espectro de Potência do Sinal Demodulado')
    plt.xlabel('Frequência (Hz)')
    plt.ylabel('Densidade Espectral de Potência')
    plt.grid(True)
    
    # Plotar também em dB
    plt.figure(figsize=(12, 6))
    plt.plot(f, Pxx_db)
    plt.title('Espectro de Potência do Sinal Demodulado (dB)')
    plt.xlabel('Frequência (Hz)')
    plt.ylabel('Densidade Espectral de Potência (dB)')
    plt.grid(True)

def plotar_lissajous(dados, fator_decimacao=100):
    """Plota a figura de Lissajous (CH1 vs CH2) para visualizar a elipse"""
    # Decimar os dados para visualização
    waveforms = dados['waveforms'][:, ::fator_decimacao]
    
    # Se temos os parâmetros da elipse, plotar também a elipse ajustada
    if 'ellipse_params' in dados:
        # Plotar dados e elipse ajustada
        plt.figure(figsize=(8, 8))
        plt.scatter(waveforms[0], waveforms[1], s=1, alpha=0.3, label='Pontos medidos')
        
        # Gerar pontos para a elipse ajustada
        t = np.linspace(0, 2*np.pi, 200)
        fitted_ellipse = mkf.rescale(np.sin(t), np.cos(t), dados['ellipse_params'], invert=True)
        plt.plot(fitted_ellipse[0], fitted_ellipse[1], 'r-', linewidth=2, label='Elipse ajustada')
        
        plt.title('Figura de Lissajous com Ajuste de Elipse')
    else:
        # Apenas plotar os dados brutos
        plt.figure(figsize=(8, 8))
        plt.scatter(waveforms[0], waveforms[1], s=1, alpha=0.5)
        plt.title('Figura de Lissajous (CH1 vs CH2)')
    
    plt.xlabel('Canal 1')
    plt.ylabel('Canal 2')
    plt.axis('equal')
    plt.grid(True)
    if 'ellipse_params' in dados:
        plt.legend()

def main():
    print("Visualizador de Dados OAS")
    print("------------------------")
    
    # Perguntar qual tipo de arquivo carregar
    print("\nTipo de arquivo a carregar:")
    print("1 - Dados demodulados (default)")
    print("2 - Dados brutos")
    tipo = input("Escolha (1/2): ")
    
    # Carregar o arquivo apropriado
    if tipo == "2":
        dados = carregar_arquivo_pkl(tipo="bruto")
        if dados is None:
            return
        
        # Mostrar informações sobre os dados carregados
        print("\nInformações sobre os dados brutos:")
        print(f"Timestamp: {dados.get('timestamp', 'Desconhecido')}")
        print(f"Canais: {dados['channels']}")
        print(f"Forma de onda: {dados['waveforms'].shape}")
        print(f"Taxa de amostragem: {dados['sample_frequency_effective']/1e6:.2f} MHz")
        print(f"Duração: {dados['acquisition_time']} segundos")
        
        # Calcular fator de decimação adequado
        tamanho_sinal = dados['waveforms'].shape[1]
        fator_decimacao = max(1, tamanho_sinal // 10000)  # Limitar a ~10000 pontos
        print(f"Fator de decimação usado: {fator_decimacao} (1:{fator_decimacao})")
        
        # Plotar os dados brutos
        plotar_dados_brutos(dados, fator_decimacao)
        
        # Plotar a figura de Lissajous
        try:
            import mkf
            plotar_lissajous(dados, fator_decimacao * 10)  # Usar mais decimação para o gráfico de dispersão
        except ImportError:
            print("Módulo 'mkf' não encontrado. Não é possível plotar a figura de Lissajous com ajuste de elipse.")
        
    else:
        # Dados demodulados
        dados = carregar_arquivo_pkl(tipo="demodulado")
        if dados is None:
            return
        
        # Mostrar informações sobre os dados carregados
        print("\nInformações sobre os dados demodulados:")
        print(f"Timestamp: {dados.get('timestamp', 'Desconhecido')}")
        print(f"Canais: {dados['channels']}")
        print(f"Forma de onda: {dados['waveforms'].shape}")
        print(f"Taxa de amostragem: {dados['sample_frequency_effective']/1e6:.2f} MHz")
        print(f"Duração: {dados['acquisition_time']} segundos")
        
        # Calcular fator de decimação adequado
        tamanho_sinal = len(dados['demodulated'])
        fator_decimacao = max(1, tamanho_sinal // 10000)  # Limitar a ~10000 pontos
        print(f"Fator de decimação usado: {fator_decimacao} (1:{fator_decimacao})")
        
        # Perguntar quais gráficos mostrar
        print("\nEscolha os gráficos para visualizar:")
        print("1 - Sinal demodulado")
        print("2 - Dados brutos")
        print("3 - Figura de Lissajous")
        print("4 - Espectro de frequências")
        print("5 - Todos os gráficos")
        opcao = input("Escolha (1-5): ")
        
        if opcao == "1" or opcao == "5":
            plotar_dados_demodulados(dados, fator_decimacao)
        
        if opcao == "2" or opcao == "5":
            plotar_dados_brutos(dados, fator_decimacao)
        
        if opcao == "3" or opcao == "5":
            try:
                import mkf
                plotar_lissajous(dados, fator_decimacao * 10)
            except ImportError:
                print("Módulo 'mkf' não encontrado. Não é possível plotar a figura de Lissajous com ajuste de elipse.")
        
        if opcao == "4" or opcao == "5":
            plotar_espectro(dados, fator_decimacao)
    
    # Manter os gráficos abertos
    plt.show()

if __name__ == "__main__":
    main() 