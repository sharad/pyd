

FROM python:3.11.0a5-slim-buster

COPY pip install jinja2

COPY run.py /

CMD /run.py






