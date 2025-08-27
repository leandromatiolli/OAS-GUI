# OAS-GUI

Interface gráfica para aquisição e análise de sinais acústicos para detecção de vazamentos.

## Descrição

O OAS-GUI (Optical Acoustic Sensing Graphical User Interface) é uma aplicação para aquisição, processamento e visualização de sinais acústicos obtidos através de sensores ópticos. O sistema permite a detecção e análise de vazamentos em tubulações através do processamento dos sinais acústicos capturados.

## Características

- Aquisição de dados diretamente de hardware RedPitaya
- Processamento de sinais com demodulação em tempo real
- Análise espectral com detecção automática de picos
- Análise de espectrograma para visualização tempo-frequência
- Análise wavelet para detecção de transientes e padrões
- Visualização de dados em diversos formatos (séries temporais, espectros, etc.)
- Armazenamento de metadados para treinamento de modelos de IA
- Interface amigável com visualização em abas
- Suporte a múltiplos formatos de arquivo para exportação

## Requisitos

- Python 3.7+
- PyQt5
- NumPy
- SciPy
- Matplotlib
- PyWavelets (para análise wavelet)
- Bibliotecas específicas para o hardware RedPitaya (opcional)

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/OAS-GUI.git
   cd OAS-GUI
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Se necessário, instale as bibliotecas específicas para o hardware RedPitaya:
   ```
   pip install redpitaya-scpi
   ```

## Uso

Execute o aplicativo principal:

```
python main.py
```

### Aquisição de Dados

1. Na aba "Aquisição", configure os parâmetros de aquisição:
   - IP do RedPitaya
   - Duração da aquisição
   - Fator de decimação
   - Canais a serem adquiridos
   - Taxa de amostragem

2. Na aba "Metadados", preencha as informações relevantes sobre o experimento:
   - Número de série do sensor
   - Tipo de teste
   - Material da tubulação
   - Localização do sensor
   - Pressão, fluxo e distância do vazamento
   - Fotos do setup (opcional)
   - Comentários adicionais

3. Clique em "Adquirir Dados" para iniciar a aquisição

### Análise de Dados

1. Na aba "Análise", selecione o arquivo a ser analisado
2. Navegue pelas sub-abas para visualizar diferentes aspectos dos dados:

#### Dados Brutos
- Visualização das séries temporais dos sinais adquiridos
- Ajuste de média móvel para suavização
- Visualização da elipse de fase

#### Sinal Demodulado
- Visualização do sinal de fase extraído
- Aplicação de filtro passa-banda
- Configuração de frequências de corte e ordem do filtro

#### Espectro
- Análise espectral do sinal demodulado
- Detecção automática de picos
- Visualização em escala logarítmica

#### Espectrograma
- Análise tempo-frequência do sinal
- Configuração de parâmetros:
  - Tamanho da janela (16-4096 amostras)
  - Sobreposição (0-99%)
  - Frequência máxima
- Visualização em escala de cores

#### Análise Wavelet
- Análise multi-resolução do sinal
- Seleção do tipo de wavelet:
  - Morlet (cmor): Boa para análise de frequência localizada
  - Mexican Hat (mexh): Útil para detecção de transientes
  - Paul: Boa resolução temporal
  - DOG: Análise de gradientes
- Configuração de parâmetros:
  - Número de escalas
  - Frequência máxima
- Visualização do escalograma

## Cuidados e Boas Práticas

1. **Antes da Aquisição**:
   - Verifique a conexão com o RedPitaya
   - Certifique-se de que o sensor está devidamente posicionado
   - Preencha todos os metadados relevantes
   - Faça uma calibração inicial se necessário

2. **Durante a Aquisição**:
   - Monitore os sinais em tempo real
   - Verifique se não há saturação nos canais
   - Mantenha o ambiente o mais silencioso possível

