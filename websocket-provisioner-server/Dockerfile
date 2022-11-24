FROM python:3.9-alpine

RUN mkdir -p /opt/project
WORKDIR /opt/project

COPY requiremnets.in .
RUN pip3 install -r requiremnets.in

COPY src/app.py .

CMD ["python", "-m", "src.app"]
