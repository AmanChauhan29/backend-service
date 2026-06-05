#!bin/bash
sudo yum update -y
sudo yum upgrade -y
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
