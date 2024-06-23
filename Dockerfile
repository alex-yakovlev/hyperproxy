FROM python:3.11-alpine3.20

WORKDIR /app

# системные зависимости
RUN apk add \
        tini~=0.19 \
        make~=4.4 \
        nginx~=1.26 \
        gettext-envsubst~=0.22 \
    && pip3 install poetry~=1.7

# зависимости проекта
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root

COPY src ./src
COPY Makefile .

# см. https://python-poetry.org/docs/faq/#poetry-busts-my-docker-cache-because-it-requires-me-to-copy-my-source-files-in-before-installing-3rd-party-dependencies
RUN poetry install --only-root

ARG APP_ENV=production
ARG INITIATOR_IPS

ENV APP_LISTEN_PORT=8081
ENV PROXY_LISTEN_PORT=8080
EXPOSE $PROXY_LISTEN_PORT

COPY nginx.conf.template /tmp/app.conf.template
RUN make prepare-env allowed_ips=$INITIATOR_IPS nginx_template=/tmp/app.conf.template

# см. https://github.com/krallin/tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["make", "start-app"]
