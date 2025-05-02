## ==================== Server setup cmds ====================

# Ready
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv cmake build-essential

# python venv
cd ~ && python3 -m venv venv
source venv/bin/activate

# python package install
cd ~/tinyllama1b/python_proj
pip install -r requirements.txt


# ==================== CV_Builder ====================
cd ~/tinyllama1b/python_proj/cv_builder

# test service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# add to systemd
sudo nano /etc/systemd/system/fastapi_cv.service

### in fastapi_cv.service ----------
[Unit]
Description=FastAPI CV Generator Service
After=network.target

[Service]
User=azureuser
WorkingDirectory=/home/azureuser/tinyllama1b/python_proj/cv_builder
ExecStart=/home/azureuser/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment="PATH=/home/azureuser/venv/bin"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
### ------------------------------

# enable service file
sudo systemctl daemon-reload
sudo systemctl enable fastapi_cv.service
sudo systemctl start fastapi_cv.service

# check
sudo systemctl status fastapi_cv.service

# ==================== Chatbot ====================
cd ~/tinyllama1b/python_proj/chatbot

# test function
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# add to systemd
sudo nano /etc/systemd/system/chatbot.service

### in chatbot.service ----------
[Unit]
Description=FastAPI Chatbot Service
After=network.target

[Service]
User=azureuser
WorkingDirectory=/home/azureuser/tinyllama1b/python_proj/chatbot
ExecStart=/home/azureuser/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
Environment="PATH=/home/azureuser/venv/bin"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
### ------------------------------

# enable service file
sudo systemctl daemon-reload
sudo systemctl enable chatbot.service
sudo systemctl start chatbot.service

# check
sudo systemctl status chatbot.service