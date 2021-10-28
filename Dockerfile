# https://hub.docker.com/_/python/
FROM python:3

WORKDIR /app

# Set up depencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV HOST=0.0.0.0
ENV PORT=5000

COPY . .
CMD [ "python", "./main.py" ]
EXPOSE ${PORT}/tcp
