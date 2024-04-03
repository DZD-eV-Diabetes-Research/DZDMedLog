FROM python:3.11
RUN python3 -m pip install --upgrade pip
#RUN apt-get update && apt-get install git -y


# install requirements
RUN mkdir -p /opt/medlog/
COPY requirements.txt /opt/medlog/
COPY pyproject.toml /opt/medlog/
RUN pip install  --no-cache-dir -r /opt/medlog/requirements.txt

# install app
COPY medlogserver /opt/medlog/medlogserver
WORKDIR /opt/medlog/medlogserver


# Install data
RUN mkdir -p /data/provisioning
COPY medlogserver /data/provisioning/demodata
RUN mkdir -p /data/db
# set base config
ENV SERVER_LISTENING_HOST=0.0.0.0
ENV APP_PROVISIONING_DATA_YAML_FILES='[]'
ENV DRUG_TABLE_PROVISIONING_SOURCE_DIR=/data/provisioning/arzneimittelindex
ENV SQL_DATABASE_URL=sqlite+aiosqlite:////data/db/local.sqlite


CMD [ "python", "./main.py" ]