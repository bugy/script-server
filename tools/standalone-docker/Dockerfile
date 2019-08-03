# docker build --tag script-server-local --file Dockerfile_standalone .
# docker run -p 5000:5000 script-server-local 
FROM ubuntu:18.04

RUN apt-get update \
 && apt-get install -y python3-pip python3-dev wget curl unzip

RUN wget `curl -s https://api.github.com/repos/bugy/script-server/releases/latest | grep browser_download_url | cut -d '"' -f 4` \
  && unzip script-server.zip -d script-server

WORKDIR script-server

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "launcher.py", "-f", "/app/config/guess_number.json"]