import tkinter as tk
from PIL import Image, ImageTk

from udp_module import start_udp_thread, update_value_label

# ------------------- VARIABILI GLOBALI/CONFIG ---------------------
square_labels = [
    "Air Sensing", "Temperature Sensing", "Tank full", "Reservoire empty", "Light Sensing","Watering the plants", 
    "Refilling Reservoire"
]
state_colors = [
    "#285a36", "#55ff6c", "#ffe46c", "#ff7070"
]

info_labels = ["Light intensity", "Air quality", "Water in the reservoir", "Temperature"]
image_paths = ["light.png", "air.png", "water.png", "temp.png"]
image_refs = []

# ------------------- GUI SETUP -------------------------------------
root = tk.Tk()
root.title("🌿 UDP Server Monitor")
root.geometry("1250x480")
root.configure(bg="#238f4d")

main_frame = tk.Frame(root, bg="#238f4d")
main_frame.pack(fill="both", expand=True, padx=15, pady=10)

left_frame = tk.Frame(main_frame, bg="#238f4d")
left_frame.pack(side="left", fill="y", padx=(0, 32))
title = tk.Label(left_frame, text="UDP 7 Squares Monitor", font=("Helvetica", 18, "bold"),
                 fg="#fff", bg="#238f4d")
title.pack(pady=(10, 10))

squares_frame = tk.Frame(left_frame, bg="#238f4d")
squares_frame.pack(pady=15)

squares = []
for i in range(7):
    frame = tk.Frame(
        squares_frame, width=95, height=95, bg=state_colors[0], bd=3, relief="groove"
    )
    frame.grid(row=0, column=i, padx=9)
    frame.grid_propagate(False)
    label = tk.Label(frame, text=square_labels[i], bg=state_colors[0], fg="#fff", font=("Helvetica", 11, "bold"))
    label.pack(expand=True)
    squares.append((frame, label))

right_frame = tk.Frame(main_frame, bg="#238f4d")
right_frame.pack(side="right", fill="y")

log_text = tk.Text(
    right_frame, width=52, height=9, bg="#222", fg="#d6ffd7",
    font=("Consolas", 11), borderwidth=2
)
log_text.pack(pady=(10, 8))
log_text.insert(tk.END, "Waiting for UDP packets...\n")
log_text.config(state='disabled')

images_container = tk.Frame(right_frame, bg="#238f4d")
images_container.pack(pady=7)

value_labels = []

for i in range(2):
    for j in range(2):
        index = i * 2 + j
        frame = tk.Frame(images_container, bg="#40a763", bd=3, relief="ridge")
        frame.grid(row=i, column=j, padx=14, pady=10)
        try:
            img = Image.open(image_paths[index])
            img = img.resize((70, 70))
            tk_img = ImageTk.PhotoImage(img)
        except Exception:
            img = Image.new('RGB', (70, 70), color=(120, 120, 120))
            tk_img = ImageTk.PhotoImage(img)
        image_refs.append(tk_img)
        img_label = tk.Label(frame, image=tk_img, bg="#40a763")
        img_label.pack(pady=(6, 3))
        value_label = tk.Label(frame, text="N/A", font=("Helvetica", 15, "bold"),
                               fg="#1d321d", bg="#40a763")
        value_label.pack(pady=(0, 5))
        value_labels.append(value_label)
        title_label = tk.Label(frame, text=info_labels[index], font=("Helvetica", 12, "bold"),
                               fg="#0b220b", bg="#40a763")
        title_label.pack(pady=(0, 10))

# ------------------- FRAME CUSTOM IN BASSO A SINISTRA ---------------------

# Nuovo frame per quadrati personalizzati
custom_squares_frame = tk.Frame(root, bg="#18432a")
custom_squares_frame.place(relx=0.01, rely=0.97, anchor="sw")  # basso sinistra

# Lista per tenere traccia dei quadrati attuali (label: widget)
custom_squares_widgets = {}

def add_square_to_custom_frame(label_text):
    """Aggiungi un quadrato con label personalizzata al frame custom."""
    if label_text in custom_squares_widgets:
        return  # Evita duplicati
    frame = tk.Frame(custom_squares_frame, width=80, height=80, bg="#369955", bd=2, relief="ridge")
    frame.pack(side="left", padx=8, pady=8)
    frame.pack_propagate(False)
    label = tk.Label(frame, text=label_text, bg="#369955", fg="#fff", font=("Helvetica", 11, "bold"))
    label.pack(expand=True)
    custom_squares_widgets[label_text] = frame

def remove_square_from_custom_frame(label_text):
    """Rimuovi il quadrato con label specificata dal frame custom."""
    if label_text in custom_squares_widgets:
        frame = custom_squares_widgets.pop(label_text)
        frame.destroy()

# # --------- Esempio di uso: bottoni di test per aggiungere/rimuovere quadrati
# def test_add():
#     from random import randint
#     # Demo: label random
#     label = f"Test {randint(1,99)}"
#     add_square_to_custom_frame(label)

# def test_remove():
#     # Rimuovi il primo quadrato che trovi
#     if custom_squares_widgets:
#         label = next(iter(custom_squares_widgets))
#         remove_square_from_custom_frame(label)

# Bottoni di test (puoi rimuoverli dopo)
# test_btn_frame = tk.Frame(root, bg="#18432a")
# test_btn_frame.place(relx=0.01, rely=0.92, anchor="sw")
# tk.Button(test_btn_frame, text="Aggiungi", command=test_add, bg="#3ad176", fg="#fff", font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
# tk.Button(test_btn_frame, text="Rimuovi", command=test_remove, bg="#f05353", fg="#fff", font=("Helvetica", 10, "bold")).pack(side="left", padx=5)

# --------------------- CALLBACKS USATE DA UDP ------------------------
def set_square_state(index, state):
    if 0 <= index < 7:
        color = state_colors[state] if 0 <= state < len(state_colors) else state_colors[0]
        squares[index][0].config(bg=color)
        squares[index][1].config(bg=color)

def log_message(msg):
    log_text.config(state='normal')
    log_text.insert(tk.END, msg + "\n")
    log_text.see(tk.END)
    log_text.config(state='disabled')

def update_square_from_udp(idx, state):
    # Qui puoi fare root.after(0, ...) se vuoi essere thread-safe!
    root.after(0, lambda: set_square_state(idx, state))

def add_task_udp(msg):
    root.after(0, lambda: add_square_to_custom_frame(msg))

def rmv_task_udp(msg):
    root.after(0, lambda: remove_square_from_custom_frame(msg))

# -------------------- INIZIALIZZA THREAD UDP -------------------------
def parse_message_in_gui_thread(message):
    # Chiamato dal thread UDP ma esegue update nella mainloop di Tkinter
    root.after(0, lambda: parse_udp_message(
        message, set_square_state, square_labels, value_labels, log_message
    ))

def log_in_gui_thread(msg):
    root.after(0, lambda: log_message(msg))

start_udp_thread(
    log_in_gui_thread,
    update_square_from_udp,
    value_labels,
    add_task_udp,
    rmv_task_udp,
)

root.mainloop()
