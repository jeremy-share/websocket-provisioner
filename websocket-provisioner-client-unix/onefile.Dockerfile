FROM python:3.11

RUN     DEBIAN_FRONTEND=noninteractive apt-get update \
    &&  DEBIAN_FRONTEND=noninteractive apt-get install -y \
          dmidecode

RUN mkdir -p /opt/project
WORKDIR /opt/project

COPY dist/websocket-provisioner-client-unix /opt/project/websocket-provisioner-client-unix
COPY run.sh /opt/project/run.sh

CMD ["/opt/project/websocket-provisioner-client-unix"]
