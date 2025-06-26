/*
 * Firmware para Monitoramento de Banco de Baterias Li-ion 3S
 * Medições: Tensão da bateria, corrente da bateria, tensão no resistor de carga
 * Comunicação via Serial para GUI Python
 */

// Definição dos pinos analógicos
const int PIN_TENSAO_BATERIA = A0;    // Tensão da bateria Li-ion 3S (máx ~12.6V)
const int PIN_CORRENTE_BATERIA = A1;  // Tensão no shunt de corrente
const int PIN_TENSAO_RESISTOR = A2;   // Tensão no resistor de carga (5V)

// Constantes de calibração - agora são variáveis com valores padrão
const float VREF = 5.0;               // Tensão de referência do Arduino
float RESISTOR_SHUNT = 1.2;     // Resistência do shunt em ohms (100mΩ)
float RESISTOR_CARGA = 120.0;    // Resistência de carga em ohms
float DIVISOR_TENSAO_BAT = 3.0; // Fator do divisor de tensão (calculado)

// Valores R1 e R2 para cálculo do divisor
float R1_DIVISOR = 20000.0;
float R2_DIVISOR = 10000.0;

// Variáveis para cálculos
float tensaoBateria = 0.0;
float correnteBateria = 0.0;
float tensaoResistor = 0.0;
float correnteResistor = 0.0;
float potenciaBateria = 0.0;
float potenciaResistor = 0.0;
float capacidadeUtilizada = 0.0; // mAh
float energiaTotal = 0.0; // mWh

// Timers
unsigned long tempoAnterior = 0;
const unsigned long INTERVALO_MEDICAO = 1000; // 1 segundo entre medições (reduzido de 100ms)

// Buffer para média móvel
const int NUM_AMOSTRAS = 5; // Reduzido de 10 para 5
float bufferTensaoBat[NUM_AMOSTRAS];
float bufferCorrenteBat[NUM_AMOSTRAS];
float bufferTensaoRes[NUM_AMOSTRAS];
int indiceBuffer = 0;

void setup() {
  // Inicialização da comunicação serial
  Serial.begin(115200);
  
  // Calcular fator do divisor de tensão inicial
  if (R2_DIVISOR > 0) {
    DIVISOR_TENSAO_BAT = (R1_DIVISOR + R2_DIVISOR) / R2_DIVISOR;
  }
  
  // Configuração dos pinos analógicos
  analogReference(DEFAULT);
  
  // Inicializar buffers
  for (int i = 0; i < NUM_AMOSTRAS; i++) {
    bufferTensaoBat[i] = 0.0;
    bufferCorrenteBat[i] = 0.0;
    bufferTensaoRes[i] = 0.0;
  }
  
  // Aguarda estabilização
  delay(1000);
  
  Serial.println("SISTEMA_MONITORAMENTO_BATERIA_INICIADO");
}

void loop() {
  unsigned long tempoAtual = millis();
  
  // Verificar se há comandos da GUI
  verificarComandosSerial();
  
  // Medições a cada 1 segundo
  if (tempoAtual - tempoAnterior >= INTERVALO_MEDICAO) {
    tempoAnterior = tempoAtual;
    
    // Realizar medições
    realizarMedicoes();
    
    // Calcular parâmetros
    calcularParametros();
    
    // Enviar dados via serial
    enviarDados();
  }
}

