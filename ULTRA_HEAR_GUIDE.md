# Guia de Uso - UltraHear

## O que é o UltraHear?

O UltraHear é uma funcionalidade do OAS-GUI que permite ouvir frequências ultrassônicas (acima de 20 kHz) convertendo-as para a faixa audível humana. Isso é útil para detectar vazamentos e outros fenômenos que emitem sons em frequências ultrassônicas.

## Como usar o UltraHear

### 1. Acessar a funcionalidade
- Execute o programa: `python main.py`
- Vá para a aba "Ultra-Hear" (índice 4)

### 2. Selecionar um arquivo
- Clique em "Selecionar Arquivo"
- **IMPORTANTE**: Use apenas arquivos que contenham dados demodulados
- Os arquivos corretos têm "demodulado" no nome
- Exemplo: `vazamento_demodulado_20250827_155206_...pkl`

### 3. Configurar filtros de frequência
- **Modo de Seleção**: Escolha entre:
  - **Seleção Manual**: Define frequência mínima e máxima manualmente
  - **Seleção Interativa**: Clique e arraste no espectro para selecionar bandas
  - **Bandas Pré-definidas**: Usa bandas padrão para ultrassom

- **Frequências recomendadas**:
  - 20-40 kHz: Frequências baixas ultrassônicas
  - 40-80 kHz: Frequências médias ultrassônicas  
  - 80-120 kHz: Frequências altas ultrassônicas

### 4. Configurar transposição de frequência
- **Ativar Transposição**: Marque para converter frequências
- **Método**: Escolha o algoritmo de conversão:
  - **Divisão de Frequência**: Divide as frequências por um fator
  - **Heterodino**: Mistura com frequência local
  - **Modulação AM**: Modula amplitude em frequência audível
  - **Compressão Temporal**: Comprime o tempo do sinal

- **Fator de Divisão**: Recomendado 10-20 para ultrassom
- **Frequência Alvo**: Frequência audível desejada (ex: 1000 Hz)

### 5. Controlar amplitude
- **Amplitude Mín/Máx**: Define faixa de amplitude em dB
- **Normalização**: Escolha método de normalização
- **Ganho**: Ajuste adicional de amplitude

### 6. Processar e reproduzir
- Clique em "🔄 Processar Áudio"
- Aguarde o processamento (pode demorar alguns segundos)
- Clique em "🔊 Reproduzir" para ouvir o resultado

## Arquivos compatíveis

O UltraHear funciona apenas com arquivos que contêm dados demodulados. Estes arquivos têm:
- Chave `'demodulated'` nos dados
- Dados processados prontos para análise de frequência
- Taxa de amostragem efetiva (geralmente 1.953 MHz)

### Arquivos disponíveis no sistema:
```
data/Dados para treinamento/vazamento_demodulado_*.pkl
```

## Interpretação dos resultados

### Espectro Original
- Mostra o espectro de frequência dos dados demodulados
- Linhas vermelhas indicam frequências de referência ultrassônicas
- Picos no espectro indicam sinais presentes

### Espectro Filtrado
- Mostra apenas as frequências selecionadas
- Áreas amarelas destacam as bandas selecionadas

### Sinal Processado
- Mostra o sinal no tempo após processamento
- Útil para verificar a qualidade do processamento

## Dicas de uso

1. **Para detectar vazamentos**:
   - Use bandas de 20-100 kHz
   - Ative transposição com fator 10-20
   - Ouça atentamente por sons característicos

2. **Para análise detalhada**:
   - Use seleção interativa para escolher bandas específicas
   - Experimente diferentes métodos de transposição
   - Ajuste amplitude para melhor audibilidade

3. **Para processamento em lote**:
   - Processe múltiplos arquivos sequencialmente
   - Compare os resultados para identificar padrões

## Solução de problemas

### "Arquivo não contém dados demodulados"
- Use apenas arquivos com "demodulado" no nome
- Verifique se o arquivo foi processado corretamente

### "Erro no processamento"
- Verifique se as frequências estão dentro da faixa válida
- Reduza o fator de divisão se necessário
- Verifique se há memória suficiente

### "Som muito baixo/alto"
- Ajuste o ganho na seção de amplitude
- Experimente diferentes tipos de normalização
- Verifique os limites de amplitude

## Arquivos gerados

O UltraHear gera arquivos WAV com o prefixo `ultra_hear_`:
- `ultra_hear_YYYYMMDD_HHMMSS.wav`
- Taxa de amostragem: 44.1 kHz
- Formato: 16-bit PCM
- Pronto para reprodução em qualquer player de áudio

## Exemplo de uso completo

1. Abra o OAS-GUI
2. Vá para a aba Ultra-Hear
3. Selecione: `vazamento_demodulado_20250827_155206_...pkl`
4. Configure: Frequência 20-100 kHz, Transposição ativada, Fator 10
5. Processe o áudio
6. Reproduza e ouça os sons de vazamento convertidos

O UltraHear transforma sinais ultrassônicos invisíveis em sons audíveis, permitindo detectar vazamentos e outros fenômenos acústicos de alta frequência.
