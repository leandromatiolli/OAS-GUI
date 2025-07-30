"""
Módulo com componentes de visualização gráfica
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from typing import Dict, List, Tuple, Optional, Union, Any
from PyQt5.QtCore import Qt

class MplCanvas(FigureCanvas):
    """Canvas para plotagem de gráficos usando Matplotlib"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Inicializa o canvas
        
        Args:
            parent: Widget pai
            width: Largura da figura em polegadas
            height: Altura da figura em polegadas
            dpi: Resolução da figura
        """
        self.fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        
    def clear(self):
        """Limpa o gráfico"""
        self.axes.clear()
        self.draw()

    def draw(self):
        """Override draw to always apply tight_layout before drawing"""
        try:
            self.fig.tight_layout()
        except Exception:
            # In case tight_layout fails, continue without it
            pass
        super().draw()
        
    def draw_inset(self, rect=[0.65, 0.65, 0.3, 0.3]):
        """
        Cria e retorna um eixo interno para visualização secundária
        
        Args:
            rect: Retângulo para posicionamento [left, bottom, width, height] em coordenadas normalizadas
            
        Returns:
            Eixo interno criado
        """
        inset_ax = self.axes.inset_axes(rect)
        return inset_ax
        
    def plot_timeseries(self, t, data, channels=None, max_points=10000, 
                     xlabel='Tempo (s)', ylabel='Amplitude', title='Série Temporal'):
        """
        Plota uma série temporal
        
        Args:
            t: Vetor de tempo
            data: Array de dados [canais, amostras]
            channels: Lista com identificadores dos canais
            max_points: Número máximo de pontos a plotar
            xlabel: Rótulo do eixo x
            ylabel: Rótulo do eixo y
            title: Título do gráfico
        """
        print(f"plot_timeseries: t={type(t)}, data={type(data)}, channels={channels}")
        print(f"t shape={len(t)}, data shape={data.shape}")
        
        self.axes.clear()
        
        # Verificar se os comprimentos coincidem
        if len(t) != data.shape[1]:
            # Truncar para o tamanho menor
            min_len = min(len(t), data.shape[1])
            print(f"Ajustando tamanhos: t={len(t)} -> {min_len}, data={data.shape[1]} -> {min_len}")
            t = t[:min_len]
            data = data[:, :min_len]
        
        # Limitar número de pontos para plotagem
        if len(t) > max_points:
            step = len(t) // max_points
            t_plot = t[::step]
            data_plot = data[:, ::step]
            print(f"Reduzindo pontos para plotagem: {len(t)} -> {len(t_plot)}")
        else:
            t_plot = t
            data_plot = data
        
        # Se não temos lista de canais, criar uma
        if channels is None:
            channels = [i+1 for i in range(data.shape[0])]
        
        # Plotar cada canal
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        for i, channel in enumerate(channels):
            if i < len(data_plot):
                print(f"Plotando canal {channel}: {len(t_plot)} pontos")
                try:
                    self.axes.plot(t_plot, data_plot[i], color=colors[i % len(colors)], 
                               label=f'Canal {channel}')
                except Exception as e:
                    print(f"Erro ao plotar canal {channel}: {e}")
        
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.set_title(title)
        self.axes.legend()
        self.axes.grid(True)
        
        try:
            self.draw()
            print("Canvas atualizado com sucesso")
        except Exception as e:
            print(f"Erro ao atualizar canvas: {e}")
        
    def plot_scatter(self, x, y, color='b', alpha=0.3, size=1, 
                   xlabel='Canal 1', ylabel='Canal 2', title='Gráfico de Dispersão'):
        """
        Plota um gráfico de dispersão
        
        Args:
            x: Dados do eixo x
            y: Dados do eixo y
            color: Cor dos pontos
            alpha: Transparência dos pontos
            size: Tamanho dos pontos
            xlabel: Rótulo do eixo x
            ylabel: Rótulo do eixo y
            title: Título do gráfico
        """
        self.axes.clear()
        
        self.axes.scatter(x, y, s=size, alpha=alpha, color=color)
        
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.axis('equal')
        self.axes.grid(True)
        
        self.draw()
        
    def plot_spectrum(self, freq_axis, magnitudes, peaks=None, log_scale=False,
                    xlabel='Frequência (Hz)', ylabel='Amplitude (dB)', 
                    title='Espectro de Frequência'):
        """
        Plota o espectro de frequência de um sinal
        
        Args:
            freq_axis: Vetor de frequências
            magnitudes: Magnitudes do espectro em dB
            peaks: Lista opcional de tuplas (freq, mag) com picos a destacar
            log_scale: Se deve usar escala logarítmica no eixo x
            xlabel: Rótulo do eixo x
            ylabel: Rótulo do eixo y
            title: Título do gráfico
        """
        self.axes.clear()
        
        # Plotar espectro
        if log_scale:
            self.axes.semilogx(freq_axis, magnitudes)
        else:
            self.axes.plot(freq_axis, magnitudes)
        
        # Destacar picos se fornecidos
        if peaks:
            for freq, mag in peaks:
                # Adicionar linha vertical no pico
                self.axes.axvline(x=freq, color='r', linestyle='--', alpha=0.7)
                
                # Adicionar rótulo do pico com frequência em kHz para melhor legibilidade
                self.axes.text(freq, mag+3, f"{freq/1000:.1f} kHz", 
                           fontsize=8, ha='center', va='bottom',
                           bbox=dict(facecolor='white', alpha=0.7, pad=1))
                
                # Marcar o ponto do pico
                self.axes.plot(freq, mag, 'ro', markersize=5)
        
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.set_title(title)
        self.axes.grid(True, which='both', linestyle='--', alpha=0.7)
        
        self.draw()
        
    def add_text(self, text, x=0.5, y=0.5, fontsize=12, ha='center', va='center', **kwargs):
        """
        Adiciona texto ao gráfico
        
        Args:
            text: Texto a ser adicionado
            x, y: Posição normalizada (0-1) ou coordenadas de dados
            fontsize: Tamanho da fonte
            ha: Alinhamento horizontal ('left', 'center', 'right')
            va: Alinhamento vertical ('top', 'center', 'bottom')
            **kwargs: Argumentos adicionais para plt.text()
        """
        self.axes.text(x, y, text, fontsize=fontsize, ha=ha, va=va, **kwargs)
        self.draw()
        
    def plot_ellipse(self, fitted_params=None, x_data=None, y_data=None, 
                   plot_params=False, y_inc=1000/2**13):
        """
        Plota a elipse ajustada sobre os dados
        
        Args:
            fitted_params: Parâmetros da elipse ajustada (p, q, r, s, alpha)
            x_data, y_data: Dados para plotar (opcional se apenas deseja plotar a elipse)
            plot_params: Se deve mostrar os parâmetros da elipse
            y_inc: Fator de escala para os valores (para converter para mV)
        """
        if x_data is not None and y_data is not None:
            self.plot_scatter(x_data, y_data, title='Figura de Lissajous')
        
        if fitted_params is not None:
            import mkf  # Importação local
            
            # Gerar pontos para a elipse
            t = np.linspace(0, 2*np.pi, 200)
            fitted_ellipse = mkf.rescale(np.sin(t), np.cos(t), fitted_params, invert=True)
            
            # Plotar a elipse
            self.axes.plot(fitted_ellipse[0], fitted_ellipse[1], 'r-', linewidth=2)
            
            # Mostrar parâmetros da elipse
            if plot_params:
                p, q, r, s, alpha = fitted_params
                plt_text = (f"DC CH1: {p*y_inc:.0f} mV\n"
                            f"DC CH2: {q*y_inc:.0f} mV\n"
                            f"Raio: {s*y_inc:.0f} mV\n"
                            f"Excent: {r:.2f}\n"
                            f"Ângulo: {alpha*360/(2*np.pi):.1f}°")
                self.axes.text(0.05, 0.95, plt_text, transform=self.axes.transAxes, 
                          verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.5))
            
            self.draw()
            
class NavigationToolbarCustom(NavigationToolbar):
    """Barra de ferramentas de navegação personalizada"""
    
    # Lista de ícones a ocultar
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in 
               ('Home', 'Pan', 'Zoom', 'Save')] 
    
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
        self.coordinate_label = None
        self.setOrientation(Qt.Vertical)
        self.setFixedWidth(50)
    
    def set_coordinate_label(self, label):
        """Set the QLabel to display coordinates"""
        self.coordinate_label = label
    
    def set_message(self, s):
        """Override to display coordinates in custom label"""
        if self.coordinate_label is not None:
            self.coordinate_label.setText(f"{s}")