3. **Análise de Dados**:
   - Comece com os dados brutos para verificar a qualidade do sinal
   - Use a média móvel para suavizar ruídos de alta frequência
   - Aplique o filtro passa-banda para isolar a faixa de interesse
   - Utilize o espectrograma para identificar padrões temporais
   - Use a análise wavelet para detectar transientes e anomalias

4. **Exportação de Dados**:
   - Salve os dados processados em formato .pkl
   - Exporte gráficos em alta resolução quando necessário
   - Mantenha um backup dos dados brutos

## Estrutura do Projeto

O projeto segue uma arquitetura MVC (Model-View-Controller):

- **Models**:
  - `data_store.py`: Gerenciamento de dados
  - `hardware/`: Comunicação com hardware RedPitaya
  - `calibration.py`: Gerenciamento de calibração

- **Views**:
  - `main_window.py`: Janela principal
  - `panels/`: Painéis de interface (aquisição, análise, metadados)
  - `plots/`: Visualizações de dados

- **Controllers**:
  - `acquisition_controller.py`: Controle de aquisição
  - `processing_controller.py`: Processamento de sinais
  - `file_controller.py`: Gerenciamento de arquivos

## Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar pull requests ou abrir issues para reportar bugs ou sugerir melhorias.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Funcionamento Interno

### Arquitetura e Fluxo de Dados

O OAS-GUI implementa uma arquitetura robusta baseada no padrão MVC (Model-View-Controller), com comunicação assíncrona entre componentes através do sistema de sinais e slots do PyQt5.

#### Inicialização do Sistema

1. **Criação da Aplicação**:
   - Inicialização do QApplication
   - Configuração do sistema de logging
   - Aplicação de estilos e temas
   - Configuração de hooks para tratamento de exceções

2. **Inicialização dos Controladores**:
   - `AcquisitionController`: Gerencia a comunicação com o hardware
   - `ProcessingController`: Responsável pelo processamento de sinais
   - `FileController`: Gerencia operações de arquivo e persistência

3. **Configuração da Interface**:
   - Criação da janela principal
   - Inicialização dos painéis (Aquisição, Análise, Metadados)
   - Conexão de sinais e slots
   - Carregamento de configurações salvas

#### Fluxo de Aquisição

1. **Preparação**:
   - Validação dos parâmetros de aquisição
   - Verificação da disponibilidade do hardware
   - Coleta de metadados
   - Configuração dos buffers de aquisição

2. **Aquisição**:
   - Inicialização da comunicação com o RedPitaya
   - Configuração dos canais e taxas de amostragem
   - Início da aquisição contínua
   - Monitoramento em tempo real dos sinais
   - Armazenamento em buffer circular

3. **Processamento**:
   - Demodulação em tempo real
   - Aplicação de filtros (se configurado)
   - Cálculo de espectros
   - Atualização das visualizações

4. **Finalização**:
   - Parada da aquisição
   - Salvamento dos dados
   - Atualização da interface
   - Limpeza de recursos

#### Processamento de Sinais

1. **Demodulação**:
   - Extração da fase dos sinais
   - Ajuste da elipse de fase
   - Compensação de desvios
   - Aplicação de calibração

2. **Filtragem**:
   - Média móvel para suavização
   - Filtro passa-banda configurável
   - Remoção de ruído
   - Normalização do sinal

3. **Análise Espectral**:
   - Cálculo da FFT
   - Detecção de picos
   - Cálculo de espectrograma
   - Análise wavelet

#### Gerenciamento de Dados

