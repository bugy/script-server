FROM debian:jessie-slim
RUN apt-get update && apt-get install -y python3 curl && rm -rf /var/lib/apt/lists/*
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py && rm get-pip.py
WORKDIR /app/
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY conf /app/conf/
COPY src /app/src/
COPY web /app/web/
COPY launcher.py /app/launcher.py
EXPOSE 5000
CMD [ "python3", "launcher.py" ]
