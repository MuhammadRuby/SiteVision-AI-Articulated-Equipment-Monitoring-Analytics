from ultralytics import YOLO
import cv2
from .activity_classifier import ActivityClassifier

class EquipmentDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.classifier = ActivityClassifier()
        self.class_names = {0: 'excavator', 1: 'concrete_mixer_truck', 2: 'dump_truck', 3: 'loader', 4: 'moxy', 5: 'roller'}
        self.prev_gray = None
        self.stats = {}

    def process_frame(self, frame, frame_id, fps):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = self.model.track(frame, persist=True, conf=0.3)
        payloads = []

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)
            clss = results[0].boxes.cls.cpu().numpy().astype(int)

            for box, tid, cls in zip(boxes, ids, clss):
                name = self.class_names[cls]
                motion = self.classifier.get_motion_status(gray, self.prev_gray, box, tid, name)
                activity = self.classifier.classify(name, motion)
                
                # حساب الـ Analytics
                if tid not in self.stats: self.stats[tid] = {"active": 0, "total": 0}
                self.stats[tid]["total"] += (1/fps)
                if motion["state"] == "ACTIVE": self.stats[tid]["active"] += (1/fps)
                util = (self.stats[tid]["active"] / self.stats[tid]["total"]) * 100

                payloads.append({
                    "equipment_id": f"{name[:2].upper()}-{tid}",
                    "class": name,
                    "state": motion["state"],
                    "activity": activity,
                    "motion_source": motion["motion_source"],
                    "utilization": f"{util:.1f}%",
                    "bbox": box.tolist()
                })

        self.prev_gray = gray.copy()
        return payloads