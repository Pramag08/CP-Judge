ARG NODE_IMAGE=node@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da
ARG PYTHON_IMAGE=python@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
FROM ${NODE_IMAGE} AS assets
WORKDIR /asset-tools
COPY package.json package-lock.json ./
RUN npm ci && npm ls --json > /asset-tools/versions.json
COPY site /app
ENV PATH="/asset-tools/node_modules/.bin:$PATH"
RUN cd /app && ./make_style.sh && mkdir -p /app/resources/a09 && \
    cp /asset-tools/node_modules/jquery/dist/jquery.min.js /app/resources/a09/jquery.min.js && \
    cp -r /asset-tools/node_modules/ace-builds/src-min-noconflict /app/resources/a09/ace
FROM ${PYTHON_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev gettext git curl && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.in requirements.lock /setup/
RUN mkdir -p /metadata && python -m pip install --no-cache-dir -r /setup/requirements.lock --report /metadata/install-report.json && \
    python -m pip check && python -m pip freeze --all > /metadata/requirements.lock && \
    dpkg-query -W > /metadata/os-packages.tsv
COPY --from=assets /app /app
COPY --from=assets /asset-tools/package.json /metadata/package.json
COPY --from=assets /asset-tools/package-lock.json /metadata/package-lock.json
COPY --from=assets /asset-tools/versions.json /metadata/npm-versions.json
COPY local_settings.py /app/dmoj/local_settings.py
RUN useradd --create-home --uid 10001 site && chown -R site:site /app /metadata
USER site
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
