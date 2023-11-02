FROM python:3.11-slim

ENV PORT=8000

RUN apt update
RUN apt install libpq5 -y
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# copy files
COPY pyproject.toml pdm.lock /project/
COPY . /project

WORKDIR /project
RUN pdm install --prod --no-lock --no-editable

STOPSIGNAL SIGINT

CMD ["pdm", "start"]