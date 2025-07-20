#include <WiFiS3.h>
#include <WiFiUdp.h>
#define READ_PIN(PORT, BIT) (((PORT)->PIDR >> (BIT)) & 0x01)


#define QUEUE_SIZE 50

int queueBuffer[QUEUE_SIZE];
int* queueStart = queueBuffer;
int* queueEnd = queueBuffer + QUEUE_SIZE;
int* head = queueBuffer;  // points to next insertion position
int* tail = queueBuffer;  // points to oldest element
bool queueFull = false;






String ssids[20]; // up to 20 networks
int numNetworks = 0;
IPAddress IPserver=IPAddress(0, 0, 0, 0);
WiFiUDP udp;
const int localPort = 12345;
const int targetPort = 12345;
const char* broadcastIP = "255.255.255.255";


bool work=false;

void setup() {
  Serial.begin(115200);
  while (!Serial);
  scanAndStoreNetworks();
  connectFlow();
  
  pinMode(2,INPUT);

  pinMode(6,INPUT);
  pinMode(7,INPUT);
  pinMode(8,INPUT);
  pinMode(9,INPUT);
  pinMode(10,INPUT);
  pinMode(11,INPUT);
  
  attachInterrupt(digitalPinToInterrupt(2),awake, RISING);

  __WFI();
}

void loop() {
  if (work) {
    readPins();
    readPinsDebug(); 
    work = false;
  } else {
    
    int value;
    while (dequeue(&value)) {
      send(value);
    }
  }

  __WFI(); 
}


//_______________________GPIO communication_____________________

void awake(){  
  work=true;
}


void readPins(){
    
  
    int bit0 = READ_PIN(R_PORT1,11); //D6
    int bit1 = READ_PIN(R_PORT1,12);  // D7
    int bit2 = READ_PIN(R_PORT3,4);  // D8
    int bit3 = READ_PIN(R_PORT3,3);  // D9
    int bit4 = READ_PIN(R_PORT1,3); // D10
    int bit5 = READ_PIN(R_PORT4,11); // D11
    
  
    // Ricostruisci il valore
    int value = (bit5 << 5) | (bit4 << 4) | (bit3 << 3) |
                (bit2 << 2) | (bit1 << 1) | bit0;
   enqueue(value);               
}

void readPinsDebug() {
  // Leggi i pin da D3 a D11 (D3 = bit 0, D4 = bit 1, ..., D11 = bit 8)
  
  int bit0 = READ_PIN(R_PORT1,11);
  int bit1 = READ_PIN(R_PORT1,12);  // D7
  int bit2 = READ_PIN(R_PORT3,4);  // D8
  int bit3 = READ_PIN(R_PORT3,3);  // D9
  int bit4 = READ_PIN(R_PORT1,3); // D10
  int bit5 = READ_PIN(R_PORT4,11); // D11
  

  // Ricostruisci il valore
  int value = (bit5 << 5) | (bit4 << 4) | (bit3 << 3) |
              (bit2 << 2) | (bit1 << 1) | bit0;

  // Stampa i singoli bit
  Serial.print("Bits: ");
  Serial.print(bit5); Serial.print(bit4); Serial.print(bit3);
  Serial.print(bit2); Serial.print(bit1); Serial.println(bit0);

  // Stampa il valore totale
  Serial.print("Received value: ");
  Serial.println(value);
}

void enqueue(int value) {
  *head = value;

  head++;
  if (head == queueEnd) head = queueStart;

  if (queueFull) {

    tail++;
    if (tail == queueEnd) tail = queueStart;
  } else if (head == tail) {
    // We just filled the queue
    queueFull = true;
  }
}

bool dequeue(int* outValue) {
  if (!queueFull && head == tail) {
    return false;  // Empty
  }

  *outValue = *tail;
  tail++;
  if (tail == queueEnd) tail = queueStart;

  queueFull = false;
  return true;
}




//_______________________WIFI_____________________


void send(int value){
  udp.beginPacket(IPserver, targetPort);
  udp.print(value); 
  udp.endPacket();
}

