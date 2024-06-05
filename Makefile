# Все make-команды предназначены для запуска внутри Docker-контейнера

# см. https://github.com/getsops/sops#passing-secrets-to-other-processes
start-app:
	@ echo "Starting main app..."
	@ echo "$$SOPS_KEY" | gpg --batch --import -
	@ secrets=$$(if [[ "$$ENV" == "dev" ]]; then echo "secrets/secrets.dev.yml"; else echo "secrets/secrets.yml"; fi);\
	echo "$$secrets" | xargs -I % sops exec-env % "sops exec-file --no-fifo secrets/payment-api-cert_default.pem 'PAYMENT_API_DEFAULT_CERT_PATH={} poetry run python src/app/main.py'"

lint:
	@ echo "Running linting..."
	@ poetry run flake518

test:
	@ echo "Running unit tests..."
	@ poetry run pytest
