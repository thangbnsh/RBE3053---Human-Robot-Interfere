# ============================================================
# robot_controller.py - PHẦN 2 (TIAGo) - SỬA LỖI WAVE_BACK
# ============================================================

from controller import Robot
import socket
import json
import threading

TIME_STEP = 64
MAX_VELOCITY = 1.5
robot = Robot()

# ====== Motor setup ======
# ... (Phần khởi tạo Motor giữ nguyên, đảm bảo tìm thấy các khớp tay)

# ====== Motor setup ======
# Bánh xe
wheel_left = robot.getDevice("wheel_left_joint")
wheel_right = robot.getDevice("wheel_right_joint")

# ====== Đầu (gaze) ======
# ... (Phần này giữ nguyên)
possible_yaw = ["head_1_joint", "head_pan_joint", "head_yaw_joint"]
possible_pitch = ["head_2_joint", "head_tilt_joint", "head_pitch_joint"]

head_yaw = None
head_pitch = None

for name in possible_yaw:
    try:
        head_yaw = robot.getDevice(name)
        if head_yaw:
            print(f"[INFO] Found head yaw joint: {name}")
            break
    except:
        pass

for name in possible_pitch:
    try:
        head_pitch = robot.getDevice(name)
        if head_pitch:
            print(f"[INFO] Found head pitch joint: {name}")
            break
    except:
        pass

# ====== Tay phải (vẫy) ======
r_shoulder_pitch = robot.getDevice("arm_5_joint")
r_elbow_roll = robot.getDevice("arm_4_joint") # Khớp khuỷu tay

motors = [wheel_left, wheel_right, r_shoulder_pitch, r_elbow_roll]
for m in motors:
    if m:
        m.setPosition(float('inf'))
        m.setVelocity(0.0)

# Riêng đầu nên để ở chế độ position control
if head_yaw:
    head_yaw.setVelocity(1.0)
    head_yaw.setPosition(0.0)
if head_pitch:
    head_pitch.setVelocity(1.0)
    head_pitch.setPosition(0.0)

print("[INFO] TIAGo Controller started. Waiting for commands...")

