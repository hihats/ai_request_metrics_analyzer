
# Default values
IMAGE_NAME := ai-metrics-analyzer
TODAY := $(shell date +%Y%m%d)
WEEK_AGO := $(shell date -v -1w +%Y-%m-%d)
MONTH_AGO := $(shell date -v -1m +%Y-%m-%d)
CURRENT_MONTH := $(shell date +%Y%m)
MONTH ?= $(CURRENT_MONTH)

# Required environment variables check
check-env:
	@if [ -z "$$GITHUB_ACCESS_TOKEN" ]; then \
		echo "ERROR: GITHUB_ACCESS_TOKEN environment variable is required"; \
		exit 1; \
	fi

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Command to fetch and analyze Copilot metrics for the past week
copilot-weekly: check-env build
	@echo "Opening Personal Access Tokens page for token regeneration..."
	@open "https://github.com/settings/personal-access-tokens"
	@echo "Please regenerate your token and press Enter to continue..."
	@read dummy
	@echo "Loading environment variables with direnv..."
	@direnv allow && eval "$$(direnv export bash)"
	@echo "Fetching GitHub Copilot metrics from $(WEEK_AGO) to $(TODAY)..."
	@mkdir -p outputs
	curl -L \
		-H "Accept: application/vnd.github+json" \
		-H "Authorization: Bearer $$GITHUB_ACCESS_TOKEN" \
		-H "X-GitHub-Api-Version: 2022-11-28" \
		https://api.github.com/orgs/crowdworksjp/copilot/metrics?since=$(WEEK_AGO) > ./outputs/copilot_metrics_weekly_$$(date +%Y%m%d).json
	@echo "Analyzing GitHub Copilot metrics from $(WEEK_AGO) to $(TODAY)..."
	docker run --rm \
		-e GITHUB_ACCESS_TOKEN=$$GITHUB_ACCESS_TOKEN \
		-e DATA_DIR=outputs \
		-v $$(pwd):/app $(IMAGE_NAME) \
		extract_copilot_acceptance_rate.py outputs/copilot_metrics_weekly_$(TODAY).json

# Run with current month data
copilot-monthly: check-env build
	@echo "Opening Personal Access Tokens page for token regeneration..."
	@open "https://github.com/settings/personal-access-tokens"
	@echo "Please regenerate your token and press Enter to continue..."
	@read dummy
	@echo "Loading environment variables with direnv..."
	@direnv allow && eval "$$(direnv export bash)"
	@echo "Fetching GitHub Copilot metrics from $(MONTH_AGO) to $(TODAY)..."
	@mkdir -p outputs
	curl -L \
		-H "Accept: application/vnd.github+json" \
		-H "Authorization: Bearer $$GITHUB_ACCESS_TOKEN" \
		-H "X-GitHub-Api-Version: 2022-11-28" \
		https://api.github.com/orgs/crowdworksjp/copilot/metrics?since=$(MONTH_AGO) > ./outputs/copilot_metrics_monthly_$$(date +%Y%m%d).json
	@echo "Analyzing GitHub Copilot metrics from $(MONTH_AGO) to $(TODAY)..."
	docker run --rm \
		-e GITHUB_ACCESS_TOKEN=$$GITHUB_ACCESS_TOKEN \
		-e DATA_DIR=outputs \
		-v $$(pwd):/app $(IMAGE_NAME) \
		extract_copilot_acceptance_rate.py outputs/copilot_metrics_monthly_$(TODAY).json

# Run latest month interactively (same as copilot-weekly)
latest: copilot-weekly

# Clean Docker images
clean:
	docker rmi $(IMAGE_NAME) || true

# Show help
help:
	@echo "ITGC Monitoring Application - Makefile Commands"
	@echo ""
	@echo "Prerequisites:"
	@echo "  Set environment variables: GITHUB_ACCESS_TOKEN, REPO_NAME"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build Docker image"
	@echo "  make copilot-weekly - Fetch and analyze GitHub Copilot metrics (past week)"
	@echo "  make copilot-monthly - Fetch and analyze GitHub Copilot metrics (past month)"
	@echo "  make latest         - Same as 'make copilot-weekly'"
	@echo "  make clean          - Remove Docker image"
	@echo "  make help           - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make copilot-weekly         # Fetch Copilot metrics for the past week"
	@echo "  make copilot-monthly        # Fetch Copilot metrics for the past month"
	@echo ""
	@echo "Output files will be saved to: ./outputs/"

# Default target
.DEFAULT_GOAL := help

.PHONY: check-env build copilot-weekly copilot-monthly latest clean help
