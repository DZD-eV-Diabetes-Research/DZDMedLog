FROM python:3.11
RUN python3 -m pip install --upgrade pip
#RUN apt-get update && apt-get install git -y
ARG APPNAME=DZDMedLog
ARG MODULE_DIR=MedLog/backend
ARG SOURCE_DIR=MedLog/backend/medlogserver
# prep stuff
RUN mkdir -p /opt/$APPNAME/$APPNAME
WORKDIR /opt/$APPNAME
RUN pip install -U pip-tools

# Generate requirements.txt based on depenencies defined in pyproject.toml
COPY $MODULE_DIR/pyproject.toml /opt/$APPNAME/$APPNAME
RUN pip-compile -o /opt/$APPNAME/requirements.txt /opt/$APPNAME/$APPNAME/pyproject.toml

# Install requirements
RUN pip install -U -r /opt/$APPNAME/requirements.txt

# install app
COPY $SOURCE_DIR /opt/$APPNAME/$APPNAME

# copy .git folder to be able to generate version file
COPY .git /opt/$APPNAME/.git
RUN echo "__version__ = '$(python -m setuptools_scm 2>/dev/null | tail -n 1)'" > /opt/$APPNAME/$APPNAME/__version__.py
# Remove git folder to reduce image size
RUN rm -r /opt/$APPNAME/.git

# Install data
RUN mkdir -p /data/db
# set base config
WORKDIR /opt/$APPNAME/$APPNAME
# set base config
ENV SERVER_LISTENING_HOST=0.0.0.0
ENV APP_PROVISIONING_DATA_YAML_FILES='[]'
ENV DRUG_TABLE_PROVISIONING_SOURCE_DIR=/data/provisioning/arzneimittelindex
ENV SQL_DATABASE_URL=sqlite+aiosqlite:////data/db/local.sqlite

CMD [ "python", "./main.py" ]