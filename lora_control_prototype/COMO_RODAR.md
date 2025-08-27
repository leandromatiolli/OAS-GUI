# 🚀 GUIA COMPLETO - COMO RODAR O SISTEMA LoRa

## 📋 **PRÉ-REQUISITOS**

### **Hardware Necessário:**
- **1x Arduino Pro Mini** (ou similar)
- **2x Módulos LoRa E220-900T22D** (um para transmissor, um para receptor)
- **1x MOSFET** (para controle de carga)
- **1x LED** (opcional, para status visual)
- **1x Cabo USB** (para conectar Arduino ao PC)
- **1x Protoboard** e jumpers
- **1x Fonte de alimentação** (3.3V para LoRa, 5V para Arduino)

### **Software Necessário:**
- **Arduino IDE** (versão 1.8.x ou superior)
- **Python 3.7+** com as bibliotecas:
  - `PyQt5`
  - `pyserial`

---

## 🔧 **PASSO 1: CONFIGURAÇÃO DO HARDWARE**

### **Conexões do Receptor (Arduino):**
```
LoRa E220 -> Arduino Pro Mini
├── M0     -> D3
├── M1     -> D4
├── RXD    -> D11 (TX do Arduino)
├── TXD    -> D10 (RX do Arduino)
├── AUX    -> D2  (INTERRUPÇÃO - CRÍTICO!)
├── VCC    -> 3.3V
└── GND    -> GND

MOSFET -> Arduino
├── Gate  -> D7
├── Drain -> Carga (lâmpada, motor, etc.)
└── Source -> GND

LED Status -> Arduino
├── Anodo -> D13 (LED_BUILTIN)
└── Catodo -> GND (via resistor 220Ω)
```

### **Conexões do Transmissor (PC):**
```
LoRa E220 -> USB-TTL
├── M0     -> GND (LOW)
├── M1     -> GND (LOW)
├── RXD    -> TX do USB-TTL
├── TXD    -> RX do USB-TTL
├── AUX    -> Não conectado
├── VCC    -> 3.3V
└── GND    -> GND
```

---

## 💻 **PASSO 2: INSTALAÇÃO DO SOFTWARE**

### **2.1 Instalar Python e Bibliotecas:**
```bash
# Instalar PyQt5 e pyserial
pip install PyQt5 pyserial
```

### **2.2 Verificar Arduino IDE:**
- Abrir Arduino IDE
- Selecionar placa: **Arduino Pro Mini**
- Selecionar processador: **ATmega328P (3.3V, 8MHz)**
- Selecionar porta COM correta

---

## 📱 **PASSO 3: CARREGAR CÓDIGO NO ARDUINO**

### **3.1 Abrir o código:**
- Abrir Arduino IDE
- Abrir arquivo: `arduino_lora_control_final.ino`

### **3.2 Compilar e Carregar:**
- Clicar em **"Verificar"** (✓) para compilar
- Clicar em **"Carregar"** (→) para enviar para Arduino
- Aguardar mensagem "Carregamento concluído"

### **3.3 Verificar funcionamento:**
- Abrir **Monitor Serial** (Ctrl+Shift+M)
- Configurar baud rate: **9600**
- Deve aparecer:
```
========================================
SISTEMA DE CONTROLE LoRa - VERSÃO FINAL
========================================

✓ Sistema inicializado
✓ Interrupção AUX configurada
✓ LoRa em modo operação

COMANDOS DISPONÍVEIS:
  'L' = Ligar equipamento
  'D' = Desligar equipamento e dormir

Sistema pronto! Entrando em modo sleep...
========================================
😴 Entrando em modo sleep...
```

---

## 🖥️ **PASSO 4: EXECUTAR A GUI DO PC**

### **4.1 Abrir terminal/prompt:**
```bash
cd lora_control_prototype
python pc_transmitter_gui.py
```

### **4.2 Configurar a GUI:**
- **Atualizar Portas**: Clicar em "Atualizar Portas"
- **Selecionar Porta**: Escolher a porta COM do LoRa transmissor
- **Verificar conexão**: A GUI deve mostrar "Interface iniciada"

---

## 🎯 **PASSO 5: TESTAR O SISTEMA**

### **5.1 Teste Básico:**
1. **Ligar**: Clicar em "Ligar Equipamento"
   - LED do Arduino deve acender
   - MOSFET deve ativar
   - GUI deve mostrar "SUCESSO: Resposta ACK correta"

2. **Desligar**: Clicar em "Desligar Equipamento"
   - LED do Arduino deve apagar
   - MOSFET deve desativar
   - Arduino deve voltar a dormir

### **5.2 Verificar Logs:**
- **No Arduino**: Monitor Serial mostra comandos recebidos
- **Na GUI**: Console mostra comunicação bidirecional

---

## 🔍 **TROUBLESHOOTING**

### **Problema: Arduino não acorda**
- ✅ Verificar conexão AUX → D2
- ✅ Verificar se LoRa está em modo operação (M0=LOW, M1=LOW)
- ✅ Verificar alimentação 3.3V do LoRa

### **Problema: Comandos não chegam**
- ✅ Verificar baud rate (9600)
- ✅ Verificar conexões RXD/TXD
- ✅ Verificar se LoRa está configurado corretamente

### **Problema: MOSFET não ativa**
- ✅ Verificar conexão Gate → D7
- ✅ Verificar alimentação da carga
- ✅ Verificar se MOSFET está funcionando

### **Problema: GUI não conecta**
- ✅ Verificar drivers USB-TTL
- ✅ Verificar porta COM correta
- ✅ Verificar se Python e bibliotecas estão instalados

---

## 📊 **MONITORAMENTO**

### **Indicadores Visuais:**
- **LED Arduino**: Status do equipamento (aceso = ligado)
- **GUI**: Logs de comunicação em tempo real
- **Monitor Serial**: Debug detalhado do Arduino

### **Comandos Disponíveis:**
- **'L'**: Liga equipamento e mantém acordado
- **'D'**: Desliga equipamento e volta a dormir

---

## ⚡ **CARACTERÍSTICAS DO SISTEMA**

### **Modo de Baixo Consumo:**
- **Sleep**: ~0.1mA (muito baixo)
- **Acordado**: ~20-30mA (normal)
- **Acorda em**: ~1-2ms

### **Tempo de Resposta:**
- **Processar comando**: ~500ms
- **Voltar a dormir**: ~200ms
- **Anti-duplicação**: 300ms

---

## 🎉 **SISTEMA PRONTO!**

O sistema está funcionando quando:
- ✅ Arduino entra em sleep automaticamente
- ✅ Comando 'L' acorda e liga equipamento
- ✅ Comando 'D' desliga e volta a dormir
- ✅ GUI mostra comunicação bem-sucedida
- ✅ LED representa estado do MOSFET

**Agora você tem um sistema de controle remoto LoRa completo e funcional!** 🚀
