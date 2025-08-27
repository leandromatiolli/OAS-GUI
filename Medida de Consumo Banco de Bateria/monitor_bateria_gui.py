#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI para Monitoramento de Banco de Baterias Li-ion 3S
Interface gráfica com plotagem em tempo real e gravação de dados
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import numpy as np
from collections import deque
import json

class MonitorBateriaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Banco de Baterias Li-ion 3S")
        self.root.geometry("1400x900")
        
        # Variáveis de controle
        self.arduino = None
        self.conectado = False
        self.gravando = False
        self.arquivo_csv = None
        self.writer_csv = None
        
        # Buffer para gravação em lotes
        self.buffer_dados = []
        self.max_buffer_size = 10  # Gravar a cada 10 medições
        
        # Dados para plotagem (últimos 50 pontos para reduzir carga)
        self.max_pontos = 50
        self.tempos = deque(maxlen=self.max_pontos)
        self.tensoes_bat = deque(maxlen=self.max_pontos)
        self.correntes_bat = deque(maxlen=self.max_pontos)
        self.potencias_bat = deque(maxlen=self.max_pontos)
        self.capacidades = deque(maxlen=self.max_pontos)
        self.tensoes_res = deque(maxlen=self.max_pontos)
        self.correntes_res = deque(maxlen=self.max_pontos)
        self.potencias_res = deque(maxlen=self.max_pontos)
        
        # --- Configurações Persistentes ---
        self.config_file = 'config.json'
        
        # Valores padrão
        self.capacidade_total = 2200.0
        self.tensao_nominal = 11.1
        self.resistor_carga = 10.0
        self.resistor_shunt = 0.1
        self.r1_divisor = 20000.0
        self.r2_divisor = 10000.0
        
        # Carregar configurações salvas
        self.load_last_state()
        
        # Thread para leitura serial
        self.thread_serial = None
        self.parar_thread = False
        
        # Controle de atualização
        self.ultima_atualizacao = 0
        self.intervalo_atualizacao = 1.0  # 1 segundo entre atualizações
        
        # Lock para thread safety
        self.lock_dados = threading.Lock()
        
        self.criar_interface()
        self.criar_graficos()
        
    def criar_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Frame de controle
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding="5")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Porta serial
        ttk.Label(control_frame, text="Porta:").grid(row=0, column=0, padx=(0, 5))
        self.combo_porta = ttk.Combobox(control_frame, width=15)
        self.combo_porta.grid(row=0, column=1, padx=(0, 10))
        
        # Botão conectar
        self.btn_conectar = ttk.Button(control_frame, text="Conectar", command=self.conectar_arduino)
        self.btn_conectar.grid(row=0, column=2, padx=(0, 10))
        
        # Botão gravar
        self.btn_gravar = ttk.Button(control_frame, text="Iniciar Gravação", command=self.iniciar_gravacao)
        self.btn_gravar.grid(row=0, column=3, padx=(0, 10))
        
        # Botão reset
        self.btn_reset = ttk.Button(control_frame, text="Reset Contadores", command=self.reset_contadores)
        self.btn_reset.grid(row=0, column=4, padx=(0, 10))
        
        # Status
        self.label_status = ttk.Label(control_frame, text="Desconectado", foreground="red")
        self.label_status.grid(row=0, column=5, padx=(10, 0))
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="5")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Capacidade total da bateria
        ttk.Label(config_frame, text="Capacidade Total (mAh):").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.entry_capacidade = ttk.Entry(config_frame, width=10)
        self.entry_capacidade.insert(0, str(self.capacidade_total))
        self.entry_capacidade.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        # Tensão nominal
        ttk.Label(config_frame, text="Tensão Nominal (V):").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.entry_tensao = ttk.Entry(config_frame, width=10)
        self.entry_tensao.insert(0, str(self.tensao_nominal))
        self.entry_tensao.grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
        
        # --- Novos campos para resistores ---
        # Resistor de Carga
        ttk.Label(config_frame, text="Resistor Carga (Ω):").grid(row=1, column=0, padx=(0, 5), pady=(5,0), sticky=tk.W)
        self.entry_res_carga = ttk.Entry(config_frame, width=10)
        self.entry_res_carga.insert(0, str(self.resistor_carga))
        self.entry_res_carga.grid(row=1, column=1, padx=(0, 20), pady=(5,0), sticky=tk.W)

        # Resistor Shunt
        ttk.Label(config_frame, text="Resistor Shunt (Ω):").grid(row=1, column=2, padx=(0, 5), pady=(5,0), sticky=tk.W)
        self.entry_res_shunt = ttk.Entry(config_frame, width=10)
        self.entry_res_shunt.insert(0, str(self.resistor_shunt))
        self.entry_res_shunt.grid(row=1, column=3, padx=(0, 20), pady=(5,0), sticky=tk.W)

        # Divisor de Tensão R1
        ttk.Label(config_frame, text="Divisor R1 (Ω):").grid(row=2, column=0, padx=(0, 5), pady=(5,0), sticky=tk.W)
        self.entry_r1 = ttk.Entry(config_frame, width=10)
        self.entry_r1.insert(0, str(self.r1_divisor))
        self.entry_r1.grid(row=2, column=1, padx=(0, 20), pady=(5,0), sticky=tk.W)

        # Divisor de Tensão R2
        ttk.Label(config_frame, text="Divisor R2 (Ω):").grid(row=2, column=2, padx=(0, 5), pady=(5,0), sticky=tk.W)
        self.entry_r2 = ttk.Entry(config_frame, width=10)
        self.entry_r2.insert(0, str(self.r2_divisor))
        self.entry_r2.grid(row=2, column=3, padx=(0, 20), pady=(5,0), sticky=tk.W)
        
        # Botão aplicar configurações
        ttk.Button(config_frame, text="Aplicar", command=self.aplicar_configuracoes).grid(row=2, column=4, padx=(10,0))
        
        # Frame de valores atuais
        valores_frame = ttk.LabelFrame(main_frame, text="Valores Atuais", padding="5")
        valores_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Grid para valores
        valores_frame.columnconfigure(1, weight=1)
        valores_frame.columnconfigure(3, weight=1)
        
        # Bateria
        ttk.Label(valores_frame, text="BATERIA:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(valores_frame, text="Tensão:").grid(row=1, column=0, sticky=tk.W)
        self.label_tensao_bat = ttk.Label(valores_frame, text="0.000 V")
        self.label_tensao_bat.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(valores_frame, text="Corrente:").grid(row=2, column=0, sticky=tk.W)
        self.label_corrente_bat = ttk.Label(valores_frame, text="0.000 A")
        self.label_corrente_bat.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(valores_frame, text="Potência:").grid(row=3, column=0, sticky=tk.W)
        self.label_potencia_bat = ttk.Label(valores_frame, text="0.000 W")
        self.label_potencia_bat.grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(valores_frame, text="Capacidade Usada:").grid(row=4, column=0, sticky=tk.W)
        self.label_capacidade_usada = ttk.Label(valores_frame, text="0.00 mAh")
        self.label_capacidade_usada.grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(valores_frame, text="% Restante:").grid(row=5, column=0, sticky=tk.W)
        self.label_percentual = ttk.Label(valores_frame, text="100.0%")
        self.label_percentual.grid(row=5, column=1, sticky=tk.W, padx=(10, 0))
        
        # Resistor de carga
        ttk.Label(valores_frame, text="RESISTOR DE CARGA:", font=("Arial", 12, "bold")).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(valores_frame, text="Tensão:").grid(row=7, column=0, sticky=tk.W)
        self.label_tensao_res = ttk.Label(valores_frame, text="0.000 V")
        self.label_tensao_res.grid(row=7, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(valores_frame, text="Corrente:").grid(row=8, column=0, sticky=tk.W)
        self.label_corrente_res = ttk.Label(valores_frame, text="0.000 A")
        self.label_corrente_res.grid(row=8, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(valores_frame, text="Potência:").grid(row=9, column=0, sticky=tk.W)
        self.label_potencia_res = ttk.Label(valores_frame, text="0.000 W")
        self.label_potencia_res.grid(row=9, column=1, sticky=tk.W, padx=(10, 0))
        
        # Energia total
        ttk.Label(valores_frame, text="Energia Total:").grid(row=10, column=0, sticky=tk.W, pady=(20, 0))
        self.label_energia_total = ttk.Label(valores_frame, text="0.00 mWh")
        self.label_energia_total.grid(row=10, column=1, sticky=tk.W, padx=(10, 0), pady=(20, 0))
        
        # Frame dos gráficos
        graficos_frame = ttk.LabelFrame(main_frame, text="Gráficos em Tempo Real", padding="5")
        graficos_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Atualizar lista de portas
        self.atualizar_portas()
        
    def criar_graficos(self):
        # Criar figura com subplots
        self.fig = Figure(figsize=(12, 8), dpi=100)
        
        # Gráfico 1: Tensão, Corrente e Potência
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax1_twin = self.ax1.twinx()  # Criar o eixo gêmeo aqui
        
        self.ax1.set_title("Tensão, Corrente e Potência da Bateria")
        self.ax1.set_xlabel("Tempo (s)")
        self.ax1.set_ylabel("Valor")
        self.ax1.grid(True)
        
        # Gráfico 2: Capacidade Utilizada
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        self.ax2.set_title("Capacidade da Bateria Utilizada")
        self.ax2.set_xlabel("Tempo (s)")
        self.ax2.set_ylabel("Capacidade (mAh)")
        self.ax2.grid(True)
        
        # Criar canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        
        # Posicionar canvas no frame de gráficos
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.LabelFrame) and "Gráficos" in child.cget("text"):
                        self.canvas.get_tk_widget().pack(in_=child, fill=tk.BOTH, expand=True)
                        break
        
        # Configurar animação com intervalo maior
        self.ani = animation.FuncAnimation(self.fig, self.atualizar_graficos, interval=1000, blit=False)
        
    def atualizar_graficos(self, frame):
        if len(self.tempos) > 1:
            try:
                # Limpar gráficos
                self.ax1.clear()
                self.ax1_twin.clear() # Limpar o eixo gêmeo também
                self.ax2.clear()
                
                # Converter tempos para segundos
                tempos_sec = [(t - self.tempos[0]) / 1000.0 for t in self.tempos]
                
                # Gráfico 1: Tensão, Corrente e Potência
                self.ax1.plot(tempos_sec, list(self.tensoes_bat), 'b-', label='Tensão (V)', linewidth=2)
                self.ax1_twin.plot(tempos_sec, list(self.correntes_bat), 'r-', label='Corrente (A)', linewidth=2)
                self.ax1_twin.plot(tempos_sec, list(self.potencias_bat), 'g-', label='Potência (W)', linewidth=2)
                
                self.ax1.set_title("Tensão, Corrente e Potência da Bateria")
                self.ax1.set_xlabel("Tempo (s)")
                self.ax1.set_ylabel("Tensão (V)", color='b')
                self.ax1_twin.set_ylabel("Corrente (A) / Potência (W)", color='r')
                self.ax1.grid(True)
                
                # Legenda
                lines1, labels1 = self.ax1.get_legend_handles_labels()
                lines2, labels2 = self.ax1_twin.get_legend_handles_labels()
                self.ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                # Gráfico 2: Capacidade
                self.ax2.plot(tempos_sec, list(self.capacidades), 'purple', linewidth=2)
                self.ax2.set_title("Capacidade da Bateria Utilizada")
                self.ax2.set_xlabel("Tempo (s)")
                self.ax2.set_ylabel("Capacidade (mAh)")
                self.ax2.grid(True)
                
                # Linha de capacidade total
                self.ax2.axhline(y=self.capacidade_total, color='red', linestyle='--', label=f'Capacidade Total ({self.capacidade_total} mAh)')
                self.ax2.legend()
                
            except Exception as e:
                print(f"Erro ao atualizar gráficos: {e}")
                
        return []
        
    def atualizar_portas(self):
        portas = [port.device for port in serial.tools.list_ports.comports()]
        self.combo_porta['values'] = portas
        if portas:
            self.combo_porta.set(portas[0])
            
    def conectar_arduino(self):
        if not self.conectado:
            porta = self.combo_porta.get()
            if not porta:
                messagebox.showerror("Erro", "Selecione uma porta serial")
                return
                
            try:
                self.arduino = serial.Serial(porta, 115200, timeout=1)
                self.conectado = True
                self.btn_conectar.config(text="Desconectar")
                self.label_status.config(text="Conectado", foreground="green")
                
                # Iniciar thread de leitura
                self.parar_thread = False
                self.thread_serial = threading.Thread(target=self.ler_serial)
                self.thread_serial.daemon = True
                self.thread_serial.start()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao conectar: {str(e)}")
        else:
            self.desconectar_arduino()
            
    def desconectar_arduino(self):
        if self.gravando:
            self.parar_gravacao()
            
        self.parar_thread = True
        if self.thread_serial:
            self.thread_serial.join(timeout=1)
            
        if self.arduino:
            self.arduino.close()
            
        self.conectado = False
        self.btn_conectar.config(text="Conectar")
        self.label_status.config(text="Desconectado", foreground="red")
        
    def ler_serial(self):
        while not self.parar_thread:
            try:
                if self.arduino and self.arduino.in_waiting:
                    linha = self.arduino.readline().decode('utf-8').strip()
                    if linha and ',' in linha:
                        self.processar_dados(linha)
                time.sleep(0.1)  # Reduzir frequência de leitura
            except Exception as e:
                print(f"Erro na leitura serial: {e}")
                break
                
    def processar_dados(self, linha):
        try:
            dados = linha.split(',')
            if len(dados) >= 9:
                tempo = float(dados[0])
                tensao_bat = float(dados[1])
                corrente_bat = float(dados[2])
                tensao_res = float(dados[3])
                corrente_res = float(dados[4])
                potencia_bat = float(dados[5])
                potencia_res = float(dados[6])
                capacidade = float(dados[7])
                energia = float(dados[8])
                
                # Usar lock para thread safety
                with self.lock_dados:
                    # Adicionar dados às listas
                    self.tempos.append(tempo)
                    self.tensoes_bat.append(tensao_bat)
                    self.correntes_bat.append(corrente_bat)
                    self.potencias_bat.append(potencia_bat)
                    self.capacidades.append(capacidade)
                    self.tensoes_res.append(tensao_res)
                    self.correntes_res.append(corrente_res)
                    self.potencias_res.append(potencia_res)
                
                # Atualizar interface apenas a cada segundo
                tempo_atual = time.time()
                if tempo_atual - self.ultima_atualizacao >= self.intervalo_atualizacao:
                    self.ultima_atualizacao = tempo_atual
                    self.root.after(0, self.atualizar_interface, tensao_bat, corrente_bat, potencia_bat,
                                  tensao_res, corrente_res, potencia_res, capacidade, energia)
                
                # Adicionar ao buffer para gravação
                if self.gravando:
                    self.buffer_dados.append([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                        tempo, tensao_bat, corrente_bat, tensao_res, corrente_res,
                        potencia_bat, potencia_res, capacidade, energia
                    ])
                    
                    # Gravar quando buffer estiver cheio
                    if len(self.buffer_dados) >= self.max_buffer_size:
                        self.gravar_buffer()
                    
        except Exception as e:
            print(f"Erro ao processar dados: {e}")
            
    def gravar_buffer(self):
        """Grava o buffer de dados no arquivo CSV"""
        if self.writer_csv and self.buffer_dados:
            try:
                for linha in self.buffer_dados:
                    self.writer_csv.writerow(linha)
                self.arquivo_csv.flush()
                self.buffer_dados.clear()
            except Exception as e:
                print(f"Erro ao gravar buffer: {e}")
            
    def atualizar_interface(self, tensao_bat, corrente_bat, potencia_bat, tensao_res, corrente_res, potencia_res, capacidade, energia):
        # Atualizar labels
        self.label_tensao_bat.config(text=f"{tensao_bat:.3f} V")
        self.label_corrente_bat.config(text=f"{corrente_bat:.3f} A")
        self.label_potencia_bat.config(text=f"{potencia_bat:.3f} W")
        self.label_capacidade_usada.config(text=f"{capacidade:.2f} mAh")
        
        self.label_tensao_res.config(text=f"{tensao_res:.3f} V")
        self.label_corrente_res.config(text=f"{corrente_res:.3f} A")
        self.label_potencia_res.config(text=f"{potencia_res:.3f} W")
        self.label_energia_total.config(text=f"{energia:.2f} mWh")
        
        # Calcular percentual restante
        percentual = max(0, 100 - (capacidade / self.capacidade_total * 100))
        self.label_percentual.config(text=f"{percentual:.1f}%")
        
        # Mudar cor do percentual baseado no nível
        if percentual < 20:
            self.label_percentual.config(foreground="red")
        elif percentual < 50:
            self.label_percentual.config(foreground="orange")
        else:
            self.label_percentual.config(foreground="green")
            
    def iniciar_gravacao(self):
        if not self.conectado:
            messagebox.showerror("Erro", "Conecte o Arduino primeiro")
            return
        if not self.gravando:
            self.abrir_janela_nome_arquivo()
        else:
            self.parar_gravacao()

    def abrir_janela_nome_arquivo(self):
        self.janela_nome = tk.Toplevel(self.root)
        self.janela_nome.title("Nome do Arquivo de Gravação")
        self.janela_nome.geometry("400x120")
        self.janela_nome.transient(self.root)
        self.janela_nome.grab_set()
        self.janela_nome.resizable(False, False)
        tk.Label(self.janela_nome, text="Digite o nome do arquivo (ex: dados.csv):").pack(pady=10)
        self.entry_nome_arquivo = tk.Entry(self.janela_nome, width=40)
        self.entry_nome_arquivo.pack(pady=5)
        self.entry_nome_arquivo.focus()
        btn_frame = tk.Frame(self.janela_nome)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Confirmar", command=self.confirmar_nome_arquivo).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancelar", command=self.janela_nome.destroy).pack(side=tk.LEFT, padx=10)

    def confirmar_nome_arquivo(self):
        nome = self.entry_nome_arquivo.get().strip()
        if not nome:
            messagebox.showerror("Erro", "Digite um nome para o arquivo.", parent=self.janela_nome)
            return
        if not nome.lower().endswith('.csv'):
            nome += '.csv'
        try:
            self.arquivo_csv = open(nome, 'w', newline='', encoding='utf-8')
            self.writer_csv = csv.writer(self.arquivo_csv)
            self.writer_csv.writerow([
                'Timestamp', 'Tempo (ms)', 'Tensão Bateria (V)', 'Corrente Bateria (A)',
                'Tensão Resistor (V)', 'Corrente Resistor (A)', 'Potência Bateria (W)',
                'Potência Resistor (W)', 'Capacidade Usada (mAh)', 'Energia Total (mWh)'
            ])
            self.gravando = True
            self.btn_gravar.config(text="Parar Gravação")
            self.janela_nome.destroy()
            messagebox.showinfo("Sucesso", f"Gravação iniciada em: {nome}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar arquivo: {str(e)}", parent=self.janela_nome)
            
    def parar_gravacao(self):
        if self.gravando:
            # Gravar dados restantes no buffer
            self.gravar_buffer()
            
            self.gravando = False
            self.btn_gravar.config(text="Iniciar Gravação")
            
            if self.arquivo_csv:
                self.arquivo_csv.close()
                self.arquivo_csv = None
                self.writer_csv = None
                
            messagebox.showinfo("Sucesso", "Gravação parada")
            
    def reset_contadores(self):
        if self.conectado and self.arduino:
            try:
                self.arduino.write(b"RESET\n")
                messagebox.showinfo("Sucesso", "Contadores resetados")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao resetar contadores: {str(e)}")
                
    def aplicar_configuracoes(self):
        try:
            # Ler valores da GUI
            cap_total = float(self.entry_capacidade.get())
            ten_nominal = float(self.entry_tensao.get())
            res_carga = float(self.entry_res_carga.get())
            res_shunt = float(self.entry_res_shunt.get())
            r1 = float(self.entry_r1.get())
            r2 = float(self.entry_r2.get())

            # Atualizar variáveis internas
            self.capacidade_total = cap_total
            self.tensao_nominal = ten_nominal
            self.resistor_carga = res_carga
            self.resistor_shunt = res_shunt
            self.r1_divisor = r1
            self.r2_divisor = r2
            
            # Salvar configuração no arquivo
            self.save_last_state()

            # Enviar para o Arduino se conectado
            if self.conectado and self.arduino:
                comando = f"CONFIG,{res_carga},{res_shunt},{r1},{r2}\n"
                self.arduino.write(comando.encode('utf-8'))
                messagebox.showinfo("Sucesso", "Configurações salvas e enviadas ao Arduino.")
            else:
                messagebox.showinfo("Sucesso", "Configurações salvas. Conecte ao Arduino para enviá-las.")
            
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos. Por favor, insira apenas números.")

    def load_last_state(self):
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                self.capacidade_total = config_data.get('capacidade_total', self.capacidade_total)
                self.tensao_nominal = config_data.get('tensao_nominal', self.tensao_nominal)
                self.resistor_carga = config_data.get('resistor_carga', self.resistor_carga)
                self.resistor_shunt = config_data.get('resistor_shunt', self.resistor_shunt)
                self.r1_divisor = config_data.get('r1_divisor', self.r1_divisor)
                self.r2_divisor = config_data.get('r2_divisor', self.r2_divisor)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Arquivo de configuração não encontrado ou inválido. Usando valores padrão.")

    def save_last_state(self):
        config_data = {
            'capacidade_total': self.capacidade_total,
            'tensao_nominal': self.tensao_nominal,
            'resistor_carga': self.resistor_carga,
            'resistor_shunt': self.resistor_shunt,
            'r1_divisor': self.r1_divisor,
            'r2_divisor': self.r2_divisor,
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
            
    def on_closing(self):
        if self.gravando:
            self.parar_gravacao()
        if self.conectado:
            self.desconectar_arduino()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MonitorBateriaGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 