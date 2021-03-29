FROM python:3.7-slim-buster

RUN apt update && \
    apt install -y build-essential pkg-config libsodium-dev libsecp256k1-dev libgmp-dev make curl git && \
    rm -rf /var/lib/apt/lists/*
RUN pip install poetry
RUN useradd -ms /bin/bash pytezos_dapps

RUN mkdir /home/pytezos_dapps/src
RUN mkdir /home/pytezos_dapps/project
COPY Makefile pyproject.toml poetry.lock README.md /home/pytezos_dapps/src/
# We want to copy our code at the last layer but not to break poetry's "packages" section
RUN mkdir -p /home/pytezos_dapps/src/src/michelson_kernel && \
    touch /home/pytezos_dapps/src/src/michelson_kernel/__init__.py && \
    mkdir -p /home/pytezos_dapps/src/src/pytezos && \
    touch /home/pytezos_dapps/src/src/pytezos/__init__.py

WORKDIR /home/pytezos_dapps/src
RUN poetry config virtualenvs.in-project true
RUN make install DEV=0

COPY . /home/pytezos_dapps/src/
RUN chown -R pytezos_dapps /home/pytezos_dapps/

USER pytezos_dapps

WORKDIR /home/jupyter/project
EXPOSE 8888
ENTRYPOINT [ "/home/pytezos_dapps/src/.venv/bin/python", "-m" "pytezos_dapps" ]