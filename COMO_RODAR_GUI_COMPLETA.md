# 🖥️ **COMO RODAR A GUI COMPLETA DO OAS**

## 🚀 **COMANDO RÁPIDO:**

```bash
python main.py
```

## 📋 **PRÉ-REQUISITOS:**

### **Software Necessário:**
- **Python 3.7+**
- **Bibliotecas Python:**
  - `PyQt5`
  - `numpy`
  - `scipy`
  - `matplotlib`
  - `pyserial`

### **Instalação das Dependências:**
```bash
# Instalar todas as dependências
pip install PyQt5 numpy scipy matplotlib pyserial

# Ou usar o requirements.txt (se existir)
pip install -r requirements.txt
```

## 🔧 **CONFIGURAÇÃO:**

### **1. Verificar Estrutura de Pastas:**
```
OAS-GUI/
├── app/
│   ├── controllers/
│   ├── models/
│   ├── utils/
│   └── views/
├── config/
├── data/
├── resources/
└── main.py
```

### **2. Configurações Iniciais:**
- **Pasta de Calibração**: `data/Calibrações/`
- **Pasta de Dados**: `data/`
- **Configurações**: `config/`

## 🎯 **FUNCIONALIDADES DISPONÍVEIS:**

### **📊 Aba de Aquisição:**
- ✅ Aquisição de dados via RedPitaya
- ✅ Calibração de sensores
- ✅ Controle LoRa (ligar/desligar equipamentos)
- ✅ Configuração de metadados

### **📈 Aba de Análise:**
- ✅ Visualização de dados brutos
- ✅ Demodulação de sinais
- ✅ Filtros passa-banda
- ✅ Média móvel
- ✅ Espectrogramas
- ✅ Análise de espectro

### **🎵 Aba de Áudio:**
- ✅ Geração de áudio
- ✅ Análise de espectro de áudio
- ✅ Reprodução de áudio

### **🔊 Aba Ultra-Hear:**
- ✅ Processamento de áudio ultrassônico
- ✅ Conversão de frequências

### **📝 Aba de Logs:**
- ✅ Logs em tempo real
- ✅ Debug detalhado

## 🚨 **TROUBLESHOOTING:**

### **Erro: "Module not found"**
```bash
# Verificar se está no diretório correto
cd "C:\Users\win\OneDrive\Empresa 2\Lab\OAS-GUI"

# Instalar dependências faltantes
pip install [nome_do_modulo]
```

### **Erro: "Hardware não disponível"**
- ✅ Verificar conexão com RedPitaya
- ✅ Verificar IP do RedPitaya
- ✅ Verificar rede

### **Erro: "Porta serial não encontrada"**
- ✅ Verificar drivers USB-TTL
- ✅ Verificar porta COM correta
- ✅ Verificar conexões LoRa

## 📱 **CONTROLE LoRa INTEGRADO:**

### **Funcionalidades:**
- ✅ **Ligar Equipamento**: Envia comando 'L' via LoRa
- ✅ **Desligar Equipamento**: Envia comando 'D' via LoRa
- ✅ **Status em Tempo Real**: Mostra resposta do Arduino
- ✅ **Lista de Portas**: Atualização automática

### **Configuração LoRa:**
- **Baud Rate**: 9600
- **Modo**: Operação (M0=LOW, M1=LOW)
- **Frequência**: 915MHz

## 🎉 **SISTEMA PRONTO!**

### **Para rodar:**
1. **Abrir terminal/prompt**
2. **Navegar para a pasta**: `cd "C:\Users\win\OneDrive\Empresa 2\Lab\OAS-GUI"`
3. **Executar**: `python main.py`
4. **Aguardar**: Interface gráfica abrirá automaticamente

### **Interface aparecerá com:**
- ✅ Todas as abas funcionais
- ✅ Controle LoRa integrado
- ✅ Sistema de logs ativo
- ✅ Configurações carregadas

**A GUI completa do OAS está pronta para uso!** 🚀
