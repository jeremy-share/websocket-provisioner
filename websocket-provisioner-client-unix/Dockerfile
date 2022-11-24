FROM python:3.9

RUN     DEBIAN_FRONTEND=noninteractive apt-get update \
    &&  DEBIAN_FRONTEND=noninteractive apt-get install -y \
          dmidecode

RUN mkdir -p /opt/project
WORKDIR /opt/project

COPY requirements.in .
RUN pip3 install -r requirements.in

COPY websocket-provisioner-client-unix.py .

CMD ["python", "websocket-provisioner-client-unix.py"]
