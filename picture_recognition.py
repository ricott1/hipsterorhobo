import cv2
import numpy as np
import os, sys


def get_image_from_path(path):
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image, gray

def get_faces(gray):
    cascadePath = "data/haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath);
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    return faces

def recognize(gray, x, y, w, h):
    id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
    return id, confidence
    

font = cv2.FONT_HERSHEY_SIMPLEX
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('data/hipster_trainer.yml')
names = ['None', 'Hipster', 'Hobo'] 
    
if __name__ == '__main__':
    
    image, gray = get_image_from_path(sys.argv[1])
    faces = get_faces(gray)

    for (x, y, w, h) in faces:
        id, confidence = recognize(gray, x, y, w, h)
        cv2.rectangle(image, (x,y), (x+w,y+h), (0,255-2.55*confidence,0), 2)
        # Check if confidence is less them 100 ==> "0" is perfect match 
        if (confidence < 100):
            id = names[id]
            confidence = "  {0}%".format(round(100 - confidence))
        else:
            id = "unknown"
            confidence = "  {0}%".format(round(100 - confidence))
        
        cv2.putText(image, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(image, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  

    cv2.imshow("Faces found", image)
    cv2.waitKey(0)