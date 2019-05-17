#!/bin/bash

cd /home/pi/webapp
sudo su
source ../opencv/OpenCV-master-py3/bin/activate
pip3 install flask
pip3 install flask-bcrypt
pip3 install flask-login
pip3 install flask-sqlalchemy
pip3 install flask-mail
pip3 install flask-user
pip3 install meinheld
pip3 install netaddr
pip3 install tensorflow
