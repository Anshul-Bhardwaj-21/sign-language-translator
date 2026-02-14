import cv2
# import numpy as np

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Camera opened successfully")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Can't recieve frame (stream end?). Exiting...")
        break

    cv2.imshow('Live Camera Feed', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()