void realizarMedicoes() {
  // Fazer uma única leitura por canal (reduzido de 10 para 1)
  float leituraTensaoBat = analogRead(PIN_TENSAO_BATERIA);
  float leituraCorrenteBat = analogRead(PIN_CORRENTE_BATERIA);
  float leituraTensaoRes = analogRead(PIN_TENSAO_RESISTOR);
  
  // Adicionar ao buffer de média móvel
  bufferTensaoBat[indiceBuffer] = leituraTensaoBat;
  bufferCorrenteBat[indiceBuffer] = leituraCorrenteBat;
  bufferTensaoRes[indiceBuffer] = leituraTensaoRes;
  
  // Avançar índice do buffer
  indiceBuffer = (indiceBuffer + 1) % NUM_AMOSTRAS;
  
  // Calcular médias
  float mediaTensaoBat = 0;
  float mediaCorrenteBat = 0;
  float mediaTensaoRes = 0;
  
  for (int i = 0; i < NUM_AMOSTRAS; i++) {
    mediaTensaoBat += bufferTensaoBat[i];
    mediaCorrenteBat += bufferCorrenteBat[i];
    mediaTensaoRes += bufferTensaoRes[i];
  }
  
  mediaTensaoBat /= NUM_AMOSTRAS;
  mediaCorrenteBat /= NUM_AMOSTRAS;
  mediaTensaoRes /= NUM_AMOSTRAS;
  
  // Converter leituras analógicas para tensões
  tensaoBateria = mediaTensaoBat * (VREF / 1023.0) * DIVISOR_TENSAO_BAT;
  float tensaoShunt = mediaCorrenteBat * (VREF / 1023.0);
  tensaoResistor = mediaTensaoRes * (VREF / 1023.0);
  
  // Calcular corrente da bateria (Lei de Ohm no shunt)
  correnteBateria = tensaoShunt / RESISTOR_SHUNT;
  
  // Calcular corrente no resistor de carga
  correnteResistor = tensaoResistor / RESISTOR_CARGA;
}

void calcularParametros() {
  // Calcular potências
  potenciaBateria = tensaoBateria * correnteBateria;
  potenciaResistor = tensaoResistor * correnteResistor;
  
  // Calcular capacidade utilizada (integração da corrente)
  float deltaTempo = INTERVALO_MEDICAO / 1000.0; // Converter para segundos
  capacidadeUtilizada += (correnteBateria * deltaTempo * 1000.0); // mAh
  
  // Calcular energia total
  energiaTotal += (potenciaBateria * deltaTempo * 1000.0); // mWh
}

void enviarDados() {
  // Formato: TEMPO,TENSAO_BAT,CORRENTE_BAT,TENSAO_RES,CORRENTE_RES,POTENCIA_BAT,POTENCIA_RES,CAPACIDADE,ENERGIA
  Serial.print(millis());
  Serial.print(",");
  Serial.print(tensaoBateria, 3);
  Serial.print(",");
  Serial.print(correnteBateria, 3);
  Serial.print(",");
  Serial.print(tensaoResistor, 3);
  Serial.print(",");
  Serial.print(correnteResistor, 3);
  Serial.print(",");
  Serial.print(potenciaBateria, 3);
  Serial.print(",");
  Serial.print(potenciaResistor, 3);
  Serial.print(",");
  Serial.print(capacidadeUtilizada, 2);
  Serial.print(",");
  Serial.println(energiaTotal, 2);
}

void verificarComandosSerial() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando.startsWith("RESET")) {
      resetarContadores();
    } else if (comando.startsWith("CONFIG")) {
      parseConfigComando(comando);
    }
  }
}

void parseConfigComando(String comando) {
  // Converte String para char array para usar strtok
  char buf[100];
  comando.toCharArray(buf, sizeof(buf));

  char* part = strtok(buf, ","); // part é "CONFIG"
  
  part = strtok(NULL, ",");
  if (part) RESISTOR_CARGA = atof(part);
  
  part = strtok(NULL, ",");
  if (part) RESISTOR_SHUNT = atof(part);
  
  part = strtok(NULL, ",");
  if (part) R1_DIVISOR = atof(part);
  
  part = strtok(NULL, ",");
  if (part) R2_DIVISOR = atof(part);
  
  // Recalcular o fator do divisor de tensão
  if (R2_DIVISOR > 0) {
    DIVISOR_TENSAO_BAT = (R1_DIVISOR + R2_DIVISOR) / R2_DIVISOR;
  }
  
  Serial.println("CONFIG_OK");
}

// Função para resetar contadores (chamada via serial)
void resetarContadores() {
  capacidadeUtilizada = 0.0;
  energiaTotal = 0.0;
  Serial.println("CONTADORES_RESETADOS");
}

// Função para calibrar sensores (chamada via serial)
void calibrarSensores() {
  Serial.println("CALIBRACAO_INICIADA");
  // Aqui você pode adicionar rotinas de calibração específicas
  Serial.println("CALIBRACAO_CONCLUIDA");
} 