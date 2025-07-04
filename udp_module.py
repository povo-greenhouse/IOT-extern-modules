import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk

# Config porta UDP
UDP_PORT = 12345

# Creazione socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("", UDP_PORT))


def start_udp_thread(log_callback, update_square_callback, value_labels,add_task_udp,rmv_task_udp):
    """
    log_callback: funzione per loggare messaggi (GUI)
    update_square_callback: funzione per aggiornare il colore del semaforo
    value_labels: lista delle label parametriche della GUI
    """
    # Mappa tra first3 e indice di value_labels: {first3: index in value_labels}
    label_map = {1: 1, 2: 3, 4: 2, 5: 0}

    def listen_udp():
        while True:
            data, addr = sock.recvfrom(1024)

            try:
                msg = data.decode(errors="ignore")
            except Exception:
                msg = ""

            if msg == "DISCOVER_SERVER":
                sock.sendto(b"SERVER_HERE", addr)
                log_callback(f"↪ Responded to {addr[0]}")
                continue
            
            info, frame, active, param,msg = decode_udp_packet(data)
            log_callback(info)
            if param is not None:
                first3, param_val = param
                # Mappa tra first3 e indice label GUI
                label_map = {1: 1, 2: 3, 4: 2, 5: 0}
                idx = label_map.get(first3)
                if idx is not None:
                    update_value_label(idx, param_val, value_labels)
            if frame is not None and active is not None:
                state = 1 if active == "ON" else 0
                update_square_callback(frame, state)
            if msg is not None:
                if "update" in msg:
                    add_task_udp(msg)
                elif "removal" in msg:
                    rmv_task_udp(msg)    

    thread = threading.Thread(target=listen_udp, daemon=True)
    thread.start()


def decode_udp_packet(data): 
    try:
        msg = data.decode().strip()
        value = int(msg)
        first3 = (value >> 6) & 0b111
        bit4 = (value >> 5) & 0b1
        param_val = (value >> 3) & 0b11  
        info = f"[DECODED] raw value: {value}   bits: {bin(value)}   first3: {bin(first3)}\n"
        frame = None
        active = None
        msg=None

        # Se è un parametro label (bit4==0)
        if bit4 == 0 and first3 in (1,2,4,5):
            case_text = f"Update param {first3} val {param_val} (e spegni semaforo)"
            info += case_text
            # Associazione frame (es: Air=0, Temp=1, WaterR=2, Light=3) <-- ADATTA alla tua GUI
            match first3:
                case 0b001:   # AIR
                    frame = 0
                    if param_val == 0:
                        param_val = ""
                    elif param_val == 1:
                        param_val = ""
                    elif param_val == 2:
                        param_val = ""
                    elif param_val == 3:
                        param_val = ""
                case 0b010:   # TEMP
                    frame = 1
                    if param_val == 0:
                        param_val = "Too coold!"
                    elif param_val == 1:
                        param_val = "Mild"
                    elif param_val == 2:
                        param_val = "Warm"
                    elif param_val == 3:
                        param_val = "Too hot!"
                case 0b100:   # WATER R
                    frame = 3  
                    if param_val == 0:
                        param_val = "Full"
                    elif param_val == 1:
                        param_val = "Abundant"
                    elif param_val == 2:
                        param_val = "Scarse"
                    elif param_val == 3:
                        param_val = "Refill!"
                case 0b101:   # LIGHT
                    frame = 4
                    if param_val == 0:
                        param_val = ""
                    elif param_val == 1:
                        param_val = ""
                    elif param_val == 2:
                        param_val = ""
                    elif param_val == 3:
                        param_val = ""
            active = "OFF"
            return info, frame, active, (first3, param_val),None

        # Altrimenti, ON/OFF semaforo (bit4==1)
        active = "ON" if bit4 else "OFF"
        match first3:
            case 0b000:
                case_text = "First 3 bits: 000 - TASK update"
                if bit4 == 1:
                    msg = f"Task update"
                else:
                    msg = f"Task removal"    
                frame = None
            case 0b001:
                case_text = "First 3 bits: 001 - AIR"
                frame = 0
            case 0b010:
                case_text = "First 3 bits: 010 - TEMP"
                frame = 1
            case 0b011:
                case_text = "First 3 bits: 011 - WATER T"
                frame = 2
            case 0b100:
                case_text = "First 3 bits: 100 - WATER R"
                frame = 3
            case 0b101:
                case_text = "First 3 bits: 101 - LIGHT"
                frame = 4
            case 0b110:
                case_text = "First 3 bits: 110 - PUMP1"
                frame = 5
            case 0b111:
                case_text = "First 3 bits: 111 - PUMP2"
                frame = 6
            case _:
                case_text = "Unknown case"
        info += case_text
        return info, frame, active, None,msg

    except Exception as e:
        return f"Decoder error: {e}", None, None, None,None



def update_value_label(label_idx, message, value_labels):
    """
    Aggiorna la label corrispondente nella lista value_labels.
    
    :param label_idx: indice (int) della label da aggiornare (0 = Light intensity, ecc)
    :param message: testo da mostrare nella label (str o int)
    :param value_labels: lista delle label tkinter (value_labels)
    """
    if 0 <= label_idx < len(value_labels):
        value_labels[label_idx].config(text=str(message))
    else:
        print(f"Indice label fuori range: {label_idx}")
