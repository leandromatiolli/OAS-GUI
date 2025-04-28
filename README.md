# OAS-GUI

Interface gráfica para aquisição e análise de sinais acústicos para detecção de vazamentos.

## Descrição

O OAS-GUI (Optical Acoustic Sensing Graphical User Interface) é uma aplicação para aquisição, processamento e visualização de sinais acústicos obtidos através de sensores ópticos. O sistema permite a detecção e análise de vazamentos em tubulações através do processamento dos sinais acústicos capturados.

## Características

- Aquisição de dados diretamente de hardware RedPitaya
- Processamento de sinais com demodulação em tempo real
- Análise espectral com detecção automática de picos
- Visualização de dados em diversos formatos (séries temporais, espectros, etc.)
- Armazenamento de metadados para treinamento de modelos de IA
- Interface amigável com visualização em abas

## Requisitos

- Python 3.7+
- PyQt5
- NumPy
- SciPy
- Matplotlib
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

2. Na aba "Metadados", preencha as informações relevantes sobre o experimento:
   - Número de série do sensor
   - Tipo de teste
   - Material da tubulação
   - Posição do sensor
   - Pressão, fluxo e distância do vazamento

3. Clique em "Adquirir Dados" para iniciar a aquisição

### Análise de Dados

1. Na aba "Análise", selecione o arquivo a ser analisado
2. Navegue pelas sub-abas para visualizar diferentes aspectos dos dados:
   - Dados Brutos: Séries temporais dos sinais adquiridos
   - Fit da Elipse: Ajuste de elipse e processamento de fase
   - Sinal Demodulado: Sinal de fase extraído
   - Espectro: Análise espectral do sinal demodulado

## Estrutura do Projeto

O projeto segue uma arquitetura MVC (Model-View-Controller):

- **Models**: Gerenciamento de dados e comunicação com hardware
- **Views**: Interface gráfica e visualização de dados
- **Controllers**: Lógica de negócio e coordenação entre modelos e visualizações

## Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar pull requests ou abrir issues para reportar bugs ou sugerir melhorias.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 