#FRONTEND BUILD STAGE


FROM oven/bun AS medlog-frontend-build
RUN mkdir /frontend_build
WORKDIR /frontend_build
COPY MedLog/frontend /frontend_build
RUN rm -rf /frontend_build/.nuxt
RUN rm -rf /frontend_build/.output
RUN rm -rf /frontend_build/node_modules
RUN bun install && bun run build && bunx nuxi generate

# BACKEND BUILD AND RUN STAGE
FROM python:3.11 AS medlog-backend
ARG APP_VERSION=""   # empty by default; only set for release builds
ARG BASEDIR=/opt/medlog
ARG MODULENAME=medlogserver
ENV MEDLOG_DOCKER_BASEDIR=$BASEDIR
ENV DOCKER_MODE=1
ENV FRONTEND_FILES_DIR=$BASEDIR/medlogfrontend

# prep stuff
RUN mkdir -p $BASEDIR/$MODULENAME
RUN mkdir -p $FRONTEND_FILES_DIR
RUN mkdir -p /data
RUN mkdir -p /data/db
RUN mkdir -p /data/provisioning/database
RUN mkdir -p /data/provisioning/dummy_drugset

# Copy frontend dist from pre stage
COPY --from=medlog-frontend-build /frontend_build/.output/public $FRONTEND_FILES_DIR


# Install Server
WORKDIR $BASEDIR

# RUN python3 -m pip install --upgrade pip # comment: removed due to https://github.com/jazzband/pip-tools/issues/2252 which broke the build process
RUN pip install -U pip-tools

# Generate requirements.txt based on depenencies defined in pyproject.toml
#COPY MedLog/backend/pyproject.toml $BASEDIR/medlogserver/pyproject.toml
#RUN pip-compile -o $BASEDIR/requirements.txt $BASEDIR/medlogserver/pyproject.toml
COPY MedLog/backend/requirements.txt $BASEDIR/requirements.txt

# Install requirements
RUN pip install -U -r $BASEDIR/requirements.txt

# install app
COPY MedLog/backend/$MODULENAME $BASEDIR/$MODULENAME

# copy .git folder to be able to generate version file
COPY .git $BASEDIR/.git
RUN if [ -n "$APP_VERSION" ]; then \
    python3 $BASEDIR/$MODULENAME/main.py --set_version_file --app_version "$APP_VERSION"; \
    else \
    python3 $BASEDIR/$MODULENAME/main.py --set_version_file; \
    fi
#RUN echo "__version__ = '$(python -m setuptools_scm 2>/dev/null | tail -n 1)'" > $BASEDIR/medlogserver/__version__.py
# Remove git folder
RUN rm -r $BASEDIR/.git

#Copy default app data provisioning files
COPY MedLog/backend/provisioning_data $BASEDIR/provisioning/database
RUN mv $BASEDIR/provisioning/database/dummy_drugset/20251228/* /data/provisioning/dummy_drugset/


# set base config
WORKDIR $BASEDIR/$MODULENAME
# set base config
ENV SERVER_LISTENING_HOST=0.0.0.0
ENV APP_PROVISIONING_DATA_YAML_FILES='[]'
ENV DRUG_TABLE_PROVISIONING_SOURCE_DIR=/data/provisioning/dummy_drugset
ENV SERVER_HOSTNAME=localhost
ENV EXPORT_CACHE_DIR=/data/export
ENV SQL_DATABASE_URL="sqlite+aiosqlite:////data/db/medlog.db"
ENTRYPOINT ["python", "./main.py"]
#CMD [ "python", "./main.py" ]