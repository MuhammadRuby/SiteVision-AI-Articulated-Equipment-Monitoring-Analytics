import cv2
import json
import os
from kafka import KafkaProducer
from detector import EquipmentDetector

def main():
    # الإعدادات من الـ Environment Variables (عشان الـ Docker)
    KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
    VIDEO_PATH = '/data/input_videos/test_video.mp4'
    MODEL_PATH = '/cv_service/best.pt'

    detector = EquipmentDetector(MODEL_PATH)
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_id = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        results = detector.process_frame(frame, frame_id, fps)
        
        for p in results:
            producer.send('equipment_status', value=p)
            # رسم للـ Debugging
            b = p['bbox']
            cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0,255,0), 2)
            cv2.putText(frame, f"{p['equipment_id']}: {p['activity']}", (int(b[0]), int(b[1]-5)), 0, 0.5, (0,255,0), 2)

        cv2.imshow('CV Service Stream', frame)
        frame_id += 1
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    producer.flush()

if __name__ == "__main__":
    main()