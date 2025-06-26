# 🎵 Ultra-Hear: Sistema Avançado de Análise de Frequências Ultrassônicas

## 📋 Visão Geral

O **Ultra-Hear** é um sistema completo implementado na aplicação OAS-GUI para análise e audição de sinais em frequências ultrassônicas (acima de 20 kHz). Permite transformar sinais inaudíveis em áudio perceptível através de algoritmos avançados de processamento de sinal.

## 🚀 Funcionalidades Implementadas

### 1. **Aba Ultra-Hear**
- Interface dedicada para análise de frequências ultrassônicas
- Seleção interativa de bandas de frequência no espectro
- Múltiplos algoritmos de transposição de frequência
- Controles avançados de amplitude e normalização

### 2. **Filtros de Espectro Interativos**
- **Seleção Manual**: Definir faixas de frequência por valores numéricos
- **Seleção Interativa**: Clicar e arrastar no gráfico do espectro para selecionar bandas
- **Bandas Pré-definidas**: Faixas otimizadas para ultrassom (20-40 kHz, 40-80 kHz, 80-120 kHz)

### 3. **Algoritmos de Transposição de Frequência**

#### 🔄 **Divisão de Frequência**
- Reduz frequências por um fator divisor (2-50x)
- Opção para manter velocidade de reprodução
- Ideal para análise geral de ultrassom

#### 📡 **Heterodino (Mixing)**
- Mistura sinal com frequência de referência
- Translada bandas específicas para faixa audível
- Preserva características espectrais originais

#### 📊 **Modulação em Amplitude**
- Extrai envelope do sinal ultrassônico
- Modula portadora em frequência audível
- Útil para detectar modulações de amplitude

#### ⏱️ **Compressão Temporal**
- Comprime sinal no tempo mantendo características
- Algoritmo baseado em PSOLA (Pitch Synchronous Overlap and Add)
- Preserva informação temporal

### 4. **Controles de Amplitude Avançados**

#### 📈 **Faixas de Amplitude**
- Definição de amplitude mínima e máxima em dB
- Controle de saturação seletiva
- Clipping suave usando função tanh

#### 🎚️ **Tipos de Normalização**
- **Peak Normalization**: Normaliza pelo pico máximo
- **RMS Normalization**: Normaliza pela energia RMS
- **Compressão Dinâmica**: Reduz faixa dinâmica automaticamente
- **Sem Normalização**: Mantém níveis originais

#### 🔊 **Ganho Adicional**
- Controle de ganho de -60 dB a +60 dB
- Aplicado antes da normalização
- Compensação de atenuação de filtros

### 5. **Filtros Avançados na Aba "Análise de Áudio"**

#### 🎛️ **Filtros de Espectro**
- Seleção visual de bandas no espectro
- Aplicação de múltiplas bandas simultaneamente
- Visualização em tempo real das bandas selecionadas

#### 🔧 **Filtros Tradicionais**
- **Passa-Baixa**: Remove frequências acima do corte
- **Passa-Alta**: Remove frequências abaixo do corte  
- **Passa-Banda**: Mantém apenas faixa específica
- **Rejeita-Banda (Notch)**: Remove faixa específica
- Ordem configurável (1-10)

## 🎯 Casos de Uso

### 🔍 **Detecção de Vazamentos**
- Transposição de ruídos ultrassônicos de vazamentos
- Filtros para isolar frequências características
- Análise temporal de padrões de vazamento

### 🦇 **Análise Bioacústica**
- Estudo de vocalizações de morcegos e golfinhos
- Transposição para faixa audível humana
- Preservação de características temporais

### 🏭 **Monitoramento Industrial**
- Detecção de falhas em máquinas rotativas
- Análise de descargas parciais em equipamentos elétricos
- Monitoramento de processos ultrassônicos

### 🔬 **Pesquisa Científica**
- Análise de sinais ultrassônicos diversos
- Desenvolvimento de algoritmos de processamento
- Validação de sensores ultrassônicos

## 🛠️ Como Usar

### **Passo 1: Carregar Dados**
1. Abra a aba "Ultra-Hear"
2. Clique em "Selecionar Arquivo"
3. Escolha um arquivo `.pkl` com dados demodulados

### **Passo 2: Configurar Filtros**
1. Escolha o modo de seleção:
   - **Manual**: Digite frequências min/max
   - **Interativo**: Clique em "Ativar Seleção" e arraste no espectro
   - **Pré-definido**: Usa bandas otimizadas automaticamente

### **Passo 3: Configurar Transposição**
1. Marque "Ativar Transposição"
2. Escolha o método desejado
3. Configure parâmetros específicos:
   - **Fator de Divisão**: Para divisão de frequência
   - **Frequência Alvo**: Para heterodino e AM
   - **Manter Velocidade**: Para preservar tempo de reprodução

### **Passo 4: Ajustar Amplitude**
1. Defina faixas de amplitude (dB)
2. Escolha tipo de normalização
3. Ajuste ganho se necessário

