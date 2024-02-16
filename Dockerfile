FROM python:3.10

ENV EMAIL_MONITOR_CONFIG=/usr/app/monitor/config.json

COPY . /usr/app/monitor

WORKDIR /usr/app/monitor

RUN pip3 install .

ENTRYPOINT [ "monitor" ]