#!/usr/bin/env python
"""
Script de teste para verificar a qualidade do áudio UltraHear
"""
import sys
import os
import pickle
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

# Adicionar o diretório atual ao path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_audio_quality():
    """Testa a qualidade do áudio processado"""
    print("🔊 Testando qualidade do áudio UltraHear...")
    
    # Arquivo de teste
    test_file = "data/Dados para treinamento/vazamento_demodulado_20250827_155206_SN01_TipoVazamentodeAgua_MatEpoxy_Dist250.0cm_Press10.0b_Flux1.0L_EquipValvula_StatusAgE_SVaz_LocalMKFotonicaLabs.pkl"
    
    if not os.path.exists(test_file):
        print(f"❌ Arquivo de teste não encontrado: {test_file}")
        return False
    
    try:
        # Carregar dados
        with open(test_file, 'rb') as f:
            data = pickle.load(f)
        
        print(f"✓ Dados carregados: {len(data['demodulated'])} pontos")
        
        # Importar controlador
        from app.controllers.ultra_hear_controller import UltraHearController
        
        # Criar controlador
        controller = UltraHearController()
        
        # Parâmetros de teste
        params = {
            'file_path': test_file,
            'frequency_bands': [(20000, 40000)],  # 20-40 kHz
            'freq_min': 20000,
            'freq_max': 40000,
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
        
        # Processar áudio
        print("🔄 Processando áudio...")
        controller.process_ultrasonic_audio(params)
        
        # Verificar se o arquivo foi criado
        import glob
        wav_files = glob.glob("ultra_hear_*.wav")
        if wav_files:
            latest_file = max(wav_files, key=os.path.getctime)
            print(f"✓ Arquivo de áudio criado: {latest_file}")
            
            # Analisar qualidade do áudio
            fs, audio_data = wavfile.read(latest_file)
            print(f"✓ Áudio carregado: {len(audio_data)} samples, {fs} Hz")
            
            # Verificar clipping
            clipped_samples = np.sum(np.abs(audio_data) >= 32767)
            clipping_percentage = (clipped_samples / len(audio_data)) * 100
            print(f"📊 Clipping: {clipped_samples} samples ({clipping_percentage:.2f}%)")
            
            # Verificar RMS
            rms = np.sqrt(np.mean((audio_data / 32767.0) ** 2))
            rms_db = 20 * np.log10(rms + 1e-12)
            print(f"📊 RMS: {rms:.4f} ({rms_db:.1f} dB)")
            
            # Verificar dinâmica
            peak = np.max(np.abs(audio_data)) / 32767.0
            peak_db = 20 * np.log10(peak + 1e-12)
            dynamic_range = peak_db - rms_db
            print(f"📊 Pico: {peak:.4f} ({peak_db:.1f} dB)")
            print(f"📊 Faixa Dinâmica: {dynamic_range:.1f} dB")
            
            # Verificar se há valores NaN ou Inf
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                print("❌ Áudio contém valores NaN ou Inf!")
                return False
            
            # Verificar se o áudio não está silencioso
            if rms < 1e-6:
                print("❌ Áudio muito silencioso!")
                return False
            
            # Verificar se não há clipping excessivo
            if clipping_percentage > 5:
                print("⚠️ Clipping excessivo detectado!")
                return False
            
            print("✅ Qualidade do áudio OK!")
            return True
            
        else:
            print("❌ Nenhum arquivo de áudio foi criado")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def analyze_audio_file(filename):
    """Analisa um arquivo de áudio em detalhes"""
    try:
        fs, audio_data = wavfile.read(filename)
        
        print(f"\n📊 Análise detalhada: {filename}")
        print(f"   Taxa de amostragem: {fs} Hz")
        print(f"   Duração: {len(audio_data)/fs:.2f} segundos")
        print(f"   Amostras: {len(audio_data)}")
        
        # Converter para float
        audio_float = audio_data.astype(np.float32) / 32767.0
        
        # Estatísticas
        print(f"   Mínimo: {np.min(audio_float):.6f}")
        print(f"   Máximo: {np.max(audio_float):.6f}")
        print(f"   Média: {np.mean(audio_float):.6f}")
        print(f"   RMS: {np.sqrt(np.mean(audio_float**2)):.6f}")
        
        # Clipping
        clipped = np.sum(np.abs(audio_float) >= 1.0)
        print(f"   Clipping: {clipped} samples ({clipped/len(audio_float)*100:.2f}%)")
        
        # Zeros
        zeros = np.sum(audio_float == 0)
        print(f"   Zeros: {zeros} samples ({zeros/len(audio_float)*100:.2f}%)")
        
        # FFT para verificar espectro
        fft_data = np.fft.fft(audio_float)
        freqs = np.fft.fftfreq(len(audio_float), 1/fs)
        
        # Encontrar picos no espectro
        magnitude = np.abs(fft_data[:len(fft_data)//2])
        peak_freqs = freqs[:len(freqs)//2][magnitude > np.max(magnitude) * 0.1]
        
        print(f"   Frequências principais: {peak_freqs[:5]} Hz")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎵 Teste de Qualidade do Áudio UltraHear")
    print("=" * 50)
    
    # Testar processamento
    success = test_audio_quality()
    
    if success:
        # Analisar arquivos criados
        import glob
        wav_files = glob.glob("ultra_hear_*.wav")
        if wav_files:
            latest_file = max(wav_files, key=os.path.getctime)
            analyze_audio_file(latest_file)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou!")
