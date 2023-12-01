FROM python:3.11.6-alpine3.18

ENV PIP_NO_CACHE_DIR off
ENV PIP_ROOT_USER_ACTION ignore

WORKDIR /app

COPY requirements.txt .
COPY fivedesc.py .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/app/fivedesc.py"]
