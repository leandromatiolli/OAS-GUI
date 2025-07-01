/*
  ========================================
  SISTEMA DE CONTROLE LoRa - VERSÃO FINAL
  ========================================
  
  Sistema de controle remoto via LoRa com modo de baixo consumo.
  
  FUNCIONAMENTO:
  - Arduino e LoRa ficam em modo sleep (baixo consumo)
  - Comando 'L' acorda o Arduino, liga MOSFET/LED e mantém acordado
  - Comando 'D' desliga MOSFET/LED e volta a dormir
  - Interrupção no pino AUX (D2) acorda o Arduino
  
  CONEXÕES:
  - LoRa M0   -> Arduino D3
  - LoRa M1   -> Arduino D4  
  - LoRa RXD  -> Arduino D11 (TX)
  - LoRa TXD  -> Arduino D10 (RX)
  - LoRa AUX  -> Arduino D2 (INTERRUPÇÃO - CRÍTICO!)
  - LoRa VCC  -> 3.3V
  - LoRa GND  -> GND
  - MOSFET Gate -> Arduino D7
  - LED Status -> Arduino D13 (embutido)
  
  COMANDOS:
  - 'L' = Ligar equipamento (MOSFET HIGH, LED HIGH)
  - 'D' = Desligar equipamento (MOSFET LOW, LED LOW) e dormir
  
  AUTOR: Sistema desenvolvido para controle remoto LoRa
  DATA: 2024
  VERSÃO: 1.0 FINAL
*/

#include <avr/sleep.h>
#include <avr/power.h>
#include <SoftwareSerial.h>

// ========================================
// CONFIGURAÇÃO DE PINOS
// ========================================
const int LORA_RX_PIN = 10;      // Conectado ao TXD do LoRa
const int LORA_TX_PIN = 11;      // Conectado ao RXD do LoRa
const int LORA_M0_PIN = 3;       // Modo LoRa
const int LORA_M1_PIN = 4;       // Modo LoRa
const int LORA_AUX_PIN = 2;      // Interrupção externa - CRÍTICO!
const int STATUS_LED_PIN = LED_BUILTIN;  // LED embutido (D13)
const int MOSFET_PIN = 7;        // Controle do MOSFET

// ========================================
// OBJETOS E VARIÁVEIS
// ========================================
SoftwareSerial loraSerial(LORA_RX_PIN, LORA_TX_PIN);

// Estados do sistema
enum EstadoSistema { 
  DESLIGADO, 
  LIGADO 
};

// Variáveis de controle
volatile bool acordar = false;           // Flag para acordar do sleep
EstadoSistema estadoAtual = DESLIGADO;   // Estado atual do equipamento
unsigned long ultimoComando = 0;         // Timestamp do último comando
bool deveDormir = false;                 // Flag para voltar a dormir

