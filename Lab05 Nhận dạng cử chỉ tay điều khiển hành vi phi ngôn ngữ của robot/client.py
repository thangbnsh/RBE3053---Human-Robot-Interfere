import socket
import json
import sys

# ==============================
# client.py
# Gửi lệnh JSON tới robot_controller.py qua socket TCP
# ==============================

HOST = "127.0.0.1"
PORT = 5005









def send_command(cmd):
    try:
        # Tạo kết nối TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        # Tạo gói JSON {"command": "<LỆNH>"}
        message = json.dumps({"command": cmd})
        s.send(message.encode('utf-8'))

        print(f"[CLIENT] Sent command: {cmd}")
        s.close()

        
    except Exception as e:
        print(f"[ERROR] {e}")

# ==============================
# Chạy từ terminal
# ==============================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng:")
        print("  python client.py <COMMAND>")
        print("Ví dụ:")
        print("  python client.py WAVE_BACK")
        print("  python client.py NOD")
        print("  python client.py LOOK_AT_HUMAN")
        print("  python client.py STOP_AT_DISTANCE")
        sys.exit(0)

    command = sys.argv[1]
    send_command(command)
