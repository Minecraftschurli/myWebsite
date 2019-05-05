#!/bin/bash

cd /home/pi/webapp
sudo su
source /home/pi/opencv/OpenCV-master-py3/bin/activate
pip3 install flask
pip3 install flask-bcrypt
pip3 install flask-login
pip3 install meinheld
pip3 install netaddr
pip3 install --upgrade tensorflow
