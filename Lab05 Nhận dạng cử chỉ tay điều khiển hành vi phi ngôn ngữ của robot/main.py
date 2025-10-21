import cv2
import mediapipe as mp
import numpy as np
import time
import json

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

# Biến hỗ trợ phát hiện wave (vẫy tay)
previous_x = None
movement_counter = 0
last_wave_time = 0

def get_finger_state(landmarks):
   
    finger_open = []

    # Ngón cái (so sánh x)
    if landmarks[4][0] > landmarks[3][0]:
        finger_open.append(1)
    else:
        finger_open.append(0)

    # Các ngón còn lại (so sánh y)
    tips = [8, 12, 16, 20]
    pip_joints = [6, 10, 14, 18]
    for tip, pip in zip(tips, pip_joints):
        if landmarks[tip][1] < landmarks[pip][1]:
            finger_open.append(1)
        else:
            finger_open.append(0)

    return finger_open

def detect_gesture(landmarks):
    global previous_x, movement_counter, last_wave_time

    finger_state = get_finger_state(landmarks)

    # Open hand ✋: tất cả ngón mở
    if sum(finger_state) == 5:
        return "open_hand", 0.95

    # Raise hand 👉: bàn tay ở nửa trên màn hình
    wrist_y = landmarks[0][1]
    if wrist_y < 0.4:  # tùy thuộc độ cao webcam
        return "raise_hand", 0.90

    # Wave 👋: phát hiện chuyển động qua trái/phải
    hand_x = landmarks[0][0]
    if previous_x is not None:
        if abs(hand_x - previous_x) > 0.05:
            movement_counter += 1
            last_wave_time = time.time()
    previous_x = hand_x

    # Nếu tay vẫy qua lại nhiều lần trong thời gian ngắn
    if movement_counter >= 4 and (time.time() - last_wave_time) < 1.5:
        movement_counter = 0
        return "wave", 0.87

    return None, 0

# =============================
# 3. Khởi động webcam
# =============================
cap = cv2.VideoCapture(0)

print("👉 Đang khởi động nhận dạng cử chỉ tay... (Nhấn 'q' để thoát)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Lật ảnh (mirror)
    frame = cv2.flip(frame, 1)

    # Chuyển sang RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Phát hiện bàn tay
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            h, w, _ = frame.shape
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y])

            # Vẽ khung bàn tay
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Nhận dạng cử chỉ
            gesture, conf = detect_gesture(landmarks)
            if gesture:
                command = gesture_map[gesture]
                data = {"gesture": gesture, "confidence": round(conf, 2), "command": command}
                print(json.dumps(data, ensure_ascii=False))

                # Hiển thị lên màn hình
                cv2.putText(frame, f"{gesture} ({conf:.2f})", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    cv2.imshow("Gesture Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
