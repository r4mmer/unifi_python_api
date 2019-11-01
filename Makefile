
.PHONY: env
env: env/bin/activate
env/bin/activate:
	python3 -m venv env

.PHONY: full
full: develop config trans
	@echo
	@echo All Good!!

.PHONY: develop
develop: setup.py
	pip install -e .[dev]

.PHONY: setup
install: env setup.py
	pip install -e .

.PHONY: clean
clean:
	rm -rf *.egg-info build dist
	find unifi_api tests -name __pycache__ -type d -exec rm -rf '{}' \;

.PHONY: distclean
distclean: clean
	rm -rf env

.PHONY: secret
secret:
	@openssl rand -base64 48
