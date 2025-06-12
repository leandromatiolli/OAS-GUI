import sys
import os
import pickle
from typing import Optional

import numpy as np
from scipy import signal
from scipy.io import wavfile

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QVBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt


class DemodulatedToWavConverter(QMainWindow):
    """Janela principal para converter arquivos demodulados em WAV."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversor Demodulado → WAV")
        self.setMinimumSize(480, 200)

        # Estado
        self.pkl_path: Optional[str] = None

        # Widgets
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.label_file = QLabel("Nenhum arquivo selecionado", self)
        self.label_file.setWordWrap(True)
        layout.addWidget(self.label_file)

        btn_select = QPushButton("Selecionar arquivo .pkl", self)
        btn_select.clicked.connect(self.on_select_file)
        layout.addWidget(btn_select)

        self.btn_convert = QPushButton("Converter para WAV", self)
        self.btn_convert.setEnabled(False)
        self.btn_convert.clicked.connect(self.on_convert)
        layout.addWidget(self.btn_convert)

        layout.addStretch()

    # ---------------------------------------------------------------------
    # Callbacks
    # ---------------------------------------------------------------------
    def on_select_file(self):
        """Abre diálogo para selecionar arquivo .pkl demodulado."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo demodulado (.pkl)",
            os.getcwd(),
            "Arquivos Pickle (*.pkl)"
        )
        if not path:
            return
        self.pkl_path = path
        self.label_file.setText(f"Arquivo selecionado: {os.path.basename(path)}")
        self.btn_convert.setEnabled(True)

    def on_convert(self):
        """Processa a conversão pkl → wav."""
        if not self.pkl_path:
            return
        try:
            wav_path = convert_demodulated_pkl_to_wav(self.pkl_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao converter arquivo:\n{e}")
            return
        QMessageBox.information(self, "Sucesso", f"Arquivo WAV salvo em:\n{wav_path}")


# -------------------------------------------------------------------------
# Função de conversão principal
# -------------------------------------------------------------------------

def convert_demodulated_pkl_to_wav(
    pkl_file: str,
    target_rate: int = 44100,
    hp_cutoff: float = 20.0,
    lp_cutoff: float = 20_000.0,
) -> str:
    """Converte arquivo .pkl com sinal demodulado para WAV.

    Parâmetros
    ----------
    pkl_file : str
        Caminho do arquivo pickle contendo dicionário com chave 'demodulated'.
    target_rate : int, opcional
        Taxa de amostragem desejada para o WAV. Padrão = 44100 Hz.
    hp_cutoff : float, opcional
        Frequência de corte (Hz) do filtro passa-alta para remover componentes
        de baixa frequência (< hp_cutoff). Padrão = 20 Hz.
    lp_cutoff : float, opcional
        Frequência de corte (Hz) do filtro passa-baixa para remover componentes
        de alta frequência (> lp_cutoff). Padrão = 20 kHz.

    Retorna
    -------
    str
        Caminho do arquivo WAV criado.
    """
    # -----------------------------------------------------------------    
    # Carregar dados do pickle
    # -----------------------------------------------------------------
    with open(pkl_file, "rb") as fh:
        data = pickle.load(fh)

    if "demodulated" not in data:
        raise ValueError("Arquivo pkl não contém chave 'demodulated'.")

    signal_in = np.asarray(data["demodulated"], dtype=np.float64)

    # -----------------------------------------------------------------    
    # Determinar taxa de amostragem original
    # -----------------------------------------------------------------
    if "sample_frequency_effective" in data:
        fs_orig = float(data["sample_frequency_effective"])
    elif "sample_frequency" in data and "decimation" in data:
        fs_orig = float(data["sample_frequency"]) / float(data["decimation"])
    else:
        raise ValueError("Não foi possível determinar a taxa de amostragem original do arquivo.")

    # -----------------------------------------------------------------    
    # Filtro passa-alta (20 Hz) – Butterworth de 4ª ordem
    # -----------------------------------------------------------------
    sos = signal.butter(N=4, Wn=hp_cutoff, btype="highpass", fs=fs_orig, output="sos")
    signal_hp = signal.sosfiltfilt(sos, signal_in)

    # -----------------------------------------------------------------    
    # Filtro passa-baixa (20 kHz) – Butterworth de 4ª ordem
    # -----------------------------------------------------------------
    sos = signal.butter(N=4, Wn=lp_cutoff, btype="lowpass", fs=fs_orig, output="sos")
    signal_lp = signal.sosfiltfilt(sos, signal_hp)

    # -----------------------------------------------------------------    
    # Reamostragem para target_rate
    #   Usa resample_poly para melhor qualidade.
    # -----------------------------------------------------------------
    # Calcular fatores inteiros up/down para resample_poly
    import math
    fs_orig_int = int(round(fs_orig))  # garantir inteiro
    if fs_orig_int == 0:
        raise ValueError("Taxa de amostragem original inválida (0 Hz).")
    g = math.gcd(target_rate, fs_orig_int)
    up = target_rate // g
    down = fs_orig_int // g
    # Se ainda estiverem muito grandes, limitar valores mantendo a razão
    max_factor = 1000  # limite arbitrário para evitar coeficientes enormes
    while down > max_factor:
        up = (up + 1) // 2
        down = (down + 1) // 2
    signal_resampled = signal.resample_poly(signal_lp, up, down)

    # -----------------------------------------------------------------    
    # Normalização para [-1, 1]
    # -----------------------------------------------------------------
    max_abs = np.max(np.abs(signal_resampled))
    if max_abs == 0:
        norm_signal = signal_resampled
    else:
        norm_signal = signal_resampled / max_abs

    # Converter para int16
    pcm16 = np.int16(norm_signal * 32767)

    # -----------------------------------------------------------------    
    # Salvar arquivo WAV na pasta raiz do projeto
    # -----------------------------------------------------------------
    root_dir = os.path.dirname(os.path.abspath(__file__))
    base_name = os.path.splitext(os.path.basename(pkl_file))[0]
    wav_name = f"{base_name}_audio.wav"
    wav_path = os.path.join(root_dir, wav_name)

    wavfile.write(wav_path, target_rate, pcm16)

    return wav_path


# -------------------------------------------------------------------------
# Execução direta
# -------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DemodulatedToWavConverter()
    win.show()
    sys.exit(app.exec_()) 