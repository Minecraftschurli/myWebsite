import cv2
#
COLOR = {'WHITE': [255, 255, 255], 'BLUE': [255, 0, 0], 'GREEN': [0, 255, 0], 'RED': [0, 0, 255], 'BLACK': [0, 0, 0]}
#
# if platform.system() is not 'Windows':
#     DIR = '/home/pi/opencv-3.4.3/data/haarcascades/'
# else:
#     DIR = cv2.haarcascades
#
# upperbody_cascade = cv2.CascadeClassifier(DIR + 'haarcascade_upperbody.xml')
# lowerbody_cascade = cv2.CascadeClassifier(DIR + 'haarcascade_lowerbody.xml')
# fullbody_cascade = cv2.CascadeClassifier(DIR + 'haarcascade_fullbody.xml')
# frontalface_cascade = cv2.CascadeClassifier(DIR + 'haarcascade_frontalface_alt.xml')
# profileface_cascade = cv2.CascadeClassifier(DIR + 'haarcascade_profileface.xml')
#
# cascades = [upperbody_cascade, lowerbody_cascade, fullbody_cascade, frontalface_cascade, profileface_cascade]
#
#
# modelFile = "/home/pi/webapp/libs/models/opencv_face_detector_uint8.pb"
# configFile = "/home/pi/webapp/libs/models/opencv_face_detector.pbtxt"
# net = cv2.dnn.readNetFromTensorflow(modelFile, configFile)
# conf_threshold = 0.7
#
#
# def draw_box(image, x, y, w, h, color=None):
#     if color is None:
#         color = COLOR['WHITE']
#     cv2.line(image, (x, y), (x + int(w / 5), y), color, 2)
#     cv2.line(image, (x + int((w / 5) * 4), y), (x + w, y), color, 2)
#     cv2.line(image, (x, y), (x, y + int(h / 5)), color, 2)
#     cv2.line(image, (x + w, y), (x + w, y + int(h / 5)), color, 2)
#     cv2.line(image, (x, (y + int(h / 5 * 4))), (x, y + h), color, 2)
#     cv2.line(image, (x, (y + h)), (x + int(w / 5), y + h), color, 2)
#     cv2.line(image, (x + int((w / 5) * 4), y + h), (x + w, y + h), color, 2)
#     cv2.line(image, (x + w, (y + int(h / 5 * 4))), (x + w, y + h), color, 2)
#
#
# def detect_face_open_cv_dnn(nn, frame):
#     frame_opencv_dnn = frame.copy()
#     frame_height = frame_opencv_dnn.shape[0]
#     frame_width = frame_opencv_dnn.shape[1]
#     blob = cv2.dnn.blobFromImage(frame_opencv_dnn, 1.0, (300, 300), [104, 117, 123], False, False)
#
#     nn.setInput(blob)
#     detections = nn.forward()
#     bboxes = []
#     for i in range(detections.shape[2]):
#         confidence = detections[0, 0, i, 2]
#         if confidence > conf_threshold:
#             x1 = int(detections[0, 0, i, 3] * frame_width)
#             y1 = int(detections[0, 0, i, 4] * frame_height)
#             x2 = int(detections[0, 0, i, 5] * frame_width)
#             y2 = int(detections[0, 0, i, 6] * frame_height)
#             bboxes.append([x1, y1, x2, y2])
#             draw_box(frame_opencv_dnn, x1, y1, x1 - x2, y1 - y2, COLOR['GREEN'])
#     return frame_opencv_dnn, bboxes


class VideoCamera(object):

    def __init__(self, cam_id='', **kwargs):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.people_detected = False
        if cam_id.isnumeric():
            self.video = cv2.VideoCapture(int(cam_id))
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        elif cam_id.endswith('.mp4'):
            self.video = cv2.VideoCapture(cam_id)
        else:
            self.video = cv2.VideoCapture(None)

        if 'use_detection' in kwargs:
            self.use_detection = kwargs['use_detection']
        else:
            self.use_detection = False

    def __del__(self):
        self.video.release()

    def get_frame(self):
        global net
        _, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        if self.use_detection:
            detects = []
        #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #     for detect in frontalface_cascade.detectMultiScale(gray, 1.1, 4):
        #         detects.append(detect)
        #     for cascade in cascades:
        #         for detect in cascade.detectMultiScale(gray, 1.1, 4):
        #             detects.append(detect)
        #
            # image, detects = detect_face_open_cv_dnn(net, image)
            # self.people_detected = len(detects) > 0
            # for x, y, w, h in detects:
            #     draw_box(image, x, y, w, h, COLOR['BLUE'])

        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def get_people_detected(self):
        return self.people_detected
