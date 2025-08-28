# Implementação de Variáveis Personalizadas e Timestamp da Internet

## Resumo das Mudanças

A aba Metadados foi atualizada para incluir:
1. **Sistema dinâmico de variáveis personalizadas**, substituindo o sistema anterior de digitação manual de labels em formato JSON
2. **Timestamp preciso da internet** usando servidores NTP para garantir precisão temporal

## Funcionalidades Implementadas

### 1. Sistema de Variáveis Dinâmicas
- **Widget Personalizado**: Criado `VariableInputWidget` para entrada de dados
- **Campos Disponíveis**:
  - **Nome**: Nome da variável personalizada
  - **Valor**: Valor numérico ou textual da variável
  - **Unidade**: Unidade de medida (opcional)

### 2. Interface de Usuário Melhorada
- **Área de Scroll**: Permite múltiplas variáveis sem ocupar muito espaço
- **Botão de Adição**: "+ Adicionar Nova Variável" para incluir mais campos
- **Botão de Remoção**: "X" para remover variáveis individuais
- **Layout Responsivo**: Interface organizada e intuitiva

### 3. Funcionalidades de Persistência
- **Salvamento Automático**: Estado das variáveis é salvo automaticamente
- **Carregamento Automático**: Variáveis são restauradas na próxima execução
- **Compatibilidade**: Mantém compatibilidade com o sistema anterior

### 4. Timestamp Preciso da Internet
- **Sincronização NTP**: Usa servidores NTP públicos para obter tempo preciso
- **Fallback Inteligente**: Se a internet falhar, usa tempo local com offset calculado
- **Múltiplos Formatos**: Suporte a diferentes formatos de timestamp
- **Timezone UTC**: Todos os timestamps são em UTC para consistência

## Como Usar

### Adicionando Variáveis
1. Na aba Metadados, localize a seção "Variáveis Personalizadas"
2. Preencha os campos:
   - **Nome**: Ex: "Temperatura", "RPM", "Pressão_Interna"
   - **Valor**: Ex: "25.3", "1500", "2.5"
   - **Unidade**: Ex: "°C", "rpm", "bar"
3. Clique em "+ Adicionar Nova Variável" para adicionar mais campos

### Removendo Variáveis
- Clique no botão "X" ao lado da variável que deseja remover
- Pelo menos uma variável sempre permanece disponível

### Salvamento dos Dados
- As variáveis são automaticamente incluídas nos metadados
- **Timestamp preciso da internet** é incluído automaticamente
- Formato de salvamento:
  ```json
  {
    "Temperatura": "25.3",
    "Temperatura_unit": "°C",
    "RPM": "1500",
    "RPM_unit": "rpm",
    "timestamp": "2025-08-28 18:22:26",
    "timestamp_iso": "2025-08-28T18:22:26.332953+00:00"
  }
  ```

## Arquivos Modificados

### `app/views/panels/metadata_panel.py`
- Adicionada classe `VariableInputWidget`
- Modificado `MetadataPanel` para usar o novo sistema
- Implementados métodos de gerenciamento de variáveis
- Atualizada lógica de salvamento/carregamento
- **Integrado timestamp da internet** nos metadados

### `app/utils/time_utils.py` (NOVO)
- Criado módulo para sincronização de tempo com servidores NTP
- Implementada classe `InternetTimeSync` com fallback inteligente
- Funções de conveniência para diferentes formatos de timestamp

### Outros Arquivos Atualizados
- `app/models/data_store.py`: Timestamp da internet para nomes de arquivo
- `OAS_GUI.py`: Timestamp da internet para metadados e arquivos
- `app/views/panels/log_panel.py`: Timestamp da internet para logs

### Funcionalidades Mantidas
- Todos os campos existentes continuam funcionando
- Sistema de fotos do setup
- Comentários
- Configurações de equipamento
- Seleção de pasta de destino

## Benefícios da Nova Implementação

1. **Usabilidade**: Interface mais intuitiva e fácil de usar
2. **Flexibilidade**: Adição/remoção dinâmica de variáveis
3. **Validação**: Campos específicos para cada tipo de dado
4. **Organização**: Melhor estrutura visual dos dados
5. **Persistência**: Salvamento automático do estado
6. **Escalabilidade**: Suporte a múltiplas variáveis
7. **Precisão Temporal**: Timestamp preciso da internet via NTP
8. **Confiabilidade**: Fallback inteligente em caso de falha de conectividade

## Compatibilidade

- **Retrocompatibilidade**: Dados salvos anteriormente ainda são carregados
- **Formato de Saída**: Mantém o mesmo formato nos metadados finais
- **Integração**: Funciona perfeitamente com o sistema de aquisição existente

## Teste da Implementação

### Variáveis Personalizadas
Execute o script de teste para verificar a funcionalidade:
```bash
python test_metadata_panel.py
```

Este script abre uma janela de teste com o painel de metadados para verificação das funcionalidades implementadas.

### Timestamp da Internet
A funcionalidade de timestamp da internet foi testada e está funcionando corretamente:
- ✅ Conectividade com servidores NTP
- ✅ Fallback para tempo local em caso de falha
- ✅ Múltiplos formatos de timestamp
- ✅ Integração com metadados e nomes de arquivo

**Servidores NTP utilizados:**
- pool.ntp.org
- time.google.com
- time.windows.com
- time.apple.com
- time.cloudflare.com
- time.nist.gov
