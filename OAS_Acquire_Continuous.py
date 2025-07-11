import os
import time
import numpy as np
import redpitaya_scpi as scpi
import pickle
from datetime import datetime
import requests

def bring_up_scpi_server(host="rp-f0b916.local", stop=False):
    """Inicializa o servidor SCPI no RedPitaya"""
    r = requests.get(f'http://{host}/get_scpi_status', auth=('user', 'pass'))
    assert r.status_code == 200, f"Erro ao conectar com {host}, código: {r.status_code}"
    command, state1, state2 = ('stop', 'active', 'inactive') if stop else ('start', 'inactive', 'active')
    if r.text.strip('\n') == state1:
        r = requests.get(f'http://{host}/{command}_scpi_manager', auth=('user', 'pass'))
        assert r.status_code == 200, f"Falha ao iniciar gerenciador SCPI {host}, código: {r.status_code}"
        r = requests.get(f'http://{host}/get_scpi_status', auth=('user', 'pass'))
        assert r.status_code == 200, f"Erro ao conectar com {host}, código: {r.status_code}"
    if r.text.strip('\n') == state2:
        print(f"Servidor SCPI {state2}")

def setup_continuous_acquisition(ip, decimation=1, avg="OFF", waveform_len=16384, ch=[1,2]):
    """Configura o RedPitaya para aquisição contínua de dados"""
    n_ch = len(ch)
    dig = scpi.scpi(ip, timeout=1) 
    dig.waveform_len = waveform_len
    
    # Resetar a aquisição
    dig.tx_txt('ACQ:RST')
    
    # Verificar memória disponível
    start_address = int(dig.txrx_txt('ACQ:AXI:START?'))
    size = int(dig.txrx_txt('ACQ:AXI:SIZE?'))
    print(f'Memória reservada para aquisição: {size/1E6:.2f} MB')
    
    # Dividir o buffer entre os canais
    start_address2 = round(start_address + size/2) if n_ch == 2 else start_address
    
    # Configurar aquisição
    dig.tx_txt(f"ACQ:AXI:DEC {decimation}")
    dig.tx_txt(f'ACQ:AVG {avg}')
    dig.tx_txt('ACQ:AXI:DATA:UNITS RAW')
    dig.tx_txt('ACQ:DATA:FORMAT BIN')
    
    # Configurar buffers por canal
    if 1 in ch:
        dig.tx_txt(f"ACQ:AXI:SOUR1:SET:Buffer {start_address},{size/n_ch}")
        dig.tx_txt('ACQ:AXI:SOUR1:ENable ON')
    if 2 in ch:
        dig.tx_txt(f"ACQ:AXI:SOUR2:SET:Buffer {start_address2},{size/n_ch}")
        dig.tx_txt('ACQ:AXI:SOUR2:ENable ON')    
    
    return dig

def wait_acquisition(dig):
    """Aguarda a aquisição ser concluída"""
    # Aguardar o disparo
    j = 0
    while True:
        j += 1
        dig.tx_txt("ACQ:TRIG:STAT?")
        if dig.rx_txt() == 'TD':
            print("Disparado", end="\r")
            break
        time.sleep(.01) 
        print(f"Aguardando disparo:{j}", end="\r")
    
    # Aguardar o preenchimento do buffer DMA
    j = 0
    while True:
        j += 1
        dig.tx_txt('ACQ:AXI:SOUR1:TRIG:FILL?')
        if dig.rx_txt() == '1':
            print(f'Buffer DMA cheio', end="\r")
            break
        time.sleep(.01)
        print(f"Aguardando aquisição:{j}", end="\r")
        if j > 20/.01:
            print("Verificar conexão WiFi ou rede", end="\r")

def get_data_continuous(dig, waveforms, ch=[1,2], chunk_size=2**16):
    """Coleta dados do buffer em chunks continuamente"""
    waveform_len = waveforms.shape[1]
    
    # Obter posição do trigger
    pos_ch = {}
    for c in ch:
        pos_ch[c] = int(dig.txrx_txt(f'ACQ:AXI:SOUR{c}:Trig:Pos?'))
    
    # Calcular número de chunks e resto
    N = waveform_len // chunk_size
    remainder = waveform_len % chunk_size
    
    # Coletar dados em chunks
    for i in range(N):
        print(f"Obtendo chunk {i+1}/{N}", end='\r')
        for c_idx, c in enumerate(ch):
            dig.tx_txt(f"ACQ:AXI:SOUR{c}:DATA:Start:N? {pos_ch[c]+i*chunk_size},{chunk_size}")
            buf = dig.rx_arb()
            waveforms[c_idx][i*chunk_size:(i+1)*chunk_size] = np.frombuffer(buf, dtype=np.dtype('>i2'))
    
    # Coletar o resto dos dados
    if remainder:
        for c_idx, c in enumerate(ch):
            dig.tx_txt(f"ACQ:AXI:SOUR{c}:DATA:Start:N? {pos_ch[c]+N*chunk_size},{remainder}")
            buf = dig.rx_arb()
            waveforms[c_idx][N*chunk_size:N*chunk_size+remainder] = np.frombuffer(buf, dtype=np.dtype('>i2'))

