FROM python:3.9-slim

COPY build/script-server /app
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD [ "python3", "launcher.py" ]