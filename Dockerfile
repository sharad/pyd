

FROM python:3.8-slim

EXPOSE 80

RUN pip install -r requirement.txt

COPY run.py /

CMD /run.py