// ========================================
// CONFIGURAÇÃO INICIAL
// ========================================
void setup() {
  // Inicializa comunicação serial com PC
  Serial.begin(9600);
  delay(2000);
  
  Serial.println(F("========================================"));
  Serial.println(F("SISTEMA DE CONTROLE LoRa - VERSÃO FINAL"));
  Serial.println(F("========================================"));
  Serial.println(F(""));
  
  // Configura pinos de saída
  pinMode(LORA_M0_PIN, OUTPUT);
  pinMode(LORA_M1_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(MOSFET_PIN, OUTPUT);
  
  // Estado inicial - tudo desligado
  digitalWrite(LORA_M0_PIN, LOW);
  digitalWrite(LORA_M1_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(MOSFET_PIN, LOW);
  estadoAtual = DESLIGADO;
  
  // Configura pino AUX para interrupção
  pinMode(LORA_AUX_PIN, INPUT_PULLUP);
  
  // Inicializa comunicação LoRa
  loraSerial.begin(9600);
  
  // Configura interrupção externa no pino D2 (AUX)
  attachInterrupt(digitalPinToInterrupt(LORA_AUX_PIN), wakeUp, FALLING);
  
  Serial.println(F("✓ Sistema inicializado"));
  Serial.println(F("✓ Interrupção AUX configurada"));
  Serial.println(F("✓ LoRa em modo operação"));
  Serial.println(F(""));
  Serial.println(F("COMANDOS DISPONÍVEIS:"));
  Serial.println(F("  'L' = Ligar equipamento"));
  Serial.println(F("  'D' = Desligar equipamento e dormir"));
  Serial.println(F(""));
  Serial.println(F("Sistema pronto! Entrando em modo sleep..."));
  Serial.println(F("========================================"));
  
  delay(100);
  dormir(); // Entra em modo sleep imediatamente
}

// ========================================
// LOOP PRINCIPAL
// ========================================
void loop() {
  // Verifica se deve acordar
  if (acordar) {
    Serial.println(F("🔔 ACORDOU! Processando comando..."));
    acordar = false;
    
    // Aguarda LoRa processar completamente
    delay(500);
    
    // Processa comandos recebidos
    processarComandos();
    
    // Se deve dormir, volta a dormir imediatamente
    if (deveDormir) {
      Serial.println(F("💤 Voltando a dormir..."));
      delay(200);
      dormir();
    }
  }
  
  // Se não deve dormir, mantém acordado e monitora
  if (!deveDormir) {
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck > 10000) { // Status a cada 10 segundos
      lastCheck = millis();
      Serial.println(F("⏰ Sistema acordado - aguardando comando 'D'..."));
      Serial.print(F("Estado: "));
      Serial.println(estadoAtual == LIGADO ? F("LIGADO") : F("DESLIGADO"));
    }
    
    // Verifica se há novos comandos
    if (loraSerial.available() > 0) {
      processarComandos();
    }
  }
  
  delay(100);
}

// ========================================
// FUNÇÃO DE SLEEP (BAIXO CONSUMO)
// ========================================
void dormir() {
  Serial.println(F("😴 Entrando em modo sleep..."));
  
  // Desliga periféricos para economizar energia
  power_adc_disable();    // Conversor A/D
  power_spi_disable();    // Interface SPI
  power_timer0_disable(); // Timer 0
  power_timer1_disable(); // Timer 1
  power_timer2_disable(); // Timer 2
  power_twi_disable();    // Interface I2C
  
  // Configura modo de sleep mais profundo
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  
  // Limpa flags de interrupção
  noInterrupts();
  EIFR = bit(INTF0); // Limpa flag de interrupção externa 0 (pino D2)
  interrupts();
  
  // Entra em modo sleep
  sleep_cpu();
  
  // Acorda aqui (quando AUX vai para LOW)
  sleep_disable();
  
  // Reativa periféricos
  power_adc_enable();
  power_spi_enable();
  power_timer0_enable();
  power_timer1_enable();
  power_timer2_enable();
  power_twi_enable();
  
  Serial.println(F("🌅 Acordou!"));
}

// ========================================
// INTERRUPÇÃO - ACORDA O ARDUINO
// ========================================
void wakeUp() {
  acordar = true;
}

// ========================================
// PROCESSAMENTO DE COMANDOS
// ========================================
void processarComandos() {
  while (loraSerial.available() > 0) {
    char comando = loraSerial.read();
    
    Serial.print(F("📨 Comando recebido: 0x"));
    Serial.print(comando, HEX);
    Serial.print(F(" ('"));
    Serial.print(comando);
    Serial.println(F("')"));
    
    // Anti-duplicação - evita comandos muito próximos
    unsigned long agora = millis();
    if (agora - ultimoComando < 300) {
      Serial.println(F("⚠️ Comando ignorado - muito próximo"));
      continue;
    }
    ultimoComando = agora;
    
    // Processa comando LIGAR
    if (comando == 'L') {
      Serial.println(F("🟢 COMANDO LIGAR"));
      
      if (estadoAtual == DESLIGADO) {
        estadoAtual = LIGADO;
        digitalWrite(STATUS_LED_PIN, HIGH);
        digitalWrite(MOSFET_PIN, HIGH);
        deveDormir = false; // Fica acordado
        
        Serial.println(F("✅ MOSFET e LED LIGADOS"));
        Serial.println(F("💡 Sistema ficará acordado até comando 'D'"));
        
        loraSerial.println(F("ACK_LIGA"));
      } else {
        Serial.println(F("⚠️ Já estava ligado"));
      }
    }
    // Processa comando DESLIGAR
    else if (comando == 'D') {
      Serial.println(F("🔴 COMANDO DESLIGAR"));
      
      if (estadoAtual == LIGADO) {
        estadoAtual = DESLIGADO;
        digitalWrite(STATUS_LED_PIN, LOW);
        digitalWrite(MOSFET_PIN, LOW);
        deveDormir = true; // Vai dormir
        
        Serial.println(F("✅ MOSFET e LED DESLIGADOS"));
        Serial.println(F("💤 Sistema voltará a dormir"));
        
        loraSerial.println(F("ACK_DESLIGA"));
        
        // Delay para garantir que o ACK seja enviado
        delay(150);
      } else {
        Serial.println(F("⚠️ Já estava desligado"));
        deveDormir = true; // Vai dormir mesmo assim
      }
    }
    // Comando desconhecido
    else {
      Serial.print(F("❓ Comando desconhecido: "));
      Serial.println(comando);
    }
  }
}

/*
  ========================================
  INFORMAÇÕES TÉCNICAS
  ========================================
  
  CONSUMO DE ENERGIA:
  - Modo sleep: ~0.1mA (muito baixo)
  - Modo acordado: ~20-30mA (normal)
  
  TEMPO DE RESPOSTA:
  - Acordar do sleep: ~1-2ms
  - Processar comando: ~500ms
  - Voltar a dormir: ~200ms
  
  CONFIGURAÇÃO LoRa E220:
  - M0 = LOW, M1 = LOW (modo operação)
  - Baud rate: 9600
  - Frequência: 915MHz (padrão)
  
  TROUBLESHOOTING:
  - Se não acordar: verificar conexão AUX -> D2
  - Se não receber comandos: verificar baud rate
  - Se resetar: verificar alimentação do MOSFET
  
  ========================================
  FIM DO CÓDIGO
  ========================================
*/ 