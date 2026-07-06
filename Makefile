    .PHONY: help init tests

POETRY ?= poetry

## Show help for all commands
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Create a local virtualenv and install dependencies
	$(POETRY) install

tests: ## Run tests
	$(POETRY) run pytest
