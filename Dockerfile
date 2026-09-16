# Stage 1: export locked project deps from Poetry (no poetry needed at runtime)
FROM python:3.12-slim AS deps-export
RUN pip install --no-cache-dir poetry==2.3.4 poetry-plugin-export
WORKDIR /src
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

# Stage 2: Airflow image + an ISOLATED venv for the pipeline's own deps
FROM apache/airflow:3.3.1-python3.12

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends make curl tar git \
    && rm -rf /var/lib/apt/lists/*

# Isolated venv for the pipeline's own deps (dbt-bigquery, google-cloud-*, pandas),
# kept separate from Airflow's own Python environment on purpose so neither
# dependency set can disturb the other's pinned transitive requirements.
RUN python -m venv /opt/pysettlens
COPY --from=deps-export /src/requirements.txt /tmp/requirements.txt
RUN /opt/pysettlens/bin/pip install --no-cache-dir -r /tmp/requirements.txt

USER airflow

# The official entrypoint sets HOME=/home/airflow so Python finds the
# airflow package under /home/airflow/.local even when the container
# runs as an arbitrary numeric UID (docker-compose's AIRFLOW_UID). We
# bypass that entrypoint for airflow-init (entrypoint: /bin/bash), so
# bake HOME into the image itself to keep that working either way.
ENV HOME=/home/airflow
