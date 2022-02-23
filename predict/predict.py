import os
from predict.preprocess import preprocess
from tensorflow import keras
import tensorflow as tf
from application.small_keras_inception_resnet_v2 import SmallKerasInceptionResNetV2
import numpy as np
from pathlib import Path
MODEL_PATH = os.path.join(str(Path(__file__).parent.parent), "model", "best", "best.weights")

model = SmallKerasInceptionResNetV2()
model.load_weights(MODEL_PATH)

LABELS = []
CLASSES = []
with open('class_to_label.txt','r', encoding='utf8') as f:
    for line in f.readlines():
        _label, _class = line.strip().split(',')
        LABELS.append(int(_label))
        CLASSES.append(_class)
LABELS = np.array(LABELS)
CLASSES = np.array(CLASSES)

def predict():
    images = preprocess() # n x 299 x 299 x 3
    predicts = model.predict(images)  # n x 150
    labels = np.argmax(predicts, axis=1) # n
    return CLASSES[labels]
    
    
    