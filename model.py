import os
from collections import Counter

from dotenv import load_dotenv

DEFAULT_WEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "model", "best.pt")


def training_model():
    """Retrains from the Roboflow dataset https://universe.roboflow.com/computer-vision-group-ji0bm/group_work Run by hand, not from the app."""
    from roboflow import Roboflow
    from ultralytics import YOLO

    load_dotenv()
    rf_api = os.getenv("ROBOFLOW_API_KEY")

    rf = Roboflow(api_key=rf_api)
    project = rf.workspace("computer-vision-group-ji0bm").project("group_work")
    version = project.version(2)
    dataset = version.download("yolov8")

    model = YOLO("yolov8n.pt")
    model.train(
        data=f"{dataset.location}/data.yaml",
        epochs=20, imgsz=640, batch=16,
        device="mps", workers=2, amp=False,
    )


def weights_available(path=DEFAULT_WEIGHTS):
    return os.path.isfile(path)


def load_model(weights_path=DEFAULT_WEIGHTS):
    from ultralytics import YOLO
    return YOLO(weights_path)


def predict_image(model, img_path, conf=0.25):
    return model.predict(source=img_path, conf=conf)


def ingredients_from_results(results):
    foods = []
    for r in results:
        labels = r.names
        for box in r.boxes:
            foods.append(labels[int(box.cls[0])])
    return Counter(foods), foods