1. **Estrutura de Dados**:
   ```python
   {
       'waveforms': np.ndarray,  # Dados brutos
       't': np.ndarray,         # Vetor de tempo
       'demodulated': np.ndarray, # Sinal demodulado
       'filtered_demodulated': np.ndarray, # Sinal filtrado
       'spectrum': {
           'freqs': np.ndarray,
           'magnitudes': np.ndarray,
           'peaks': list
       },
       'spectrogram': {
           't': np.ndarray,
           'freqs': np.ndarray,
           'Sxx': np.ndarray
       },
       'wavelet': {
           't': np.ndarray,
           'scales': np.ndarray,
           'coefs': np.ndarray
       },
       'metadata': {
           'sensor_id': str,
           'test_type': str,
           'material': str,
           'location': str,
           'pressure': float,
           'flow': float,
           'distance': float,
           'setup_photos': list,
           'comments': str
       },
       'processing_params': {
           'moving_average': int,
           'bandpass': {
               'enabled': bool,
               'low_freq': float,
               'high_freq': float,
               'order': int
           },
           'spectrogram': {
               'window_size': int,
               'overlap': float,
               'max_freq': float
           },
           'wavelet': {
               'type': str,
               'n_scales': int,
               'max_freq': float
           }
       }
   }
   ```

2. **Persistência**:
   - Salvamento em formato .pkl
   - Compressão de dados
   - Metadados embutidos
   - Versionamento de arquivos

#### Sistema de Eventos

1. **Sinais Principais**:
   ```python
   # Aquisição
   acquisitionStarted = pyqtSignal()
   acquisitionFinished = pyqtSignal(str)
   acquisitionError = pyqtSignal(str)
   
   # Processamento
   demodulationStarted = pyqtSignal()
   demodulationFinished = pyqtSignal(dict)
   demodulationError = pyqtSignal(str)
   
   # Análise
   spectrumCalculated = pyqtSignal(object, object, object)
   spectrogramGenerated = pyqtSignal(dict, object, object, object)
   waveletGenerated = pyqtSignal(dict, object, object, object)
   
   # Arquivos
   fileLoaded = pyqtSignal(dict)
   fileSaved = pyqtSignal(str)
   fileError = pyqtSignal(str)
   ```

2. **Tratamento de Erros**:
   - Exceções capturadas em cada camada
   - Logging detalhado
   - Mensagens de erro amigáveis
   - Recuperação de estado

#### Otimizações

1. **Performance**:
   - Uso de NumPy para operações vetoriais
   - Buffering eficiente de dados
   - Processamento assíncrono
   - Cache de resultados

2. **Memória**:
   - Gerenciamento de buffers
   - Liberação de recursos
   - Compressão de dados
   - Limpeza periódica

3. **Interface**:
   - Atualizações assíncronas
   - Redesenho otimizado
   - Cache de gráficos
   - Threading seguro

### Sequência de Execução Típica

1. **Início do Programa**:
   ```python
   app = QApplication(sys.argv)
   window = MainWindow()
   controllers = init_controllers()
   connect_signals()
   window.show()
   sys.exit(app.exec_())
   ```

2. **Aquisição de Dados**:
   ```python
   # 1. Validação e preparação
   validate_params()
   collect_metadata()
   setup_hardware()
   
   # 2. Aquisição
   start_acquisition()
   while acquiring:
       read_samples()
       process_realtime()
       update_display()
   
   # 3. Finalização
   stop_acquisition()
   save_data()
   update_interface()
   ```

3. **Análise de Dados**:
   ```python
   # 1. Carregamento
   load_file()
   validate_data()
   setup_processing()
   
   # 2. Processamento
   demodulate()
   apply_filters()
   calculate_spectrum()
   generate_spectrogram()
   perform_wavelet_analysis()
   
   # 3. Visualização
   update_plots()
   enable_controls()
   ```

### Considerações de Desenvolvimento

1. **Testes**:
   - Testes unitários para cada componente
   - Testes de integração entre módulos
   - Validação de performance
   - Verificação de memória

2. **Manutenção**:
   - Documentação de código
   - Logging detalhado
   - Tratamento de erros
   - Versionamento

3. **Extensibilidade**:
   - Interfaces bem definidas
   - Plugins para novos processamentos
   - Suporte a diferentes hardwares
   - Formatos de arquivo customizáveis 