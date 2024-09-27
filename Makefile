
.PHONY: env
env: env/bin/activate
env/bin/activate:
	python3 -m venv env

.PHONY: install
install: env
	pip install -e .

.PHONY: build
build:
	python3 -m build

.PHONY: clean
clean:
	rm -rf src/*.egg-info dist
	find src tests -name __pycache__ -type d -exec rm -rf '{}' \;

.PHONY: distclean
distclean: clean
	rm -rf env

.PHONY: test-upload
test-upload:
	python3 -m twine upload --repository testpypi dist/*

.PHONY: upload
upload:
	python3 -m twine upload dist/*

.PHONY: secret
secret:
	@openssl rand -base64 48
