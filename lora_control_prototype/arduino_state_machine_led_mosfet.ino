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

void setup() {
  Serial.begin(9600);
  delay(2000);
  Serial.println(F("=== INICIALIZAÇÃO ARDUINO ==="));
  Serial.println(F("=== MÁQUINA DE ESTADOS LED+MOSFET ==="));
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
  Serial.println(F("Sistema pronto em modo baixo consumo!"));
}

void loop() {
  // Dorme se não precisa acordar
  if (!acordar) {
    Serial.println(F("Dormindo..."));
    delay(100); // Para garantir que o Serial envie antes de dormir
    dormir();
    // Quando acordar, acordar=true
    Serial.println(F("Acordou!"));
  }
  acordar = false;

  // Processa comandos LoRa
  processarComandos();

  // Mantém o estado do MOSFET/LED
  if (estadoAtual == LIGADO) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    digitalWrite(MOSFET_PIN, HIGH);
  } else {
    digitalWrite(STATUS_LED_PIN, LOW);
    digitalWrite(MOSFET_PIN, LOW);
  }
}

void dormir() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  noInterrupts();
  EIFR = bit(INTF0); // Limpa flag de interrupção externa 0
  interrupts();
  sleep_cpu();
  sleep_disable();
}

void wakeUp() {
  acordar = true;
}

void processarComandos() {
  while (loraSerial.available() > 0) {
    char comando = loraSerial.read();
    Serial.print(F("Comando: "));
    Serial.println(comando);
    unsigned long agora = millis();
    if (agora - ultimoComando < 1000) continue;
    ultimoComando = agora;
    if (comando == 'L') {
      estadoAtual = LIGADO;
      Serial.println(F("MOSFET/LED ligados, Arduino ficará acordado."));
    } else if (comando == 'D') {
      estadoAtual = DESLIGADO;
      Serial.println(F("MOSFET/LED desligados, Arduino voltará a dormir."));
      delay(200); // Pequeno delay para garantir desligamento
      acordar = false; // Vai dormir no próximo loop
    }
  }
} 