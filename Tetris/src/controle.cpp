#include <Arduino.h>

int buttonPin1 = 2;  // Pino do botão 1
int buttonPin2 = 3;  // Pino do botão 2
int buttonPin3 = 4;  // Pino do botão 3
int buttonPin4 = 5;  // Pino do botão 4

int buttonState1 = 0;
int buttonState2 = 0;
int buttonState3 = 0;
int buttonState4 = 0;

int lastButtonState4 = LOW; // Para controle do botão 4
unsigned long lastDebounceTime4 = 0; // Tempo de debounce para o botão 4
int debounceDelay = 50;  // Tempo de debounce (em milissegundos)

void setup() {
  Serial.begin(9600);  // Inicializa a comunicação serial
  pinMode(buttonPin1, INPUT);
  pinMode(buttonPin2, INPUT);
  pinMode(buttonPin3, INPUT);
  pinMode(buttonPin4, INPUT);
}

void loop() {
  unsigned long currentMillis = millis();

  int reading1 = digitalRead(buttonPin1);  // Leitura do botão 1
  int reading2 = digitalRead(buttonPin2);  // Leitura do botão 2
  int reading3 = digitalRead(buttonPin3);  // Leitura do botão 3
  int reading4 = digitalRead(buttonPin4);  // Leitura do botão 4

  // Botão 1: Envia "1" quando pressionado
  if (reading1 == HIGH) {
    if (millis() - lastDebounceTime4 > debounceDelay) {
      Serial.println("1");
      lastDebounceTime4 = millis(); // Atualiza o tempo de debounce
    }
  }

  // Botão 2: Envia "2" quando pressionado
  if (reading2 == HIGH) {
    if (millis() - lastDebounceTime4 > debounceDelay) {
      Serial.println("2");
      lastDebounceTime4 = millis(); // Atualiza o tempo de debounce
    }
  }

  // Botão 3: Envia "3" quando pressionado
  if (reading3 == HIGH) {
    if (millis() - lastDebounceTime4 > debounceDelay) {
      Serial.println("3");
      lastDebounceTime4 = millis(); // Atualiza o tempo de debounce
    }
  }

  // Botão 4: Envia "4" apenas uma vez ao ser pressionado
  if (reading4 == HIGH && lastButtonState4 == LOW) {
    if (millis() - lastDebounceTime4 > debounceDelay) {
      Serial.println("4");
      lastDebounceTime4 = millis(); // Atualiza o tempo de debounce
    }
  }

  lastButtonState4 = reading4; // Atualiza o estado anterior do botão 4
}
