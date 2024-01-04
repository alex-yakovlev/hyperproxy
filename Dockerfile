FROM python:3.11-alpine

WORKDIR /app

# системные зависимости
RUN apk add tini~=0.19 && \
    pip3 install poetry~=1.7

# зависимости проекта
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root

COPY src ./src

# см. https://python-poetry.org/docs/faq/#poetry-busts-my-docker-cache-because-it-requires-me-to-copy-my-source-files-in-before-installing-3rd-party-dependencies
RUN poetry install --only-root

ARG APP_ENV=production
ENV APP_ENV=$APP_ENV

ENV APP_LISTEN_PORT=8080
EXPOSE $APP_LISTEN_PORT

# см. https://github.com/krallin/tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["poetry", "run", "python", "src/app/server.py"]
