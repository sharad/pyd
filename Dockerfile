

FROM python:3.8-slim

EXPOSE 80

RUN pip install jinja2 netifaces

COPY run.py /

CMD /run.py






