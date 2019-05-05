# download release of Script-Server
wget `curl -s https://api.github.com/repos/bugy/script-server/releases/latest | grep browser_download_url | cut -d '"' -f 4`
unzip script-server.zip

# create virtual environment
python3 -m venv virtual_env

# dependencies installation
virtual_env/bin/pip install wheel 
wget https://github.com/bugy/script-server/raw/master/requirements.txt
virtual_env/bin/pip install -r requirements.txt

# start 
virtual_env/bin/python3 launcher.py

# start with custom configuration 
# virtual_env/bin/python3 launcher.py  -f /home/me/configs/script-server.json
