#!/usr/bin/env bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install screen
sudo pip3 install flask
sudo pip3 install meinheld
sudo pip3 install netaddr
sudo screen python3 ./app.py