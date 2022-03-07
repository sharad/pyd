

FROM python:3.8-slim

RUN pip install jinja2 datetime json base64 netifaces traceback

COPY run.py /

CMD /run.py