def tear_down(dig):
    """Encerra a conexão com o RedPitaya"""
    print('Liberando recursos')
    dig.tx_txt('ACQ:STOP')
    dig.tx_txt('ACQ:AXI:SOUR1:ENable OFF')
    dig.tx_txt('ACQ:AXI:SOUR2:ENable OFF')
    dig.close()

def acquire_continuous_data(ip_address, duration=5, sample_rate=125e6, decimation=1, channels=[1,2]):
    """Adquire dados continuamente por um período específico"""
    # Calcular tamanho da forma de onda baseado na duração e taxa de amostragem
    effective_sample_rate = sample_rate / decimation
    # Calcular tamanho total (ou próximo possível) baseado na memória do RedPitaya
    waveform_len = int(effective_sample_rate * duration)
    
    # Ajustar para potência de 2 (mais eficiente)
    power_of_2 = int(np.log2(waveform_len))
    waveform_len = 2 ** min(power_of_2, 25)  # Limite de 2^25 (33.5M pontos)
    
    # Recalcular a duração real
    actual_duration = waveform_len / effective_sample_rate
    
    print(f"Iniciando aquisição contínua:")
    print(f"- Duração solicitada: {duration}s")
    print(f"- Duração real: {actual_duration:.2f}s")
    print(f"- Tamanho da forma de onda: {waveform_len:_} pontos")
    print(f"- Taxa de amostragem efetiva: {effective_sample_rate/1e6:.2f} MHz")
    print(f"- Fator de decimação: {decimation}")
    
    # Configurar a aquisição
    dig = setup_continuous_acquisition(ip_address, decimation=decimation, 
                                     waveform_len=waveform_len, ch=channels)
    
    # Criar um buffer para armazenar os dados
    n_ch = len(channels)
    waveforms = np.zeros((n_ch, waveform_len), dtype=np.int16)
    
    # Iniciar a aquisição
    print("Iniciando aquisição...")
    dig.tx_txt('ACQ:START')
    dig.tx_txt('ACQ:TRIG NOW')
    
    # Aguardar a conclusão da aquisição
    wait_acquisition(dig)
    
    # Obter os dados
    print("Coleta de dados em andamento...")
    get_data_continuous(dig, waveforms, ch=channels)
    
    # Encerrar a conexão
    tear_down(dig)
    
    # Criar objeto de dados
    data = {
        'waveforms': waveforms,
        'sample_frequency': sample_rate,
        'decimation': decimation,
        'sample_frequency_effective': effective_sample_rate,
        'acquisition_time': actual_duration,
        'channels': channels,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        't': np.arange(waveform_len)/effective_sample_rate
    }
    
    return data

def save_data(data):
    """Salva os dados da aquisição em um arquivo pickle"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extrair metadados se disponíveis
    metadata_str = ""
    if 'metadata' in data and isinstance(data['metadata'], dict):
        metadata = data['metadata']
        # Adicionar informações relevantes ao nome do arquivo
        if metadata.get('test_type'):
            metadata_str += f" {metadata['test_type']}"
        if metadata.get('sensor_sn'):
            metadata_str += f" SN{metadata['sensor_sn']}"
        if metadata.get('flow') and float(metadata.get('flow', 0)) > 0:
            metadata_str += f" Fluxo-{float(metadata['flow']):.1f}L-min"
        if metadata.get('pressure') and float(metadata.get('pressure', 0)) > 0:
            metadata_str += f" Pressão{float(metadata['pressure']):.1f}Bar"
        if metadata.get('material'):
            metadata_str += f" Material-{metadata['material']}"
        if metadata.get('distance') and float(metadata.get('distance', 0)) > 0:
            metadata_str += f" Distância-{float(metadata['distance']):.1f}cm"
    
    # Criar nome do arquivo com timestamp e metadados
    filename = f"vazamento_continuo_{timestamp}{metadata_str}.pkl"
    
    # Limpar caracteres inválidos no nome do arquivo
    filename = filename.replace(" ", "_").replace("/", "-").replace(":", "-")
    
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"Dados salvos em {filename}")
    return filename

def main():
    # Configurações
    IP_ADDRESS = "rp-f0b916.local"  # Substitua pelo IP ou hostname do seu RedPitaya
    DURATION = 5  # Duração da aquisição em segundos (máximo de ~0.5s para 125MHz sem decimação)
    SAMPLE_RATE = 125e6  # Taxa de amostragem do RedPitaya (125 MHz)
    DECIMATION = 64  # Fator de decimação para reduzir a taxa de amostragem
    CHANNELS = [1, 2]  # Canais a serem adquiridos
    
    # Adquirir dados de forma contínua
    print("Iniciando aquisição contínua de dados do sensor de vazamento...")
    data = acquire_continuous_data(IP_ADDRESS, duration=DURATION, 
                                 sample_rate=SAMPLE_RATE, 
                                 decimation=DECIMATION,
                                 channels=CHANNELS)
    
    # Salvar dados
    filename = save_data(data)
    
    print(f"Aquisição concluída! Os dados foram salvos em {filename}")
    print(f"Forma de onda adquirida: {data['waveforms'].shape}")
    print(f"Taxa de amostragem efetiva: {data['sample_frequency_effective']/1e6:.2f} MHz")
    print(f"Duração total: {data['t'][-1]:.2f} segundos")

if __name__ == "__main__":
    main() 