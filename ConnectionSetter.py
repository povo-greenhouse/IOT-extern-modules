import serial
import time
import threading


SERIAL_PORT = 'COM11'     
BAUDRATE = 115200

def read_from_serial(ser):
    """Funzione in thread per leggere dalla seriale e mostrare su console."""
    buffer = ''
    while True:
        if ser.in_waiting > 0:
            byte_data = ser.read(ser.in_waiting).decode(errors='ignore')
            buffer += byte_data
            # Mostra una linea completa (o tutte se ci sono \n multipli)
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                print(line)
                # Se la linea contiene una richiesta input, sblocca l'input utente
                if ('Enter' in line and 'password' in line) or 'Enter the number' in line or 'retry' in line or 'back' in line:
                    user_input = input("> ").strip()
                    # Invia la risposta alla seriale
                    ser.write((user_input + '\n').encode())

def main():
    # Apri la seriale
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1) as ser:
        print(f"Connessione seriale su {SERIAL_PORT} aperta. Premere CTRL+C per uscire.")
        # Avvia thread lettura seriale
        t = threading.Thread(target=read_from_serial, args=(ser,), daemon=True)
        t.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nChiusura script...")

if __name__ == '__main__':
    main()
