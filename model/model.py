from roboflow import Roboflow
from ultralytics import YOLO
import os
from dotenv import load_dotenv
from collections import Counter

def training_model():
    load_dotenv(dotenv_path="/Users/Internet/Documents/Coding/FridgeSense/.env")
    rf_api = os.getenv("ROBOFLOW_API_KEY")

    rf = Roboflow(api_key = rf_api)
    project = rf.workspace("computer-vision-group-ji0bm").project("group_work")
    version = project.version(2)
    dataset = version.download("yolov8")

    model = YOLO("yolov8n.pt")

    results = model.train(
        data=f"{dataset.location}/data.yaml", 
        epochs=20, 
        imgsz=640, 
        batch=16, 
        device="mps",
        workers=2,
        amp=False
    )

def load_model():
    global model
    model = YOLO("model/best.pt")


def predict_image(img_path):
    return model.predict(source=img_path, conf=0.25)

pantry = {}

load_model()
results = predict_image("/Users/Internet/Desktop/Coding/FridgeSense/download.jpeg")

def ingredients(results):
    foods = []
    for r in results:
        labels = r.names
        
        for box in r.boxes:
            classid = int(box.cls[0])

            foods.append(labels[classid])

    pantry = Counter(foods)
    return pantry, foods

