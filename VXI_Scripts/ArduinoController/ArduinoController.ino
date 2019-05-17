
#define ReadTrig 20
#define VMcomplete 35 
#define IMcomplete 36
#define Power 29
#define FET1 27
#define PressurePin 8
#define ledPin 13 //builtin LED

enum State : uint8_t { STAND_BY = 1, INIT, RUN, SEND_DATA, BALANCE };
State THW = STAND_BY;

char rx_byte;
elapsedMicros Timer;
const unsigned int PowerTimeStart = 40000; //10ms
const unsigned int PowerTime = 1000000; //2s
const unsigned int numReadings = 1000;
unsigned int VMtime[numReadings];
unsigned int IMtime[numReadings];
unsigned int VMcounter;
unsigned int IMcounter;
volatile int VMTrigCheck = 0;
volatile int IMTrigCheck = 0;
int PowerCheck = 0;

float Voltage;
float Signal;
float Pressure;

void setup() {
  Serial.begin(9600);
  pinMode(ReadTrig, OUTPUT);
  pinMode(Power, OUTPUT);
  pinMode(VMcomplete, INPUT);
  pinMode(IMcomplete, INPUT);
  attachInterrupt(VMcomplete, ISR_VMTrigTiming, FALLING);
  attachInterrupt(IMcomplete, ISR_IMTrigTiming, FALLING);
}

void loop() {

  if (Serial.available() > 0) {
    rx_byte = Serial.read();
    Serial.clear();

  if ((rx_byte == '0')) {
      THW = STAND_BY;
   }else if ((rx_byte == '1')) {
      THW = INIT;
   }else if ((rx_byte == '2')) {
      THW = SEND_DATA;
   }else if ((rx_byte == '3')) {
      THW = BALANCE;
   }else {
      Serial.print(rx_byte);
      Serial.println(" is not a valid command.");
   }
  }

   switch(THW){
    case STAND_BY:
      digitalWrite(ledPin, HIGH);
      digitalWrite(ReadTrig, HIGH);
      digitalWrite(Power, LOW);
      digitalWrite(FET1, HIGH);
      break;
    case INIT:
      PowerCheck = 0;
      VMTrigCheck = 0;
      IMTrigCheck = 0;
      VMcounter = 0;
      IMcounter = 0;
      Timer = 0;
      THW = RUN;
      //No break, just carry on with the run!
    case RUN: //Also running while in start mode.
      if (Timer <= (PowerTime + PowerTimeStart)){
        digitalWrite(ReadTrig, LOW);
        digitalWrite(ledPin, LOW);
        if (Timer >= PowerTimeStart){
          digitalWrite(FET1, LOW);
          digitalWrite(Power, HIGH);
        }
      } else if (Timer > (PowerTime + PowerTimeStart) && PowerCheck == 0){
        Serial.println("Break");
        digitalWrite(Power, LOW);
        PowerCheck = 1;
      }

      if (VMTrigCheck == 1){
        VMtime[VMcounter] = Timer;
        VMTrigCheck = 0;
        VMcounter++;
      } 

      if (IMTrigCheck == 1){
        IMtime[IMcounter] = Timer;
        IMTrigCheck = 0;
        IMcounter++;
      } 

      if (Timer > PowerTime){
        THW = SEND_DATA;
      }
      break;
    case SEND_DATA:
      Serial.println("PowerTimeStart");
      Serial.println(PowerTimeStart);

      Serial.println("PowerTime");
      Serial.println(PowerTime);

      Serial.println("VMReadings");
      Serial.println(VMcounter);

      Serial.println("VMtime");
      for (unsigned int n = 0; n < VMcounter; n++){
        Serial.println(VMtime[n]);
      }

      Serial.println("IMReadings");
      Serial.println(IMcounter);
      Serial.println("IMtime");
      for (unsigned int i = 0; i< IMcounter; i++){
        Serial.println(IMtime[i]);
      }
      
      THW = STAND_BY;
      
      break;
    case BALANCE:
      digitalWrite(Power, HIGH);
      break;
   }
}

void ISR_VMTrigTiming(){
  VMTrigCheck = 1;
}

void ISR_IMTrigTiming(){
  IMTrigCheck = 1;
}
      //Pressure Transducer
      //Serial.println(analogRead(PressurePin));
      //Signal = analogRead(PressurePin);
      //Voltage = (Signal/(1024))*3.3;
      //Serial.println(Voltage);
      //Pressure = ((Voltage/5) - 0.04)/0.0012858;
      //Serial.println(Pressure);
      //delay(200);
      //break;
