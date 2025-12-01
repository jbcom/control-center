help: ## Display this help screen
	@echo "Makefile for managing this project"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@for file in $(MAKEFILE_LIST); do \
	    grep -E '^[a-zA-Z_-]+:.*?## .*$$' $$file; \
	done | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'