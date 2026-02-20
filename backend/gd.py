import cv2
import time
import mediapipe as mp

# MediaPipe Tasks API
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

with FaceLandmarker.create_from_options(options) as landmarker:
    start_time = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp = int(time.time() * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp)

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]

            # Using normalized coordinates
            top = landmarks[159]
            bottom = landmarks[145]
            iris = landmarks[468]

            eye_center = (top.y + bottom.y) / 2
            eye_height = bottom.y - top.y
            offset = iris.y - eye_center

            ratio = offset / eye_height if eye_height != 0 else 0
            looking_down = ratio > 0.15

            if looking_down:
                if start_time is None:
                    start_time = time.time()

                elapsed = time.time() - start_time

                cv2.putText(frame, f"Down: {elapsed:.1f}s", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

                if elapsed > 3:
                    cv2.putText(frame, "ALERT!", (30, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
            else:
                start_time = None

        cv2.imshow("PhoneIsBad - Gaze Detection", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
