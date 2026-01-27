.PHONY: setup install dev run backend frontend build clean test lint format

# Setup the project
setup:
	./scripts/setup.sh

# Install dependencies
install:
	poetry install
	cd frontend && npm install

# Run both backend and frontend (development mode)
dev:
	./scripts/run_demo.sh

# Run only the backend
backend:
	poetry run python -m backend.main

# Run only the frontend
frontend:
	cd frontend && npm run dev

# Build the frontend for production
build:
	cd frontend && npm run build

# Clean build artifacts
clean:
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# Run tests
test:
	poetry run pytest

# Lint code
lint:
	poetry run ruff check backend/
	cd frontend && npm run lint

# Format code
format:
	poetry run ruff format backend/
	cd frontend && npm run format 2>/dev/null || true

# Show help
help:
	@echo "UCP Demo - Available commands:"
	@echo ""
	@echo "  make setup     - Initial project setup"
	@echo "  make install   - Install all dependencies"
	@echo "  make dev       - Start development servers (backend + frontend)"
	@echo "  make backend   - Start only the backend server"
	@echo "  make frontend  - Start only the frontend dev server"
	@echo "  make build     - Build frontend for production"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linters"
	@echo "  make format    - Format code"
	@echo "  make clean     - Remove build artifacts"
	@echo ""
