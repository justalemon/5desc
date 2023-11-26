FROM python:3.12.0-alpine3.18

ENV PIP_NO_CACHE_DIR off
ENV PIP_ROOT_USER_ACTION ignore

COPY requirements.txt .
COPY fivedesc.py .

RUN pip install --no-cache-dir -r requirements.txt
