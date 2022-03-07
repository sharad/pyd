

FROM python:3.11.0a5-slim-buster

RUN pip install jinja2 datetime json base64 netifaces traceback

COPY run.py /

CMD /run.py






