FROM python:3.11
RUN python3 -m pip install --upgrade pip
#RUN apt-get update && apt-get install git -y
RUN mkdir -p /opt/medlogserver
WORKDIR /opt/medlogserver

ADD . /opt/medlogserver
ENV LISTENING_HOST=0.0.0.0
RUN pip install  --no-cache-dir -e ./MedLog/backend
CMD [ "medlogserver" ]