#include <SoftwareSerial.h>

const int LORA_RX_PIN = 10;
const int LORA_TX_PIN = 11;
const int LORA_M0_PIN = 3;
const int LORA_M1_PIN = 4;
const int LORA_AUX_PIN = 2;
const int STATUS_LED_PIN = LED_BUILTIN;
const int MOSFET_PIN = 7;

SoftwareSerial loraSerial(LORA_RX_PIN, LORA_TX_PIN);

enum EstadoSistema { DESLIGADO, LIGADO };
volatile bool auxPulseDetected = false;
volatile int auxPulseCount = 0;
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
  attachInterrupt(digitalPinToInterrupt(LORA_AUX_PIN), onAuxPulse, FALLING);
  Serial.println(F("Sistema pronto!"));
}

void loop() {
  if (auxPulseDetected) {
    Serial.print(F("PULSO #"));
    Serial.println(auxPulseCount);
    delay(100);
    processarComandos();
    auxPulseDetected = false;
  }
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 2000) {
    lastCheck = millis();
    if (loraSerial.available() > 0) {
      Serial.println(F("Dados encontrados!"));
      processarComandos();
    }
  }
  manterEstado();
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 10000) {
    lastStatus = millis();
    Serial.println(F("--- STATUS ---"));
    Serial.print(F("Estado: "));
    Serial.println(estadoAtual == LIGADO ? F("LIGADO") : F("DESLIGADO"));
    Serial.print(F("LED: "));
    Serial.println(digitalRead(STATUS_LED_PIN) ? F("HIGH") : F("LOW"));
    Serial.print(F("MOSFET: "));
    Serial.println(digitalRead(MOSFET_PIN) ? F("HIGH") : F("LOW"));
    Serial.print(F("Pulsos: "));
    Serial.println(auxPulseCount);
    Serial.println(F("--- FIM ---"));
  }
  delay(50);
}

void onAuxPulse() {
  auxPulseCount++;
  auxPulseDetected = true;
}

void manterEstado() {
  if (estadoAtual == LIGADO) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    digitalWrite(MOSFET_PIN, HIGH);
  } else {
    digitalWrite(STATUS_LED_PIN, LOW);
    digitalWrite(MOSFET_PIN, LOW);
  }
}

void processarComandos() {
  while (loraSerial.available() > 0) {
    char comando = loraSerial.read();
    Serial.print(F("Comando: 0x"));
    Serial.print(comando, HEX);
    Serial.print(F(" ('"));
    Serial.print(comando);
    Serial.println(F("')"));
    unsigned long agora = millis();
    if (agora - ultimoComando < 1000) {
      Serial.println(F("IGNORADO - muito próximo"));
      continue;
    }
    if (comando == 'L') {
      Serial.println(F(">>> COMANDO LIGAR"));
      estadoAtual = LIGADO;
      ultimoComando = agora;
      Serial.println(F("=== LED E MOSFET DEVEM FICAR ACESOS ==="));
    } else if (comando == 'D') {
      Serial.println(F(">>> COMANDO DESLIGAR"));
      estadoAtual = DESLIGADO;
      ultimoComando = agora;
      Serial.println(F("=== LED E MOSFET DEVEM FICAR APAGADOS ==="));
    } else {
      Serial.print(F("Comando desconhecido: "));
      Serial.println(comando);
    }
  }
} 