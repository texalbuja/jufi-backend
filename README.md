# JF Portal Backend

A Flask REST API for the JF Portal.

## Setup

1. Install uv if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run the application:
   ```bash
   uv run python main.py
   ```

The API will be available at http://localhost:8080

## API Endpoints

- GET /api/hello: Returns a hello message in JSON format.