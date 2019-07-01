
#define ReadTrig 20
#define VMcomplete 35 
#define IMcomplete 36
#define Power 29
#define FET1 27
#define PressurePin 8
#define ledPin 13 //builtin LED

enum State : uint8_t { STAND_BY = 1, IDLE_MODE, WIRE_ON, INIT, RUN, SEND_VDATA, SEND_IDATA, BALANCE };
State THW = STAND_BY;

char rx_byte;

//Microsecond times for events
const unsigned long PowerTimeStart = 1000;
const unsigned long PowerTime = 10000000;

//Number of readings to take
const unsigned long numReadings = 10000;

unsigned long VMtime[numReadings];
unsigned long IMtime[numReadings];
unsigned long VMcounter;
unsigned long IMcounter;

volatile unsigned long runStartMicros;
volatile int VMTrigCheck;
volatile unsigned int VMTrigMicros;
volatile int IMTrigCheck;
volatile unsigned int IMTrigMicros;


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
      THW = SEND_VDATA;
   }else if ((rx_byte == '3')) {
      THW = BALANCE;
   }else if ((rx_byte == '4')) {
      THW = WIRE_ON;
   }else if ((rx_byte == '5')) {
      THW = SEND_IDATA;
   }else {
      Serial.print(rx_byte);
      Serial.println(" is not a valid command.");
   }
  }

   switch(THW){
    case IDLE_MODE:
      break;
    case WIRE_ON:
      digitalWrite(Power, HIGH);
      digitalWrite(FET1, LOW);    
      break;
    case STAND_BY:
      digitalWrite(ledPin, HIGH);
      digitalWrite(ReadTrig, HIGH);
      digitalWrite(Power, LOW);
      digitalWrite(FET1, HIGH);
      THW=IDLE_MODE;
      break;
    case INIT:
      PowerCheck = 0;
      VMTrigCheck = 0;
      IMTrigCheck = 0;
      VMcounter = 0;
      IMcounter = 0;
      THW = RUN;
      runStartMicros = micros();
      //No break, just carry on with the run!
    case RUN: //Also running while in start mode.
    {
      unsigned long currTime = micros() - runStartMicros;
      if (currTime <= (PowerTime + PowerTimeStart)){
        digitalWrite(ReadTrig, LOW);
        digitalWrite(ledPin, LOW);
        if (currTime >= PowerTimeStart){
          digitalWrite(FET1, LOW);
          digitalWrite(Power, HIGH);
        }
      } else if (currTime > (PowerTime + PowerTimeStart) && PowerCheck == 0){
        digitalWrite(Power, LOW);
        PowerCheck = 1;
        Serial.println("Break");
      }

      if (VMTrigCheck == 1){
        VMtime[VMcounter++] = VMTrigMicros - runStartMicros;
        VMTrigCheck = 0;
      } 

      if (IMTrigCheck == 1){
        IMtime[IMcounter++] = IMTrigMicros - runStartMicros;
        IMTrigCheck = 0;
      } 

      if (currTime > PowerTime){
        THW = STAND_BY;
        Serial.println("PowerTimeStart");
        Serial.println(PowerTimeStart);
        Serial.println("PowerTime");
        Serial.println(PowerTime);
      }
      break;
    }
    case SEND_VDATA:
      Serial.println("VMReadings");
      Serial.println(VMcounter);

      Serial.println("VMtime");
      for (unsigned int n = 0; n < VMcounter; n++){
        delay(1); //Delay to allow python time to process (so as to not run out of input buffer)
        Serial.println(VMtime[n]);
      }
      THW = STAND_BY;
      break;
    case SEND_IDATA:
      Serial.println("IMReadings");
      Serial.println(IMcounter);
      Serial.println("IMtime");
      for (unsigned int i = 0; i< IMcounter; i++){
        delay(1); //Delay to allow python time to process (so as to not run out of input buffer)
        Serial.println(IMtime[i]);
      }
      THW = STAND_BY;
      break;
    case BALANCE:
      digitalWrite(Power, HIGH);
      THW=IDLE_MODE;
      break;
   }
}

void ISR_VMTrigTiming(){
  VMTrigMicros = micros();
  VMTrigCheck = 1;
}

void ISR_IMTrigTiming(){
  IMTrigMicros = micros();
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
