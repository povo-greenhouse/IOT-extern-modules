import socket

HOST = "localhost"  # The server's hostname or IP address
PORT = 12345  # The port used by the server

# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # Get input from the user
    message = input("Send a message (or type 'exit' to quit): ")

    # Check if the user wants to exit
    if message.lower() == "exit":
        print("Exiting...")
        break

    # Send data to the server (encode the string to bytes)
    s.sendto(message.encode(), (HOST, PORT))

# Close the socket
s.close()
