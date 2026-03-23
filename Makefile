
# Default values
IMAGE_NAME := ai-metrics-analyzer
TODAY := $(shell date +%Y%m%d)
WEEK_AGO := $(shell date -v -1w +%Y-%m-%d)
MONTH_AGO := $(shell date -v -1m +%Y-%m-%d)
CURRENT_MONTH := $(shell date +%Y%m)
MONTH ?= $(CURRENT_MONTH)

# Get GitHub token from gh CLI
GITHUB_ACCESS_TOKEN := $(shell gh auth token 2>/dev/null)

# Check gh CLI is authenticated
check-gh-auth:
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "ERROR: gh CLI is not installed. Install it with: brew install gh"; \
		exit 1; \
	fi
	@if [ -z "$(GITHUB_ACCESS_TOKEN)" ]; then \
		echo "ERROR: gh CLI is not authenticated. Run: gh auth login"; \
		exit 1; \
	fi
	@echo "GitHub CLI authenticated successfully"

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Fetch and analyze Copilot metrics for a specific day (default: 2 days ago)
copilot-daily: check-gh-auth build
	@echo "Fetching GitHub Copilot daily metrics..."
	@mkdir -p outputs
	docker run --rm \
		-e GH_TOKEN=$(GITHUB_ACCESS_TOKEN) \
		-v $$(pwd):/app $(IMAGE_NAME) \
		extract_copilot_acceptance_rate.py --api --report-type 1-day --output outputs/copilot_metrics_daily_$(TODAY).json

# Fetch and analyze Copilot metrics for the past 28 days
copilot-monthly: check-gh-auth build
	@echo "Fetching GitHub Copilot 28-day metrics..."
	@mkdir -p outputs
	docker run --rm \
		-e GH_TOKEN=$(GITHUB_ACCESS_TOKEN) \
		-v $$(pwd):/app $(IMAGE_NAME) \
		extract_copilot_acceptance_rate.py --api --report-type 28-day --output outputs/copilot_metrics_monthly_$(TODAY).json

cursor-weekly:
	@echo "Loading environment variables with direnv..."
	@direnv allow && eval "$$(direnv export bash)"
	@mkdir -p outputs
	@echo "Fetching Cursor metrics for the past week..."
	docker run --rm \
		-e CURSOR_API_KEY=$$CURSOR_API_KEY \
		-v $$(pwd):/app $(IMAGE_NAME) \
		extract_cursor_metrics.py --days 7 --output outputs/cursor_metrics_$(TODAY).json

cursor-monthly:
	@echo "Loading environment variables with direnv..."
	@direnv allow && eval "$$(direnv export bash)"
	@mkdir -p outputs
	@echo "Fetching Cursor metrics for the past month..."
	docker run --rm \
		-e CURSOR_API_KEY=$$CURSOR_API_KEY \
		-v $$(pwd):/app $(IMAGE_NAME) \
		extract_cursor_metrics.py --days 30 --output outputs/cursor_metrics_monthly_$(TODAY).json

# Run latest (same as copilot-monthly)
latest: copilot-monthly

# Clean Docker images
clean:
	docker rmi $(IMAGE_NAME) || true

# Show help
help:
	@echo "ITGC Monitoring Application - Makefile Commands"
	@echo ""
	@echo "Prerequisites:"
	@echo "  GitHub CLI (gh) must be installed and authenticated: gh auth login"
	@echo ""
	@echo "Available commands:"
	@echo "  make build           - Build Docker image"
	@echo "  make copilot-daily   - Fetch and analyze GitHub Copilot metrics (1-day)"
	@echo "  make copilot-monthly - Fetch and analyze GitHub Copilot metrics (28-day)"
	@echo "  make cursor-weekly   - Fetch and analyze Cursor metrics (past week)"
	@echo "  make cursor-monthly  - Fetch and analyze Cursor metrics (past month)"
	@echo "  make latest          - Same as 'make copilot-monthly'"
	@echo "  make clean           - Remove Docker image"
	@echo "  make help            - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make copilot-daily          # Fetch Copilot metrics for a specific day"
	@echo "  make copilot-monthly        # Fetch Copilot metrics for 28 days"
	@echo ""
	@echo "Output files will be saved to: ./outputs/"

# Default target
.DEFAULT_GOAL := help

.PHONY: check-gh-auth build copilot-daily copilot-monthly cursor-weekly cursor-monthly latest clean help
