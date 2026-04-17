# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency file and install
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code
COPY . .

# Expose port
EXPOSE 8080

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "module_name:app_name"]