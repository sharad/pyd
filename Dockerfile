

FROM python:3.8-slim

EXPOSE 80

COPY requirement.txt requirement.txt
RUN pip install -r requirement.txt

COPY run.py /

CMD /run.py






