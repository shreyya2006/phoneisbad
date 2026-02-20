import cv2
import mediapipe as mp
import time

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

model_path = "face_landmarker.task"

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

cap = cv2.VideoCapture(0)

prev_left = None
prev_right = None

left_eye_overlay = None
right_eye_overlay = None

baseline_y = None
start_time = None

DOWN_THRESHOLD = 20      # how far eyes must move down
GAZE_TIME_THRESHOLD = 5  # seconds

with FaceLandmarker.create_from_options(options) as landmarker:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp = int(time.time() * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp)

        looking_down = False

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]

            def to_pixel(lm):
                return int(lm.x * w), int(lm.y * h)

            left_outer = to_pixel(landmarks[33])
            left_inner = to_pixel(landmarks[133])
            right_outer = to_pixel(landmarks[362])
            right_inner = to_pixel(landmarks[263])

            left_center = ((left_outer[0] + left_inner[0]) // 2,
                           (left_outer[1] + left_inner[1]) // 2)

            right_center = ((right_outer[0] + right_inner[0]) // 2,
                            (right_outer[1] + right_inner[1]) // 2)

            eye_center_y = (left_center[1] + right_center[1]) // 2

            if baseline_y is None:
                baseline_y = eye_center_y

            if eye_center_y - baseline_y > DOWN_THRESHOLD:
                looking_down = True
            else:
                looking_down = False

            # smoothing
            if prev_left is None:
                prev_left = left_center
                prev_right = right_center

            alpha = 0.7
            left_center = (int(alpha * prev_left[0] + (1-alpha) * left_center[0]),
                           int(alpha * prev_left[1] + (1-alpha) * left_center[1]))

            right_center = (int(alpha * prev_right[0] + (1-alpha) * right_center[0]),
                            int(alpha * prev_right[1] + (1-alpha) * right_center[1]))

            prev_left = left_center
            prev_right = right_center

            eye_w, eye_h = 80, 60

            lx, ly = left_center
            rx, ry = right_center

            left_eye_roi = frame[ly-eye_h:ly+eye_h, lx-eye_w:lx+eye_w]
            right_eye_roi = frame[ry-eye_h:ry+eye_h, rx-eye_w:rx+eye_w]

            if left_eye_roi.size != 0:
                left_eye_overlay = cv2.resize(left_eye_roi, (200, 120))

            if right_eye_roi.size != 0:
                right_eye_overlay = cv2.resize(right_eye_roi, (200, 120))

        # ---------- TIMER LOGIC ----------
        if looking_down:
            if start_time is None:
                start_time = time.time()

            elapsed = time.time() - start_time

            cv2.putText(frame, f"Looking Down: {elapsed:.1f}s",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

            if elapsed > GAZE_TIME_THRESHOLD:
                # BIG ALERT TEXT
                cv2.putText(frame, "⚠ ALERT ⚠",
                            (int(w*0.3), int(h*0.5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 2,
                            (0,0,255), 5)
        else:
            start_time = None

        # ---------- EYE FILTER ----------
        if left_eye_overlay is not None:
            frame[20:140, 20:220] = left_eye_overlay

        if right_eye_overlay is not None:
            frame[20:140, w-220:w-20] = right_eye_overlay

        cv2.imshow("PhoneIsBad - Focus Monitor", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
