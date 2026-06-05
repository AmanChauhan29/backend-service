#!/bin/bash
set e

sudo systemctl stop backend-service || true

mkdir -p /opt/backend-service

cd /opt/backend-service

python3 -m venv venv || true

source venv/bin/activate

pip install -r requirements.txt

sudo systemctl daemon-reload

sudo systemctl restart backend-service

curl -f http://localhost:8000/health