import cv2
from flask import Blueprint, Response, stream_with_context

from libs import configuration
from .decorators import *
from .functions import *

camera = Blueprint('camera', __name__)

cams = [0]


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
        _, image = self.video.read()
        if self.use_detection:
            from libs.face_detection import detect_face_open_cv_dnn
            image, detects = detect_face_open_cv_dnn(image)
            self.people_detected = len(detects) > 0

        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def get_people_detected(self):
        return self.people_detected


@camera.route('/cam')
@permission_required('camera')
@check_ip
def cam():
    if configuration['camera']['status']:
        return render_with_nav('cam')
    else:
        abort(404)


@camera.route('/video_feed/<cam_id>')
@permission_required('camera')
@check_ip
def video_feed(cam_id='0'):
    if (not configuration['camera']['status']) or (not cam_id.isnumeric()) or (int(cam_id) not in cams):
        abort(404)
    """Video streaming route. Put this in the src attribute of an img tag."""
    video_cameras = [VideoCamera('0', use_detection=configuration['camera']['use_detect'])]

    def gen_camera(camera):
        """Video streaming generator function."""
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(stream_with_context(gen_camera(video_cameras[int(cam_id)])),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
