# Все make-команды предназначены для запуска внутри Docker-контейнера

nginx_conf_dir := /etc/nginx/http.d/
certs_dir := /tmp/certs/

prepare-env:
	@ echo 'Generating nginx config from template...'
# 	вставка директив `allow`
	@ allowed_ips=''; \
	for ip in $$(echo '$(allowed_ips)' | tr ',' ' '); do \
		allowed_ips="$$allowed_ips\n\t\tallow $$ip;"; \
	done; \
	sed -i -E "s|(deny all;)|$$allowed_ips\n\t\t\1|" $(nginx_template)
# 	интерполяция переменных
# 	см. https://github.com/nginxinc/docker-nginx/blob/master/entrypoint/20-envsubst-on-templates.sh
	@ defined_envs=$$(printf '$${%s} ' $$(awk "END { for (name in ENVIRON) { print name } }" < /dev/null )); \
	envsubst "$$defined_envs" < $(nginx_template) > '$(addprefix $(nginx_conf_dir), app.conf)'
	@ rm -f '$(addprefix $(nginx_conf_dir), default.conf)'
	@ nginx -t

start-app:
	@ echo 'Starting nginx...'
	@ nginx -g 'pid /tmp/nginx.pid;'
	@ echo 'Starting app...'
	@ mkdir -p $$LOGS_DIR; \
	mkdir '$(certs_dir)'; \
	cert_path='$(addprefix $(certs_dir), payment-api-cert_default.pem)'; \
	echo "$$PAYMENT_API_DEFAULT_CERT" > $$cert_path; \
	PAYMENT_API_DEFAULT_CERT_PATH=$$cert_path poetry run python src/app/main.py

lint:
	@ echo 'Running linting...'
	@ poetry run flake518

test:
	@ echo 'Running unit tests...'
	@ poetry run pytest