void scanAndStoreNetworks() {
  Serial.println("Scanning for Wi-Fi networks...");
  numNetworks = WiFi.scanNetworks();

  if (numNetworks <= 0) {
    Serial.println("No networks found.");
    while (true); // Stop here
  }

  Serial.println("Available networks:");
  for (int i = 0; i < numNetworks; i++) {
    ssids[i] = WiFi.SSID(i);
    Serial.print(i);
    Serial.print(": ");
    Serial.print(ssids[i]);
    Serial.print(" (");
    Serial.print(WiFi.RSSI(i));
    Serial.println(" dBm)");
  }
}


void connectFlow() {
  while (true) {
    int selection = getNetworkSelection();
    String password = getPassword(ssids[selection]);
    while (true) {
     

      Serial.print("Connecting to ");
      Serial.println(ssids[selection]);

      WiFi.begin(ssids[selection].c_str(), password.c_str());

      Serial.print("Connecting");
      unsigned long startAttemptTime = millis();
      while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
        Serial.print(".");
        delay(500);
      }

      if (WiFi.status() == WL_CONNECTED) {
        IPAddress ip = WiFi.localIP();
        if (ip == IPAddress(0, 0, 0, 0)) {
          Serial.println("\n❌ Connected, but IP is 0.0.0.0 — retrying...");
          WiFi.disconnect();
          delay(1000);
          continue;  // Retry with the same credentials
        }

        Serial.println("\n✅ Connected!");
        Serial.print("IP address: ");
        Serial.println(ip);
        
        udp.begin(localPort);  // Start UDP listening
        do{
          sendDiscoveryBroadcast();
          listenForDiscoveryResponses(5000);  // wait 5 seconds for replies
        }while(IPserver==IPAddress(0, 0, 0, 0));
        

        return; 
      } else {
        Serial.println("\n❌ Failed to connect.");
        Serial.println("Enter 'r' to retry password or 'b' to go back to network selection:");

        while (!Serial.available());
        char choice = Serial.read();
        Serial.readStringUntil('\n'); // clear buffer

        if (choice == 'b' || choice == 'B') {
          break; // back to SSID selection
        } else if (choice == 'r' || choice == 'R') {
          Serial.println("🔁 Retrying password entry...");
        } else {
          Serial.println("Invalid choice. Going back to network selection.");
          break;
        }
      }
    }
  }
}

int getNetworkSelection() {
  int selection = -1;

  while (true) {
    Serial.println("\nEnter the number of the network you want to connect to:");
    while (!Serial.available());
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (isNumeric(input)) {
      selection = input.toInt();
      if (selection >= 0 && selection < numNetworks) {
        return selection;
      }
    }

    Serial.println("❌ Invalid selection. Please try again.");
  }
}

String getPassword(String ssid) {
  Serial.print("\nEnter password for network \"");
  Serial.print(ssid);
  Serial.println("\":");

  while (!Serial.available());
  String pw = Serial.readStringUntil('\n');
  pw.trim();
  return pw;
}

bool isNumeric(String str) {
  for (int i = 0; i < str.length(); i++) {
    if (!isDigit(str[i])) return false;
  }
  return str.length() > 0;
}

void sendDiscoveryBroadcast() {
  Serial.println("\n📡 Sending UDP broadcast to discover server...");

  udp.beginPacket(broadcastIP, targetPort);
  udp.write("DISCOVER_SERVER");
  udp.endPacket();
}


void listenForDiscoveryResponses(unsigned long durationMs) {
  unsigned long startTime = millis();
  char incomingPacket[255];

  Serial.println("🕓 Waiting for responses...");

  while (millis() - startTime < durationMs) {
    int packetSize = udp.parsePacket();
    if (packetSize) {
      int len = udp.read(incomingPacket, 255);
      if (len > 0) {
        incomingPacket[len] = '\0'; // Null-terminate string
      }

      IPAddress senderIP = udp.remoteIP();

      // ✅ Ignore packets from self
      if (senderIP == WiFi.localIP()) {
        continue;
      }

      IPserver = senderIP;
      Serial.print("📬 Received response from ");
      Serial.print(senderIP);
      Serial.print(": ");
      Serial.println(incomingPacket);
    }
    delay(100); // avoid tight loop
  }

  Serial.println("✅ Discovery complete.");
}
