

FROM python:3.8-slim

RUN pip install jinja2 netifaces

COPY run.py /

CMD /run.py






