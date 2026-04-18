import cv2
import numpy as np

class ActivityClassifier:
    def __init__(self):
        self.prev_centroids = {}

    def get_motion_status(self, frame_gray, prev_gray, box, track_id, class_name):
        x1, y1, x2, y2 = map(int, box)
        current_centroid = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
        
        # 1. كشف الحركة الكلية (للصندوق بالكامل)
        is_moving_globally = False
        if track_id in self.prev_centroids:
            dist = np.linalg.norm(current_centroid - self.prev_centroids[track_id])
            if dist > 2.5: is_moving_globally = True
        self.prev_centroids[track_id] = current_centroid

        # 2. كشف الحركة الداخلية (للأجزاء المفصلية - الحفار)
        state = "INACTIVE"
        motion_source = "none"

        if class_name == 'excavator':
            if not is_moving_globally and prev_gray is not None:
                roi_curr = frame_gray[y1:y2, x1:x2]
                roi_prev = prev_gray[y1:y2, x1:x2]
                if roi_curr.shape == roi_prev.shape and roi_curr.size > 0:
                    flow = cv2.calcOpticalFlowFarneback(roi_prev, roi_curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                    if np.mean(mag) > 0.8:
                        state = "ACTIVE"
                        motion_source = "arm_only"
            elif is_moving_globally:
                state = "ACTIVE"
                motion_source = "full_body"
        else:
            if is_moving_globally:
                state = "ACTIVE"
                motion_source = "vehicle_movement"

        return {"state": state, "motion_source": motion_source}

    def classify(self, class_name, motion_data):
        if motion_data["state"] == "INACTIVE": return "WAITING"
        if class_name == 'excavator':
            return "DIGGING" if motion_data["motion_source"] == "arm_only" else "SWINGING"
        return "WORKING"