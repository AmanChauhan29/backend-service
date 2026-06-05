#!/bin/bash

set -e

# Log everything

exec > >(tee /var/log/bootstrap.log)
exec 2>&1

echo "====================================="
echo "BOOTSTRAP STARTED"
echo "====================================="

# Variables

APP_NAME="backend-service"
APP_DIR="/opt/backend-service"
SECRET_NAME="application/prod"
REPO_URL="https://github.com/AmanChauhan29/backend-service.git"

echo "Updating system..."

yum update -y

echo "Installing packages..."

yum install -y \
python3.11 \
python3.11-pip \
python3.11-devel \
git \
nginx \
ruby \
wget \
jq
# Install CodeDeploy agent
cd /tmp
wget https://aws-codedeploy-ap-south-1.s3.ap-south-1.amazonaws.com/latest/install
chmod +x install
sudo ./install auto
echo "codedeploy-agent installation completed"

echo "Creating application directory..."

mkdir -p /opt

cd /opt

# Clone repository

if [ ! -d "$APP_DIR" ]; then
    echo "Cloning repository..."

    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "Creating virtual environment..."

python3.11 -m venv venv

source venv/bin/activate

echo "Upgrading pip..."

pip install --upgrade pip

echo "Installing requirements..."

pip install -r requirements.txt

echo "Fetching secrets..."

mkdir -p /etc/fastapi

SECRET=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_NAME" \
  --query SecretString \
  --output text)

echo "$SECRET" | jq -r '
to_entries
| map("\(.key)=\(.value)")
| .[]
' > /etc/fastapi/app.env

chmod 600 /etc/fastapi/app.env

echo "Environment file created"

cat <<EOF >/etc/systemd/system/backend-service.service
[Unit]
Description=Backend Service
After=network.target

[Service]

User=ec2-user
Group=ec2-user

WorkingDirectory=/opt/backend-service

EnvironmentFile=/etc/fastapi/app.env

ExecStart=/opt/backend-service/venv/bin/gunicorn \
main:app \
-k uvicorn.workers.UvicornWorker \
--bind 127.0.0.1:8000 \
--workers 4

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Systemd service created"

cat <<EOF >/etc/nginx/conf.d/backend-service.conf
server {

    listen 80;

    server_name localhost;

    location / {

        proxy_pass http://127.0.0.1:8000;

        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }
}
EOF

echo "Nginx configuration created"

nginx -t

systemctl daemon-reload

systemctl enable nginx
systemctl restart nginx

systemctl enable backend-service
systemctl restart backend-service

echo "Waiting for application startup..."

sleep 10

echo "Checking service status..."

systemctl status backend-service --no-pager || true

curl http://127.0.0.1:8000/health || true

echo "====================================="
echo "BOOTSTRAP COMPLETED"
echo "====================================="