

FROM python:3.8-slim

RUN pip install jinja2 netifaces traceback

COPY run.py /

CMD /run.py






