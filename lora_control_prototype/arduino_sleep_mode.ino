#include <avr/sleep.h>
#include <avr/power.h>
#include <SoftwareSerial.h>

const int LORA_RX_PIN = 10;
const int LORA_TX_PIN = 11;
const int LORA_M0_PIN = 3;
const int LORA_M1_PIN = 4;
const int LORA_AUX_PIN = 2; // Interrupção externa 0
const int STATUS_LED_PIN = LED_BUILTIN;
const int MOSFET_PIN = 7;

SoftwareSerial loraSerial(LORA_RX_PIN, LORA_TX_PIN);

enum EstadoSistema { DESLIGADO, LIGADO };
volatile bool acordar = false;
EstadoSistema estadoAtual = DESLIGADO;
unsigned long ultimoComando = 0;
bool deveDormir = false;

void setup() {
  Serial.begin(9600);
  delay(2000);
  Serial.println(F("=== SISTEMA DE BAIXO CONSUMO ==="));
  
  pinMode(LORA_M0_PIN, OUTPUT);
  pinMode(LORA_M1_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(MOSFET_PIN, OUTPUT);
  digitalWrite(LORA_M0_PIN, LOW);
  digitalWrite(LORA_M1_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(MOSFET_PIN, LOW);
  estadoAtual = DESLIGADO;
  
  pinMode(LORA_AUX_PIN, INPUT_PULLUP);
  loraSerial.begin(9600);
  attachInterrupt(digitalPinToInterrupt(LORA_AUX_PIN), wakeUp, FALLING);
  
  Serial.println(F("Sistema pronto! Dormindo..."));
  delay(100);
  dormir();
}

void loop() {
  if (acordar) {
    Serial.println(F("🔔 ACORDOU! Processando comando..."));
    acordar = false;
    
    // Aguarda mais tempo para o LoRa processar completamente
    delay(500);
    
    // Processa comandos
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
    if (millis() - lastCheck > 5000) {
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

void dormir() {
  Serial.println(F("😴 Entrando em modo sleep..."));
  
  // Desliga periféricos para economizar energia
  power_adc_disable();
  power_spi_disable();
  power_timer0_disable();
  power_timer1_disable();
  power_timer2_disable();
  power_twi_disable();
  
  // Configura modo de sleep mais profundo
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  
  // Limpa flags de interrupção
  noInterrupts();
  EIFR = bit(INTF0); // Limpa flag de interrupção externa 0
  interrupts();
  
  // Dorme
  sleep_cpu();
  
  // Acorda aqui
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

void wakeUp() {
  acordar = true;
}

void processarComandos() {
  while (loraSerial.available() > 0) {
    char comando = loraSerial.read();
    
    Serial.print(F("📨 Comando recebido: 0x"));
    Serial.print(comando, HEX);
    Serial.print(F(" ('"));
    Serial.print(comando);
    Serial.println(F("')"));
    
    // Anti-duplicação - reduzido para permitir comandos mais frequentes
    unsigned long agora = millis();
    if (agora - ultimoComando < 300) {
      Serial.println(F("⚠️ Comando ignorado - muito próximo"));
      continue;
    }
    ultimoComando = agora;
    
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
        
        // Delay para garantir que o ACK seja enviado completamente
        delay(150);
      } else {
        Serial.println(F("⚠️ Já estava desligado"));
        deveDormir = true; // Vai dormir mesmo assim
      }
    }
    else {
      Serial.print(F("❓ Comando desconhecido: "));
      Serial.println(comando);
    }
  }
} 