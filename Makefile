# Все make-команды предназначены для запуска внутри Docker-контейнера

nginx_conf_dir := /etc/nginx/http.d/

prepare-env:
	@ echo 'Generating nginx config from template...'
# 	вставка директив `allow`
	@ allowed_ips=''; \
	for ip in $$(echo '$(allowed_ips)' | tr ',' ' '); do \
		allowed_ips="$$allowed_ips\n\tallow $$ip;"; \
	done; \
	sed -i -E "s|(deny all;)|$$allowed_ips\n\t\1|" $(nginx_template)
# 	интерполяция переменных
# 	см. https://github.com/nginxinc/docker-nginx/blob/master/entrypoint/20-envsubst-on-templates.sh
	@ defined_envs=$$(printf '$${%s} ' $$(awk "END { for (name in ENVIRON) { print name } }" < /dev/null )); \
	envsubst "$$defined_envs" < $(nginx_template) > '$(addprefix $(nginx_conf_dir), app.conf)'
	@ rm '$(addprefix $(nginx_conf_dir), default.conf)'
	@ nginx -t

start-app:
	@ echo 'Starting nginx...'
	@ nginx -g 'pid /tmp/nginx.pid;'
	@ echo 'Importing GPG key...'
	@ echo "$$SOPS_KEY" | gpg --batch --import -
	@ echo 'Starting app...'
# 	см. https://github.com/getsops/sops#passing-secrets-to-other-processes
	@ env_secrets=$$(if [[ "$$APP_ENV" == 'dev' ]]; then echo 'secrets/secrets.dev.yml'; else echo 'secrets/secrets.yml'; fi); \
	echo $$env_secrets | xargs -I % sops exec-env % "sops exec-file --no-fifo secrets/payment-api-cert_default.pem 'PAYMENT_API_DEFAULT_CERT_PATH={} poetry run python src/app/main.py'"

lint:
	@ echo 'Running linting...'
	@ poetry run flake518

test:
	@ echo 'Running unit tests...'
	@ poetry run pytest
