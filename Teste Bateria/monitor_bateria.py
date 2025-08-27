import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from datetime import datetime

# --- Constantes ---
RESISTOR_SHUNT = 2.9  # Ohms
RESISTOR_TOTAL = 24.0  # Ohms (3 + 20)
TENSAO_REFERENCIA_ARDUINO = 5.0  # Volts
RESOLUCAO_ADC = 1023.0
INTERVALO_MEDIDA = 10.0  # Segundos entre cada medida do Arduino

class MonitorBateriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Bateria Li-Ion")
        self.root.geometry("800x600")

        self.porta_serial = None
        self.thread_leitura = None
        self.monitorando = False
        self.dados = []

        # Configura handler para erros não tratados
        import sys
        sys.excepthook = self.handle_exception

        # --- Estrutura da GUI ---
        self.criar_widgets()

    def criar_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de Controles (Esquerda)
        controles_frame = ttk.LabelFrame(main_frame, text="Controles e Dados", padding="10")
        controles_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # --- Controles ---
        ttk.Label(controles_frame, text="Porta Serial:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.porta_serial_entry = ttk.Entry(controles_frame, width=15)
        self.porta_serial_entry.insert(0, "COM6") # Porta onde o Arduino está conectado
        self.porta_serial_entry.grid(row=0, column=1, padx=5, pady=5)

        self.btn_iniciar = ttk.Button(controles_frame, text="Iniciar Monitoramento", command=self.iniciar_monitoramento)
        self.btn_iniciar.grid(row=1, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        self.btn_parar = ttk.Button(controles_frame, text="Parar Monitoramento", command=self.parar_monitoramento, state=tk.DISABLED)
        self.btn_parar.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- Separador ---
        ttk.Separator(controles_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        # --- Mostradores de Dados ---
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("Valor.TLabel", font=("Helvetica", 14, "bold"), foreground="blue")

        ttk.Label(controles_frame, text="Tensão na Bateria (V):").grid(row=4, column=0, padx=5, pady=10, sticky="w")
        self.tensao_var = tk.StringVar(value="0.00")
        ttk.Label(controles_frame, textvariable=self.tensao_var, style="Valor.TLabel").grid(row=4, column=1, padx=5, pady=10, sticky="e")

        ttk.Label(controles_frame, text="Corrente (A):").grid(row=5, column=0, padx=5, pady=10, sticky="w")
        self.corrente_var = tk.StringVar(value="0.000")
        ttk.Label(controles_frame, textvariable=self.corrente_var, style="Valor.TLabel").grid(row=5, column=1, padx=5, pady=10, sticky="e")

        ttk.Label(controles_frame, text="Capacidade Usada (mAh):").grid(row=6, column=0, padx=5, pady=10, sticky="w")
        self.capacidade_var = tk.StringVar(value="0.0")
        ttk.Label(controles_frame, textvariable=self.capacidade_var, style="Valor.TLabel").grid(row=6, column=1, padx=5, pady=10, sticky="e")

        ttk.Label(controles_frame, text="Tempo Decorrido:").grid(row=7, column=0, padx=5, pady=10, sticky="w")
        self.tempo_var = tk.StringVar(value="00:00:00")
        ttk.Label(controles_frame, textvariable=self.tempo_var, style="Valor.TLabel").grid(row=7, column=1, padx=5, pady=10, sticky="e")

        ttk.Label(controles_frame, text="Status:").grid(row=8, column=0, padx=5, pady=10, sticky="w")
        self.status_var = tk.StringVar(value="Parado")
        ttk.Label(controles_frame, textvariable=self.status_var, style="Valor.TLabel").grid(row=8, column=1, padx=5, pady=10, sticky="e")

        # Frame do Gráfico (Direita)
        grafico_frame = ttk.LabelFrame(main_frame, text="Tensão da Bateria vs. Tempo", padding="10")
        grafico_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Gráfico Matplotlib ---
        self.figura = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figura.add_subplot(111)
        self.ax.set_title("Descarga da Bateria")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Tensão (V)")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.figura, master=grafico_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.draw()
        
        # Adiciona um handler para o fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.fechar_janela)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handler para exceções não tratadas"""
        import traceback
        error_msg = f"Erro não tratado:\nTipo: {exc_type.__name__}\nMensagem: {exc_value}"
        print(error_msg)
        traceback.print_tb(exc_traceback)
        
        # Mostra mensagem de erro na GUI se possível
        try:
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{exc_value}\n\nO programa pode não funcionar corretamente.")
        except:
            pass

    def iniciar_monitoramento(self):
        try:
            # Tenta abrir a porta serial
            porta = self.porta_serial_entry.get()
            # Timeout maior que o intervalo de envio do Arduino (10s + margem de segurança)
            self.porta_serial = serial.Serial(porta, 9600, timeout=20)
            time.sleep(2) # Aguarda a inicialização do Arduino
            
            # Limpa o buffer serial para evitar dados antigos
            self.porta_serial.reset_input_buffer()
            self.porta_serial.reset_output_buffer()
            
            # Testa a comunicação enviando um comando de teste
            print(f"Conectado à porta {porta}")
            print("Aguardando dados do Arduino...")
            print("Nota: O Arduino deve enviar dados a cada 10 segundos")
            
            # Aguarda um pouco mais para sincronizar com o Arduino
            time.sleep(3)
            
        except serial.SerialException as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar à porta {porta}.\nVerifique a porta e tente novamente.\n\nErro: {e}")
            return

        # Reseta os dados e o gráfico
        self.dados = []
        self.ax.clear()
        self.ax.grid(True)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Tensão (V)")

        # Configura o estado dos botões
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_parar.config(state=tk.NORMAL)
        
        # Atualiza status
        self.status_var.set("Iniciando...")
        
        # Inicia a thread de leitura
        self.monitorando = True
        self.thread_leitura = threading.Thread(target=self.loop_leitura, daemon=True)
        self.thread_leitura.start()

    def parar_monitoramento(self):
        self.monitorando = False
        if self.thread_leitura:
            self.thread_leitura.join() # Espera a thread terminar
        
        if self.porta_serial and self.porta_serial.is_open:
            self.porta_serial.close()

        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_parar.config(state=tk.DISABLED)
        self.status_var.set("Parado")
        messagebox.showinfo("Finalizado", "Monitoramento parado.")

    def loop_leitura(self):
        # Nome do arquivo de saída
        timestamp_inicio = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.nome_arquivo_excel = f"log_bateria_{timestamp_inicio}.xlsx"

        capacidade_total_As = 0.0 # Ampere-segundo
        tempo_inicio = time.time()
        contador_erros = 0
        max_erros_consecutivos = 10

        while self.monitorando:
            try:
                if not self.porta_serial or not self.porta_serial.is_open:
                    print("Porta serial fechada ou não disponível")
                    break
                
                # Atualiza status para "Aguardando dados..."
                self.root.after(0, lambda: self.status_var.set("Aguardando dados..."))
                
                linha = self.porta_serial.readline()
                if not linha:
                    # Timeout é esperado quando o Arduino envia dados a cada 10s
                    # Não é um erro, apenas aguarda o próximo ciclo
                    continue
                
                linha_decodificada = linha.decode('utf-8').strip()
                if not linha_decodificada:
                    continue
                
                # Dados recebidos com sucesso

                try:
                    valor_adc = int(linha_decodificada)
                except ValueError:
                    print(f"Valor ADC inválido: {linha_decodificada}")
                    continue

                # --- Cálculos ---
                tensao_shunt = (valor_adc / RESOLUCAO_ADC) * TENSAO_REFERENCIA_ARDUINO
                corrente = tensao_shunt / RESISTOR_SHUNT
                tensao_bateria = corrente * RESISTOR_TOTAL
                
                # Integral da corrente (Capacidade)
                capacidade_total_As += corrente * INTERVALO_MEDIDA  # Corrente * tempo = carga
                capacidade_total_mAh = (capacidade_total_As / 3600) * 1000

                # Tempo decorrido
                tempo_decorrido_s = time.time() - tempo_inicio
                
                # Armazena os dados
                timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nova_linha = {
                    "Timestamp": timestamp_atual,
                    "Tempo (s)": tempo_decorrido_s,
                    "Valor ADC": valor_adc,
                    "Tensão Bateria (V)": tensao_bateria,
                    "Corrente (A)": corrente,
                    "Capacidade Usada (mAh)": capacidade_total_mAh
                }
                self.dados.append(nova_linha)

                # Atualiza a GUI (de forma segura para threads)
                try:
                    self.root.after(0, self.atualizar_gui, nova_linha, tempo_decorrido_s)
                except Exception as e:
                    print(f"Erro ao atualizar GUI: {e}")
                
                # Salva no Excel
                try:
                    self.salvar_em_excel(nova_linha)
                except Exception as e:
                    print(f"Erro ao salvar no Excel: {e}")

                # Reset contador de erros se tudo funcionou
                contador_erros = 0
                
                # Atualiza status para "Dados recebidos"
                self.root.after(0, lambda: self.status_var.set("Dados recebidos"))

            except serial.SerialException as e:
                contador_erros += 1
                print(f"Erro de comunicação serial ({contador_erros}/{max_erros_consecutivos}): {e}")
                self.root.after(0, lambda: self.status_var.set(f"Erro: {contador_erros}/{max_erros_consecutivos}"))
                if contador_erros >= max_erros_consecutivos:
                    print("Muitos erros consecutivos. Parando monitoramento.")
                    self.root.after(0, lambda: messagebox.showerror("Erro", "Muitos erros de comunicação. Monitoramento parado."))
                    break
                time.sleep(1)  # Pausa antes de tentar novamente
                
            except Exception as e:
                contador_erros += 1
                print(f"Erro inesperado ({contador_erros}/{max_erros_consecutivos}): {e}")
                if contador_erros >= max_erros_consecutivos:
                    print("Muitos erros consecutivos. Parando monitoramento.")
                    self.root.after(0, lambda: messagebox.showerror("Erro", "Muitos erros inesperados. Monitoramento parado."))
                    break
                time.sleep(1)  # Pausa antes de tentar novamente
        
        print("Loop de leitura encerrado.")
        # Para o monitoramento automaticamente se a thread terminar
        self.root.after(0, self.parar_monitoramento)

    def atualizar_gui(self, ultima_leitura, tempo_decorrido):
        try:
            # Atualiza os mostradores
            self.tensao_var.set(f"{ultima_leitura['Tensão Bateria (V)']:.2f}")
            self.corrente_var.set(f"{ultima_leitura['Corrente (A)']:.3f}")
            self.capacidade_var.set(f"{ultima_leitura['Capacidade Usada (mAh)']:.1f}")
            
            # Formata o tempo
            mins, secs = divmod(int(tempo_decorrido), 60)
            hours, mins = divmod(mins, 60)
            self.tempo_var.set(f"{hours:02d}:{mins:02d}:{secs:02d}")

            # Atualiza o gráfico apenas se houver dados
            if self.dados and len(self.dados) > 0:
                tempos = [d['Tempo (s)'] for d in self.dados]
                tensoes = [d['Tensão Bateria (V)'] for d in self.dados]
                
                # Limita o número de pontos no gráfico para evitar lentidão
                if len(tempos) > 1000:
                    # Mostra apenas os últimos 1000 pontos
                    tempos = tempos[-1000:]
                    tensoes = tensoes[-1000:]
                
                self.ax.clear()
                self.ax.plot(tempos, tensoes, marker='.', linestyle='-', markersize=4)
                self.ax.set_title("Descarga da Bateria")
                self.ax.set_xlabel("Tempo (s)")
                self.ax.set_ylabel("Tensão (V)")
                self.ax.grid(True)
                
                # Ajusta automaticamente os limites do gráfico
                if len(tensoes) > 1:
                    self.ax.relim()
                    self.ax.autoscale_view()
                
                self.canvas.draw()
                
        except Exception as e:
            print(f"Erro ao atualizar GUI: {e}")
            # Não deixa o erro propagar para evitar crash

    def salvar_em_excel(self, ultima_leitura):
        try:
            df_novo = pd.DataFrame([ultima_leitura])
            
            # Se o arquivo não existe, cria com cabeçalho
            try:
                with pd.ExcelWriter(self.nome_arquivo_excel, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    # Verifica se a planilha existe
                    if 'Sheet1' in writer.sheets:
                        startrow = writer.sheets['Sheet1'].max_row
                    else:
                        startrow = 0
                    df_novo.to_excel(writer, index=False, header=(startrow == 0), startrow=startrow)
            except FileNotFoundError:
                df_novo.to_excel(self.nome_arquivo_excel, index=False, header=True)
            except PermissionError:
                print("Arquivo Excel está aberto. Dados não salvos.")
            except Exception as e:
                print(f"Erro ao salvar no Excel: {e}")

        except Exception as e:
            print(f"Erro geral ao salvar no Excel: {e}")

    def fechar_janela(self):
        if self.monitorando:
            if messagebox.askokcancel("Sair", "O monitoramento está em andamento. Deseja realmente parar e sair?"):
                self.parar_monitoramento()
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MonitorBateriaApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro crítico na aplicação: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para sair...") 