# ============================================================
# HÀM THỰC HIỆN HÀNH ĐỘNG
# ============================================================
def perform_action(cmd):
    cmd = cmd.upper()
    print(f"[CMD] Executing: {cmd}")

    # --- Di chuyển (giữ nguyên) ---
    if cmd == "MOVE_FORWARD":
        wheel_left.setVelocity(MAX_VELOCITY)
        wheel_right.setVelocity(MAX_VELOCITY)

    elif cmd == "MOVE_BACKWARD":
        wheel_left.setVelocity(-MAX_VELOCITY)
        wheel_right.setVelocity(-MAX_VELOCITY)

    elif cmd == "TURN_LEFT":
        wheel_left.setVelocity(-0.5 * MAX_VELOCITY)
        wheel_right.setVelocity(0.5 * MAX_VELOCITY)

    elif cmd == "TURN_RIGHT":
        wheel_left.setVelocity(0.5 * MAX_VELOCITY)
        wheel_right.setVelocity(-0.5 * MAX_VELOCITY)

    elif cmd == "STOP":
        wheel_left.setVelocity(0.0)
        wheel_right.setVelocity(0.0)

    # --- Vẫy tay (ĐÃ CHỈNH SỬA) ---
    elif cmd == "WAVE_BACK" and r_shoulder_pitch and r_elbow_roll:
        wheel_left.setVelocity(0.0)
        wheel_right.setVelocity(0.0)
        print("[ACTION] Waving hand...")

        # 1. Đặt khớp vai (arm_5_joint) vào vị trí giơ cao cố định
        r_shoulder_pitch.setVelocity(0.5)
        r_shoulder_pitch.setPosition(-1.5) # Giơ cánh tay lên cao
        robot.step(50 * TIME_STEP)
        
        # 2. Tạo dao động vẫy bằng khớp khuỷu tay (arm_4_joint)
        r_elbow_roll.setVelocity(2.0) # Tốc độ cao để tạo chuyển động nhanh
        wave_pos1 = 1.5
        wave_pos2 = -0.5
        
        for _ in range(5): # Vẫy 5 lần
            r_elbow_roll.setPosition(wave_pos1)
            robot.step(15 * TIME_STEP) # Vẫy nhanh
            r_elbow_roll.setPosition(wave_pos2)
            robot.step(15 * TIME_STEP)
        
        # 3. Kết thúc hành động: đưa tay về vị trí ban đầu
        r_elbow_roll.setPosition(0.0)
        robot.step(20 * TIME_STEP)
        r_shoulder_pitch.setPosition(0.0)
        robot.step(50 * TIME_STEP)
        print("[ACTION] Done waving.")


    # --- Gật đầu (giữ nguyên) ---
    elif cmd == "NOD" and head_pitch:
        # ... (Code NOD giữ nguyên)
        wheel_left.setVelocity(0.0)
        wheel_right.setVelocity(0.0)
        print("[ACTION] Nodding (head pitch)...")

        head_pitch.setVelocity(1.0)
        for _ in range(3):
            head_pitch.setPosition(0.25)   # cúi xuống
            robot.step(20 * TIME_STEP)
            head_pitch.setPosition(-0.15)  # ngẩng lên
            robot.step(20 * TIME_STEP)
        head_pitch.setPosition(0.0)
        robot.step(30 * TIME_STEP)
        print("[ACTION] Done nodding.")

    # --- Nhìn người dùng (giữ nguyên) ---
    elif cmd == "LOOK_AT_HUMAN" and head_yaw and head_pitch:
        # ... (Code LOOK_AT_HUMAN giữ nguyên)
        wheel_left.setVelocity(0.0)
        wheel_right.setVelocity(0.0)
        print("[ACTION] Looking at human...")
        head_yaw.setVelocity(1.0)
        head_pitch.setVelocity(1.0)
        head_yaw.setPosition(0.5)    # quay sang trái
        robot.step(40 * TIME_STEP)
        head_yaw.setPosition(-0.5)   # quay sang phải
        robot.step(40 * TIME_STEP)
        head_yaw.setPosition(0.0)
        head_pitch.setPosition(0.0)
        print("[ACTION] Done LOOK_AT_HUMAN.")

    # --- Dừng ở khoảng cách giả lập (giữ nguyên) ---
    elif cmd == "STOP_AT_DISTANCE":
        # ... (Code STOP_AT_DISTANCE giữ nguyên)
        print("[SIM] Moving forward to stop at 1.5 m ...")
        wheel_left.setVelocity(MAX_VELOCITY)
        wheel_right.setVelocity(MAX_VELOCITY)
        robot.step(150 * TIME_STEP)   # mô phỏng di chuyển ~1.5m
        wheel_left.setVelocity(0.0)
        wheel_right.setVelocity(0.0)
        print("[SIM] Robot stopped at target distance.")

    else:
        print(f"[WARN] Unknown or unsupported command: {cmd}")

# ============================================================
# SOCKET SERVER (Giữ nguyên)
# ============================================================
def socket_server():
    host = "127.0.0.1"
    port = 5005
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    print(f"[SERVER] Listening on {host}:{port}")

    while True:
        try:
            client, addr = server.accept()
            data = client.recv(1024).decode()
            if data:
                command = json.loads(data)
                perform_action(command["command"])
            client.close()
        except Exception as e:
            print(f"[SERVER ERROR] {e}")

# ============================================================
# KHỞI ĐỘNG SERVER (Giữ nguyên)
# ============================================================
threading.Thread(target=socket_server, daemon=True).start()

# ============================================================
# VÒNG LẶP CHÍNH WEBOTS (Giữ nguyên)
# ============================================================
while robot.step(TIME_STEP) != -1:
    pass