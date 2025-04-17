#FRONTEND BUILD STAGE


FROM oven/bun AS medlog-frontend-build
RUN mkdir /frontend_build
WORKDIR /frontend_build
COPY MedLog/frontend /frontend_build
RUN bun install && bun run build && bunx nuxi generate

# BACKEND BUILD AND RUN STAGE
FROM python:3.11 AS medlog-backend
ARG BASEDIR=/opt/medlog
ARG MODULENAME=medlogserver
ENV MEDLOG_DOCKER_BASEDIR=$BASEDIR
ENV DOCKER_MODE=1
ENV FRONTEND_FILES_DIR=$BASEDIR/medlogfrontend

# prep stuff
RUN mkdir -p $BASEDIR/medlogserver
RUN mkdir -p $BASEDIR/medlogfrontend
RUN mkdir -p /data
RUN mkdir -p /data/provisioning/database
RUN mkdir -p /data/provisioning/arzneimittelindex/demo

# Copy frontend dist from pre stage
COPY --from=medlog-frontend-build /frontend_build/.output/public $BASEDIR/medlogfrontend


# Install Server
WORKDIR $BASEDIR

RUN python3 -m pip install --upgrade pip
RUN pip install -U pip-tools

# Generate requirements.txt based on depenencies defined in pyproject.toml
COPY MedLog/backend/pyproject.toml $BASEDIR/medlogserver/pyproject.toml
RUN pip-compile -o $BASEDIR/requirements.txt $BASEDIR/medlogserver/pyproject.toml

# Install requirements
RUN pip install -U -r $BASEDIR/requirements.txt

# install app
COPY MedLog/backend/medlogserver $BASEDIR/medlogserver

# copy .git folder to be able to generate version file
COPY .git $BASEDIR/.git
RUN python3 $BASEDIR/medlogserver/main.py --set_version_file
#RUN echo "__version__ = '$(python -m setuptools_scm 2>/dev/null | tail -n 1)'" > $BASEDIR/medlogserver/__version__.py
# Remove git folder
RUN rm -r $BASEDIR/.git

#Copy default app data provisioning files
COPY MedLog/backend/provisioning_data $BASEDIR/provisioning/database
RUN mv $BASEDIR/provisioning/database/dummy_drugset/20241126/* /data/provisioning/arzneimittelindex/demo/


# set base config
WORKDIR $BASEDIR/medlogserver
# set base config
ENV SERVER_LISTENING_HOST=0.0.0.0
ENV APP_PROVISIONING_DATA_YAML_FILES='[]'
ENV DRUG_TABLE_PROVISIONING_SOURCE_DIR=/data/provisioning/arzneimittelindex/demo
ENV SERVER_HOSTNAME=localhost
ENV EXPORT_CACHE_DIR=/data/export
ENV SQL_DATABASE_URL="sqlite+aiosqlite:///$BASEDIR/data/db/medlog.db"
ENTRYPOINT ["python", "./main.py"]
#CMD [ "python", "./main.py" ]