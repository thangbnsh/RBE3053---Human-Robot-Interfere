import cv2
import mediapipe as mp
import numpy as np
import time
import json
import socket
import argparse

# =============================
# 1. Khởi tạo MediaPipe Hands
# =============================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# =============================
# 2. Ánh xạ gesture → hành vi
# =============================
gesture_map = {
    "raise_hand": "STOP_AT_DISTANCE",
    "open_hand": "LOOK_AT_HUMAN",
    "wave": "WAVE_BACK"
}

# =============================
# 3. Socket gửi lệnh đến robot_controller
# =============================
HOST = "127.0.0.1"
PORT = 5005

def send_to_robot(command):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        msg = json.dumps({"command": command})
        s.send(msg.encode("utf-8"))
        s.close()
        print(f"[SOCKET] Sent command: {command}")
    except Exception as e:
        print(f"[SOCKET ERROR] {e}")

# =============================
# 4. Phát hiện trạng thái ngón tay
# =============================
previous_x = None
movement_counter = 0
last_wave_time = 0
last_sent = None
cooldown = 2.0  # giãn cách 2 giây giữa các lệnh

def get_finger_state(landmarks):
    finger_open = []

    # Ngón cái
    finger_open.append(1 if landmarks[4][0] > landmarks[3][0] else 0)

    # Các ngón còn lại
    tips = [8, 12, 16, 20]
    pip_joints = [6, 10, 14, 18]
    for tip, pip in zip(tips, pip_joints):
        finger_open.append(1 if landmarks[tip][1] < landmarks[pip][1] else 0)

    return finger_open

def detect_gesture(landmarks):
    global previous_x, movement_counter, last_wave_time

    finger_state = get_finger_state(landmarks)

    # Mở tay (open hand)
    if sum(finger_state) == 5:
        return "open_hand", 0.95

    # Giơ tay cao
    wrist_y = landmarks[0][1]
    if wrist_y < 0.4:
        return "raise_hand", 0.9

    # Vẫy tay (wave)
    hand_x = landmarks[0][0]
    if previous_x is not None:
        if abs(hand_x - previous_x) > 0.05:
            movement_counter += 1
            last_wave_time = time.time()
    previous_x = hand_x

    if movement_counter >= 4 and (time.time() - last_wave_time) < 1.5:
        movement_counter = 0
        return "wave", 0.87

    return None, 0

# =============================
# 5. Chạy webcam và gửi tín hiệu
# =============================
def main(video_index=0):
    global last_sent
    cap = cv2.VideoCapture(video_index)
    print("👉 Hệ thống nhận dạng cử chỉ tay đang khởi động... (Nhấn 'q' để thoát)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                h, w, _ = frame.shape
                landmarks = [[lm.x, lm.y] for lm in hand_landmarks.landmark]

                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                gesture, conf = detect_gesture(landmarks)
                if gesture:
                    command = gesture_map[gesture]
                    now = time.time()
                    # tránh gửi quá dày (spam socket)
                    if not last_sent or now - last_sent > cooldown:
                        data = {"gesture": gesture, "confidence": round(conf, 2), "command": command}
                        print(json.dumps(data, ensure_ascii=False))
                        send_to_robot(command)
                        last_sent = now

                    cv2.putText(frame, f"{gesture} ({conf:.2f})", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        cv2.imshow("Gesture Recognition → Robot Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# =============================
# 6. Entry point
# =============================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=int, default=0, help="Chọn camera index (mặc định 0)")
    args = parser.parse_args()
    main(args.video)
