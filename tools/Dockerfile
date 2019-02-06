FROM python:3.6

COPY build/script-server /app
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD [ "python3", "launcher.py" ]