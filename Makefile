.PHONY: test example install ensure-uv

test:
	PYTHONPATH=$$PYTHONPATH:. uv run pytest -s -vv $(filter-out $@,$(MAKECMDGOALS))

example:
	@args="$(filter-out $@,$(MAKECMDGOALS))"; \
	PYTHONPATH=$$PYTHONPATH:. uv run pytest -s -vv $$args

install: ensure-uv
	uv sync --all-extras

ensure-uv:
	@if ! command -v uv &> /dev/null; then \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

%:
	@: