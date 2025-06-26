# Sistema de Monitoramento de Banco de Baterias Li-ion 3S

Este sistema permite monitorar em tempo real o consumo de um banco de baterias Li-ion 3S, incluindo medições de tensão, corrente, potência e capacidade utilizada.

## Componentes do Sistema

### Hardware Necessário
- Arduino Uno
- Resistor shunt de 100mΩ para medição de corrente
- Divisor de tensão para bateria (12.6V → 5V)
- Resistor de carga de 10Ω
- Regulador de tensão 5V
- Banco de baterias Li-ion 3S

### Conexões do Arduino
- **Pino A0**: Tensão da bateria (após divisor de tensão)
- **Pino A1**: Tensão no shunt de corrente
- **Pino A2**: Tensão no resistor de carga

## Instalação

### 1. Firmware Arduino
1. Abra o arquivo `arduino_firmware.ino` no Arduino IDE
2. Conecte o Arduino Uno via USB
3. Selecione a porta correta no Arduino IDE
4. Faça upload do firmware

### 2. GUI Python
1. Instale Python 3.7 ou superior
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### 1. Executar a GUI
```bash
python monitor_bateria_gui.py
```

### 2. Configuração
1. Selecione a porta serial onde o Arduino está conectado
2. Clique em "Conectar"
3. Configure a capacidade total da bateria (mAh) e tensão nominal (V)
4. Clique em "Aplicar"

### 3. Monitoramento
- Os valores atuais são exibidos em tempo real
- Os gráficos são atualizados automaticamente
- Use "Iniciar Gravação" para salvar os dados em CSV
- Use "Reset Contadores" para zerar os acumuladores

## Funcionalidades

### Medições Realizadas
- **Tensão da Bateria**: Medida através de divisor de tensão
- **Corrente da Bateria**: Calculada através da queda de tensão no shunt
- **Tensão no Resistor**: Medida diretamente no resistor de carga
- **Corrente no Resistor**: Calculada pela Lei de Ohm
- **Potência da Bateria**: Produto da tensão e corrente da bateria
- **Potência no Resistor**: Produto da tensão e corrente no resistor
- **Capacidade Utilizada**: Integração da corrente ao longo do tempo
- **Energia Total**: Integração da potência ao longo do tempo

### Gráficos em Tempo Real
1. **Gráfico 1**: Tensão, corrente e potência da bateria
2. **Gráfico 2**: Capacidade utilizada vs. tempo

### Gravação de Dados
- Os dados são salvos em formato CSV
- Inclui timestamp, todas as medições e cálculos
- Arquivo pode ser aberto em Excel ou outros programas

## Calibração

### Divisor de Tensão para Bateria
Para medir até 12.6V com entrada de 5V:
```
R1 = 2 * R2
Vout = Vin * R2 / (R1 + R2)
```

### Shunt de Corrente
Resistência de 100mΩ para medição de corrente:
```
I = Vshunt / Rshunt
```

### Resistor de Carga
Resistência de 10Ω para dissipar potência:
```
I = V / R
P = V * I
```

## Configurações Ajustáveis

### No Firmware (arduino_firmware.ino)
- `RESISTOR_SHUNT`: Resistência do shunt (ohms)
- `RESISTOR_CARGA`: Resistência de carga (ohms)
- `DIVISOR_TENSAO_BAT`: Relação do divisor de tensão
- `INTERVALO_MEDICAO`: Intervalo entre medições (ms)

### Na GUI (monitor_bateria_gui.py)
- Capacidade total da bateria (mAh)
- Tensão nominal da bateria (V)
- Número de pontos nos gráficos
- Intervalo de atualização dos gráficos

## Segurança

⚠️ **ATENÇÃO**: 
- Sempre desconecte a alimentação antes de fazer modificações
- Verifique todas as conexões antes de energizar
- Monitore a temperatura dos componentes
- Não exceda os limites de tensão e corrente dos componentes

## Solução de Problemas

### Arduino não conecta
- Verifique se a porta está correta
- Teste a comunicação com o Monitor Serial do Arduino IDE
- Verifique se o firmware foi carregado corretamente

### Medições incorretas
- Calibre os divisores de tensão
- Verifique as resistências dos shunts
- Ajuste as constantes no firmware

### GUI não responde
- Verifique se todas as dependências estão instaladas
- Reinicie a aplicação
- Verifique se o Arduino está enviando dados

## Especificações Técnicas

- **Tensão de Alimentação**: 5V (USB)
- **Resolução ADC**: 10 bits (0-1023)
- **Taxa de Amostragem**: 10 Hz
- **Precisão**: ±1% (depende da calibração)
- **Formato de Dados**: CSV
- **Interface**: Tkinter (GUI nativa)

## Licença

Este projeto é de código aberto e pode ser modificado conforme necessário. 