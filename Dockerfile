FROM python:3.11.6-alpine3.18

ENV PIP_NO_CACHE_DIR off
ENV PIP_ROOT_USER_ACTION ignore

WORKDIR /files

COPY requirements.txt /requirements.txt
COPY fivedesc.py /usr/bin/5desc

RUN pip install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["/usr/bin/5desc"]
