// Define o pino analógico que será utilizado para a leitura de tensão.
const int pinoAnalogico = A0;

void setup() {
  // Inicia a comunicação serial a uma taxa de 9600 bits por segundo.
  // Certifique-se de que a mesma taxa seja usada no programa Python.
  Serial.begin(9600);
}

void loop() {
  // Lê o valor do pino analógico (um número entre 0 e 1023).
  int valorADC = analogRead(pinoAnalogico);
  
  // Envia o valor lido pela porta serial.
  Serial.println(valorADC);
  
  // Aguarda 1 segundo (1000 milissegundos) antes da próxima leitura.
  delay(10000);
} 