import cv2
import mediapipe as mp
import time

# -------- MediaPipe Setup --------
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

baseline_eye = None
baseline_pitch = None
start_time = None

left_eye_overlay = None
right_eye_overlay = None

DEAD_ZONE = 8
GAZE_TIME_THRESHOLD = 5

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
            lm = result.face_landmarks[0]

            def pt(i):
                return int(lm[i].x * w), int(lm[i].y * h)

            # -------- Eye centers --------
            left_outer = pt(33)
            left_inner = pt(133)
            right_outer = pt(362)
            right_inner = pt(263)

            left_center = ((left_outer[0] + left_inner[0]) // 2,
                           (left_outer[1] + left_inner[1]) // 2)

            right_center = ((right_outer[0] + right_inner[0]) // 2,
                            (right_outer[1] + right_inner[1]) // 2)

            eye_center_y = (left_center[1] + right_center[1]) // 2

            # -------- Head pitch --------
            forehead = pt(10)
            chin = pt(152)
            pitch = chin[1] - forehead[1]

            # -------- Baselines --------
            if baseline_eye is None:
                baseline_eye = eye_center_y
            if baseline_pitch is None:
                baseline_pitch = pitch

            eye_disp = eye_center_y - baseline_eye
            pitch_disp = baseline_pitch - pitch

            # -------- Neutral drift --------
            if abs(eye_disp) < DEAD_ZONE:
                baseline_eye = int(0.9 * baseline_eye + 0.1 * eye_center_y)

            if abs(pitch_disp) < DEAD_ZONE:
                baseline_pitch = int(0.9 * baseline_pitch + 0.1 * pitch)

            # -------- Balanced Detection Logic --------
            if eye_disp > 18:
                looking_down = True

            elif eye_disp > 10 and pitch_disp > 4:
                looking_down = True

            else:
                looking_down = False

            # -------- Eye ROIs --------
            eye_w, eye_h = 80, 60

            lx, ly = left_center
            rx, ry = right_center

            left_eye_roi = frame[ly-eye_h:ly+eye_h, lx-eye_w:lx+eye_w]
            right_eye_roi = frame[ry-eye_h:ry+eye_h, rx-eye_w:rx+eye_w]

            if left_eye_roi.size != 0:
                left_eye_overlay = cv2.resize(left_eye_roi, (200, 120))

            if right_eye_roi.size != 0:
                right_eye_overlay = cv2.resize(right_eye_roi, (200, 120))

        # -------- Timer --------
        if looking_down:
            if start_time is None:
                start_time = time.time()

            elapsed = time.time() - start_time

            cv2.putText(frame, f"Looking Down: {elapsed:.1f}s",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

            if elapsed > GAZE_TIME_THRESHOLD:
                cv2.putText(frame, "⚠ ALERT ⚠",
                            (int(w*0.3), int(h*0.5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 2,
                            (0,0,255), 5)
        else:
            start_time = None

        # -------- Eye Filter --------
        if left_eye_overlay is not None:
            frame[20:140, 20:220] = left_eye_overlay

        if right_eye_overlay is not None:
            frame[20:140, w-220:w-20] = right_eye_overlay

        cv2.imshow("PhoneIsBad - Focus Monitor", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
