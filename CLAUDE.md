# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Code Editor metrics analysis tool that includes:
1. **GitHub Copilot metrics analysis** - Processes JSON data from GitHub Copilot usage to calculate acceptance rates and generate detailed statistics
2. **Cursor Admin API metrics collection** - Retrieves team usage metrics, spending data, and member information from Cursor Admin API

Both tools are designed to run locally and in Docker containers.

## Key Architecture

- **GitHub Copilot script**: `extract_copilot_acceptance_rate.py` - Python script that parses GitHub Copilot metrics JSON data and calculates acceptance rates with breakdowns by language and editor
- **Cursor Admin API script**: `extract_cursor_metrics.py` - Python script that retrieves team usage metrics from Cursor Admin API
- **Configuration management**: `config.py` - Manages API keys and tool settings
- **Data format**: Expects JSON files containing Copilot usage metrics with nested structure for editors, models, and languages
- **Output**: Japanese-language formatted reports showing overall acceptance rates, language-specific stats, and editor-specific stats

## Commands

### Running the tools locally

#### GitHub Copilot Analysis
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default file location (~/Downloads/copilot_metrics.json)
python extract_copilot_acceptance_rate.py

# Run with specific file
python extract_copilot_acceptance_rate.py path/to/copilot_metrics.json

# Show help
python extract_copilot_acceptance_rate.py --help
```

#### Cursor Admin API Metrics
```bash
# Set up API key
export CURSOR_API_KEY=your-api-key-here

# Get metrics for past 7 days
python extract_cursor_metrics.py

# Get metrics for specific period
python extract_cursor_metrics.py --start-date 2024-01-01 --end-date 2024-01-31

# Save to JSON file
python extract_cursor_metrics.py --output cursor_metrics_$(date +%Y%m%d).json

# Get metrics for 30 days with spending data
python extract_cursor_metrics.py --days 30 --include-spending
```

### Docker usage
```bash
# Build Docker image
docker build -t ai-metrics-analyzer .

# GitHub Copilot analysis
docker run -v /path/to/data:/app ai-metrics-analyzer extract_copilot_acceptance_rate.py copilot_metrics.json

# Cursor Admin API metrics (with environment variable)
source .envrc && docker run -e CURSOR_API_KEY=$CURSOR_API_KEY -v $(pwd):/app ai-metrics-analyzer extract_cursor_metrics.py --days 30 --output outputs/cursor_metrics_$(date +%Y%m%d).json
```

## Data Structure

The tool expects JSON data with this structure:
- Root array of daily metrics objects
- Each day contains `copilot_ide_code_completions` with nested editors/models/languages
- Key metrics: `total_code_suggestions` and `total_code_acceptances` per language

## Important Notes

- All user-facing output is in Japanese
- The tool handles both single objects and arrays in JSON input
- Supports multiple editors (VS Code, etc.) and programming languages
- Default file path is `~/Downloads/copilot_metrics.json` when no argument provided
- Docker container expects files to be mounted at `/app` volume

## References

- **Cursor Admin API specification**: https://docs.cursor.com/en/account/teams/admin-api