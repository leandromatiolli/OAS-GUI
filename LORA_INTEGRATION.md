# Integração do Controle LoRa

## Resumo das Mudanças

Este documento descreve a integração dos controles LoRa do arquivo `pc_transmitter_gui.py` na aba de aquisição do programa principal OAS-GUI.

## Arquivos Modificados

### 1. `app/controllers/lora_controller.py` (NOVO)
- **Controlador LoRa**: Implementa a comunicação serial com módulos LoRa
- **Funcionalidades**:
  - Listagem de portas seriais disponíveis
  - Envio de comandos "L" (ligar) e "D" (desligar)
  - Tratamento de respostas ACK
  - Gerenciamento de status do equipamento
  - Logging detalhado das operações

### 2. `app/views/panels/acquisition_panel.py` (MODIFICADO)
- **Novos sinais**:
  - `loraLigarRequested`: Emitido quando usuário solicita ligar equipamento
  - `loraDesligarRequested`: Emitido quando usuário solicita desligar equipamento

- **Novos controles adicionados**:
  - Grupo "Controle Remoto LoRa"
  - Combo box para seleção de porta serial
  - Botão de atualização de portas (↻)
  - Botão "Ligar Equipamento" (verde)
  - Botão "Desligar Equipamento" (vermelho)
  - Label de status do equipamento

- **Novos métodos**:
  - `refresh_lora_ports()`: Atualiza lista de portas
  - `ligar_equipamento_lora()`: Solicita ligar equipamento
  - `desligar_equipamento_lora()`: Solicita desligar equipamento
  - `update_lora_ports()`: Atualiza combo de portas
  - `update_lora_status()`: Atualiza status do equipamento

### 3. `main.py` (MODIFICADO)
- **Importação**: Adicionado `from app.controllers.lora_controller import LoraController`
- **Inicialização**: Criado `self.lora_controller = LoraController()`
- **Conexões de sinais**:
  - Painel → Controlador: comandos de ligar/desligar
  - Controlador → Painel: atualizações de status e erros
- **Novos métodos**:
  - `on_lora_ligar_requested()`: Manipula solicitação de ligar
  - `on_lora_desligar_requested()`: Manipula solicitação de desligar
  - `on_lora_error()`: Manipula erros do LoRa
- **Inicialização**: Lista de portas LoRa carregada na inicialização

### 4. `requirements.txt` (MODIFICADO)
- **Adicionado**: `pyserial>=3.5` para comunicação serial

## Funcionalidades Implementadas

### Controle Remoto via LoRa
1. **Seleção de Porta**: Combo box com todas as portas seriais disponíveis
2. **Atualização de Portas**: Botão para atualizar lista de portas
3. **Ligar Equipamento**: Envia comando "L" e aguarda "ACK_LIGA"
4. **Desligar Equipamento**: Envia comando "D" e aguarda "ACK_DESLIGA"
5. **Status Visual**: Label colorido indicando estado do equipamento
6. **Logging**: Todas as operações são logadas no sistema

### Interface Visual
- **Botão Ligar**: Verde (`lightgreen`)
- **Botão Desligar**: Vermelho (`#ff7f7f`)
- **Status**: 
  - Verde: Equipamento LIGADO
  - Vermelho: Equipamento DESLIGADO
  - Laranja: Status desconhecido

### Tratamento de Erros
- Validação de porta selecionada
- Timeout de 3 segundos para respostas
- **Erros são ignorados**: O sistema assume sucesso mesmo com falhas
- **Sem caixas de diálogo**: Erros são apenas logados, não interrompem o usuário

## Como Usar

1. **Conectar módulo LoRa** via USB
2. **Abrir programa principal**: `python main.py`
3. **Ir para aba de Aquisição**
4. **Selecionar porta serial** do módulo LoRa
5. **Clicar em "Ligar Equipamento"** ou **"Desligar Equipamento"**
6. **Acompanhar status** no label de status

## Compatibilidade

- **Protocolo**: Compatível com o firmware Arduino do `pc_transmitter_gui.py`
- **Comandos**: "L" para ligar, "D" para desligar
- **Respostas**: "ACK_LIGA" e "ACK_DESLIGA"
- **Baud Rate**: 9600 bps
- **Timeout**: 3 segundos

## Observações

- Os comentários de erro do programa original foram mantidos no logging
- A funcionalidade está integrada de forma não-intrusiva na interface existente
- O sistema de logging captura todas as operações para debug
- A interface é responsiva e fornece feedback visual adequado
- **Comportamento tolerante a falhas**: O sistema sempre assume que o comando foi executado com sucesso
- **Sem interrupções**: Não há caixas de diálogo de erro que interrompam o usuário 