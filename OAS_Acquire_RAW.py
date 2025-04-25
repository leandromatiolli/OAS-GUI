import os
import time
import numpy as np
import redpitaya_scpi as scpi
import pickle
from datetime import datetime

def bring_up_scpi_server(host="rp-f0b916.local", stop=False):
    """Inicializa o servidor SCPI no RedPitaya"""
    import requests
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

def setup_acquisition(ip, decimation=1, avg="OFF", waveform_len=16384, delay=0, ch=[1,2]):
    """Configura o RedPitaya para aquisição de dados"""
    n_ch = len(ch)
    dig = scpi.scpi(ip, timeout=1) 
    dig.delay = delay
    dig.waveform_len = waveform_len
    dig.tx_txt('ACQ:RST')
    start_address = int(dig.txrx_txt('ACQ:AXI:START?'))
    size = int(dig.txrx_txt('ACQ:AXI:SIZE?'))
    print(f'Memória reservada para aquisição: {size/1E6:.2f} MB')
    start_address2 = round(start_address + size/2) if n_ch == 2 else start_address
    dig.tx_txt(f"ACQ:AXI:DEC {decimation}")
    dig.tx_txt(f'ACQ:AVG {avg}')
    dig.tx_txt('ACQ:AXI:DATA:UNITS RAW')
    dig.tx_txt('ACQ:DATA:FORMAT BIN')
    dig.tx_txt(f"ACQ:AXI:SOUR1:Trig:Dly {waveform_len + 1 - delay}")
    dig.tx_txt(f"ACQ:AXI:SOUR2:Trig:Dly {waveform_len + 1 - delay}")
    if 1 in ch:
        dig.tx_txt(f"ACQ:AXI:SOUR1:SET:Buffer {start_address},{size/n_ch}")
        dig.tx_txt('ACQ:AXI:SOUR1:ENable ON')
    if 2 in ch:
        dig.tx_txt(f"ACQ:AXI:SOUR2:SET:Buffer {start_address2},{size/n_ch}")
        dig.tx_txt('ACQ:AXI:SOUR2:ENable ON')    
    return dig

def acquire_data(ip_address, duration=5, sample_rate=125e6, decimation=1, channels=[1,2]):
    """Adquire dados do sensor por um período específico"""
    # Calcular tamanho da forma de onda necessário para duração especificada
    effective_sample_rate = sample_rate / decimation
    waveform_len = int(effective_sample_rate * duration)
    
    # Limitar ao tamanho máximo se for muito grande
    max_waveform_len = 16384  # Tamanho típico máximo para RedPitaya
    chunk_size = 2**16  # Tamanho do bloco para leitura de dados
    
    if waveform_len > max_waveform_len:
        num_acquisitions = int(np.ceil(waveform_len / max_waveform_len))
        waveform_len = max_waveform_len
    else:
        num_acquisitions = 1
    
    print(f"Iniciando aquisição de {duration}s a {effective_sample_rate/1e6:.2f} MHz")
    print(f"Serão feitas {num_acquisitions} aquisições sequenciais")
    
    # Inicializar o servidor SCPI
    bring_up_scpi_server(ip_address)
    
    # Configurar o RedPitaya
    dig = setup_acquisition(ip_address, decimation=decimation, 
                           waveform_len=waveform_len, ch=channels)
    
    # Preparar array para armazenar os dados
    n_ch = len(channels)
    all_waveforms = np.zeros((n_ch, waveform_len * num_acquisitions), dtype=np.int16)
    
    # Adquirir dados
    for acq in range(num_acquisitions):
        print(f"Aquisição {acq+1}/{num_acquisitions}")
        
        # Criar matriz para armazenar formas de onda
        waveforms = np.zeros((n_ch, waveform_len), dtype=np.int16)
        
        # Iniciar aquisição
        dig.tx_txt('ACQ:START')
        dig.tx_txt('ACQ:TRIG NOW')
        
        # Aguardar aquisição
        j = 0
        while True:
            j += 1
            dig.tx_txt("ACQ:TRIG:STAT?")
            if dig.rx_txt() == 'TD':
                print("Disparado", end="\r")
                break
            time.sleep(.01) 
            print(f"Aguardando disparo:{j}", end="\r")
        
        # Aguardar o preenchimento do buffer ADC
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
        
        # Obter os dados
        # Obter posição do ponteiro de escrita na localização do trigger
        pos_ch = {}
        for c in channels:
            pos_ch[c] = int(dig.txrx_txt(f'ACQ:AXI:SOUR{c}:Trig:Pos?'))
        
        # Calcular número de chunks e resto
        N = waveform_len // chunk_size
        remainder = waveform_len % chunk_size
        
        # Obter dados em chunks
        for i in range(N):
            print(f"{i+1}/{N}", end='\r')
            for c_idx, c in enumerate(channels):
                dig.tx_txt(f"ACQ:AXI:SOUR{c}:DATA:Start:N? {pos_ch[c]+i*chunk_size - dig.delay},{chunk_size}")
                buf = dig.rx_arb()
                waveforms[c_idx][i*chunk_size:(i+1)*chunk_size] = np.frombuffer(buf, dtype=np.dtype('>i2'))
        
        # Obter o resto dos dados, se houver
        if remainder:
            for c_idx, c in enumerate(channels):
                dig.tx_txt(f"ACQ:AXI:SOUR{c}:DATA:Start:N? {pos_ch[c]+N*chunk_size - dig.delay},{remainder}")
                buf = dig.rx_arb()
                waveforms[c_idx][N*chunk_size:N*chunk_size+remainder] = np.frombuffer(buf, dtype=np.dtype('>i2'))
        
        # Armazenar os dados da aquisição atual
        start_idx = acq * waveform_len
        end_idx = start_idx + waveform_len
        all_waveforms[:, start_idx:end_idx] = waveforms
    
    # Encerrar conexão com RedPitaya
    print('Liberando recursos')
    dig.tx_txt('ACQ:STOP')
    dig.tx_txt('ACQ:AXI:SOUR1:ENable OFF')
    dig.tx_txt('ACQ:AXI:SOUR2:ENable OFF')
    dig.close()
    
    # Criar objeto de dados
    data = {
        'waveforms': all_waveforms,
        'sample_frequency': sample_rate,
        'decimation': decimation,
        'sample_frequency_effective': sample_rate / decimation,
        'acquisition_time': duration,
        'channels': channels,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        't': np.arange(all_waveforms.shape[1])/(sample_rate/decimation)
    }
    
    return data

def save_data(data, filename=None):
    """Salva os dados em um arquivo pickle"""
    if filename is None:
        # Criar nome de arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vazamento_sensor_{timestamp}.pkl"
    
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"Dados salvos em {filename}")
    return filename

def main():
    # Configurações
    IP_ADDRESS = "rp-f0b916.local"  # Substitua pelo IP ou hostname do seu RedPitaya
    DURATION = 2  # Duração da aquisição em segundos
    SAMPLE_RATE = 125e6  # Taxa de amostragem do RedPitaya (125 MHz)
    DECIMATION = 64  # Fator de decimação para reduzir a taxa de amostragem
    CHANNELS = [1, 2]  # Canais a serem adquiridos
    
    # Adquirir dados
    print("Iniciando aquisição de dados do sensor de vazamento...")
    data = acquire_data(IP_ADDRESS, duration=DURATION, 
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