### **Passo 5: Processar e Ouvir**
1. Clique em "🔄 Processar Áudio"
2. Aguarde o processamento
3. Clique em "🔊 Reproduzir" para ouvir o resultado

## 📊 Visualizações

### **Espectro Original**
- Mostra espectro completo do sinal
- Permite seleção interativa de bandas
- Escala logarítmica para melhor visualização

### **Espectro Filtrado**
- Exibe resultado após aplicação dos filtros
- Destaca bandas selecionadas
- Comparação com espectro original

### **Sinal Processado**
- Visualiza forma de onda final
- Informações de processamento
- Eixo temporal ajustado

## ⚙️ Parâmetros Técnicos

### **Frequências Suportadas**
- **Entrada**: Até taxa de Nyquist do sinal original
- **Saída**: 44.1 kHz (padrão de áudio)
- **Faixa Ultrassônica**: 20 kHz - 1 MHz+

### **Formatos de Arquivo**
- **Entrada**: Arquivos `.pkl` com dados demodulados
- **Saída**: Arquivos `.wav` 16-bit PCM
- **Nomenclatura**: `ultra_hear_YYYYMMDD_HHMMSS.wav`

### **Algoritmos Implementados**
- **FFT**: Transformada rápida de Fourier para análise espectral
- **Filtros IIR**: Butterworth para filtros tradicionais
- **Reamostragem**: Scipy.signal.resample para alta qualidade
- **Hilbert**: Transformada para extração de envelope

## 🔧 Arquitetura do Sistema

### **Componentes Principais**
```
Ultra-Hear System
├── UltraHearPanel (Interface)
│   ├── Controles de Arquivo
│   ├── Filtros de Frequência  
│   ├── Transposição
│   ├── Controle de Amplitude
│   └── Visualizações
├── UltraHearController (Lógica)
│   ├── Carregamento de Dados
│   ├── Filtros de Frequência
│   ├── Algoritmos de Transposição
│   ├── Controle de Amplitude
│   └── Salvamento de Áudio
└── FrequencyBandSelector (Seleção Interativa)
    ├── SpanSelector (Matplotlib)
    ├── Gerenciamento de Bandas
    └── Callbacks de Seleção
```

### **Fluxo de Processamento**
```
Dados Originais → Filtros de Frequência → Transposição → Controle de Amplitude → Áudio Final
      ↓                    ↓                   ↓                    ↓              ↓
   Carregamento        FFT/Masking        Algoritmos        Normalização      WAV 16-bit
```

## 🎵 Qualidade de Áudio

### **Características do Áudio Gerado**
- **Taxa de Amostragem**: 44.1 kHz
- **Resolução**: 16-bit PCM
- **Canais**: Mono
- **Normalização**: Automática para -5% do máximo
- **Formato**: WAV padrão

### **Otimizações Implementadas**
- Filtros anti-aliasing automáticos
- Reamostragem de alta qualidade
- Clipping suave para evitar distorção
- Preservação de características espectrais

## 🚀 Funcionalidades Futuras

### **Planejadas para Próximas Versões**
- [ ] Filtros em cascata múltiplos
- [ ] Preview em tempo real
- [ ] Filtros personalizados (FIR)
- [ ] Análise de pitch e harmônicos
- [ ] Exportação de configurações
- [ ] Processamento em lote
- [ ] Análise espectrotemporal avançada

## 📈 Performance

### **Tempos de Processamento Típicos**
- **Arquivo 8M pontos**: ~2-5 segundos
- **Filtros simples**: ~1 segundo
- **Transposição complexa**: ~3-10 segundos
- **Dependente de**: CPU, RAM, complexidade dos filtros

### **Requisitos de Sistema**
- **RAM**: Mínimo 4GB (recomendado 8GB+)
- **CPU**: Qualquer processador moderno
- **Armazenamento**: ~100MB para arquivos temporários
- **Python**: 3.7+ com SciPy, NumPy, PyQt5

## 🎓 Fundamentos Teóricos

### **Transposição de Frequência**
A transposição de frequências ultrassônicas para faixa audível é baseada em princípios de processamento de sinais digitais:

1. **Teorema de Nyquist**: Garante reconstrução sem aliasing
2. **Análise Espectral**: FFT para decomposição em frequências
3. **Modulação**: Técnicas de AM/FM para transposição
4. **Filtragem Digital**: Remoção de componentes indesejadas

### **Preservação de Características**
- **Envelope Temporal**: Mantido através de análise de Hilbert
- **Relações Espectrais**: Preservadas em métodos lineares
- **Informação de Fase**: Considerada em algoritmos avançados

## 📞 Suporte e Contribuições

Para dúvidas, sugestões ou contribuições, consulte a documentação principal do projeto OAS-GUI.

---

**Ultra-Hear** - Transformando o inaudível em perceptível! 🎵🔬 