import platform

from cv2 import cv2

COLOR = {'WHITE': [255, 255, 255], 'BLUE': [255, 0, 0], 'GREEN': [0, 255, 0], 'RED': [0, 0, 255], 'BLACK': [0, 0, 0]}

if platform.system() == 'Linux':
    directory = "/home/pi/webapp/libs"
else:
    directory = "C:/Users/georg/PycharmProjects/website/libs"


modelFile = directory + "/models/opencv_face_detector_uint8.pb"
configFile = directory + "/models/opencv_face_detector.pbtxt"
nn = cv2.dnn.readNetFromTensorflow(modelFile, configFile)
conf_threshold = 0.7


def draw_box(image, x, y, w, h, color=None):
    if color is None:
        color = COLOR['WHITE']
    cv2.line(image, (x, y), (x + int(w / 5), y), color, 2)
    cv2.line(image, (x + int((w / 5) * 4), y), (x + w, y), color, 2)
    cv2.line(image, (x, y), (x, y + int(h / 5)), color, 2)
    cv2.line(image, (x + w, y), (x + w, y + int(h / 5)), color, 2)
    cv2.line(image, (x, (y + int(h / 5 * 4))), (x, y + h), color, 2)
    cv2.line(image, (x, (y + h)), (x + int(w / 5), y + h), color, 2)
    cv2.line(image, (x + int((w / 5) * 4), y + h), (x + w, y + h), color, 2)
    cv2.line(image, (x + w, (y + int(h / 5 * 4))), (x + w, y + h), color, 2)


def detect_face_open_cv_dnn(frame):
    global nn
    frame_opencv_dnn = frame.copy()
    frame_height = frame_opencv_dnn.shape[0]
    frame_width = frame_opencv_dnn.shape[1]
    blob = cv2.dnn.blobFromImage(frame_opencv_dnn, 1.0, None, [104, 117, 123], False, False)

    nn.setInput(blob)
    detections = nn.forward()
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frame_width)
            y1 = int(detections[0, 0, i, 4] * frame_height)
            x2 = int(detections[0, 0, i, 5] * frame_width)
            y2 = int(detections[0, 0, i, 6] * frame_height)
            bboxes.append([x1, y1, x2, y2])
            draw_box(frame_opencv_dnn, x1, y1, x2 - x1, y2 - y1, COLOR['GREEN'])
    return frame_opencv_dnn, bboxes
