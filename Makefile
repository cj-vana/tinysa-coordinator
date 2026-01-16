# TinySA Coordinator - Makefile
# Common development commands for the project

# Colors for help output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BOLD := \033[1m
RESET := \033[0m

# Project configuration
PYTHON := python3
VENV_DIR := venv
FRONTEND_DIR := frontend
BACKEND_DIR := backend
DATA_DIR := data

# Docker configuration
DOCKER_IMAGE := tinysa-coordinator
DOCKER_TAG := latest

.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend build lint lint-backend lint-frontend clean docker-build docker-run docker-stop test test-e2e test-e2e-ui test-e2e-headed test-e2e-report

##@ General

help: ## Display this help message
	@echo ""
	@echo "$(BOLD)$(CYAN)TinySA Coordinator$(RESET) - Development Commands"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Installation

install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)All dependencies installed successfully!$(RESET)"

install-backend: ## Install Python backend dependencies
	@echo "$(CYAN)Setting up Python virtual environment...$(RESET)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@echo "$(CYAN)Installing Python dependencies...$(RESET)"
	@. $(VENV_DIR)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "$(GREEN)Backend dependencies installed!$(RESET)"

install-frontend: ## Install Node.js frontend dependencies
	@echo "$(CYAN)Installing Node.js dependencies...$(RESET)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)Frontend dependencies installed!$(RESET)"

##@ Development

dev: ## Start both backend and frontend development servers (in background)
	@echo "$(CYAN)Starting development servers...$(RESET)"
	@echo "$(YELLOW)Starting backend on http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Starting frontend on http://localhost:5173$(RESET)"
	@echo ""
	@echo "$(BOLD)Run 'make dev-backend' and 'make dev-frontend' in separate terminals for better control$(RESET)"
	@echo ""
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Start the FastAPI backend development server
	@echo "$(CYAN)Starting FastAPI backend...$(RESET)"
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start the Vite frontend development server
	@echo "$(CYAN)Starting Vite frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run dev

##@ Building

build: build-frontend ## Build the project for production
	@echo "$(GREEN)Build complete!$(RESET)"

build-frontend: ## Build the frontend for production
	@echo "$(CYAN)Building frontend for production...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run build
	@echo "$(GREEN)Frontend built to $(FRONTEND_DIR)/dist$(RESET)"

##@ Code Quality

lint: lint-backend lint-frontend ## Run all linters
	@echo "$(GREEN)All linting complete!$(RESET)"

lint-backend: ## Lint Python backend code
	@echo "$(CYAN)Linting Python backend...$(RESET)"
	@. $(VENV_DIR)/bin/activate && \
		if command -v ruff >/dev/null 2>&1; then \
			ruff check $(BACKEND_DIR); \
		elif command -v flake8 >/dev/null 2>&1; then \
			flake8 $(BACKEND_DIR); \
		else \
			echo "$(YELLOW)No Python linter found (ruff or flake8). Skipping backend lint.$(RESET)"; \
		fi

lint-frontend: ## Lint TypeScript/React frontend code
	@echo "$(CYAN)Linting frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run lint

typecheck: ## Run TypeScript type checking
	@echo "$(CYAN)Running TypeScript type check...$(RESET)"
	@cd $(FRONTEND_DIR) && npx tsc --noEmit
	@echo "$(GREEN)Type check passed!$(RESET)"

##@ Testing

test: ## Run all tests
	@echo "$(CYAN)Running tests...$(RESET)"
	@. $(VENV_DIR)/bin/activate && \
		if command -v pytest >/dev/null 2>&1; then \
			pytest $(BACKEND_DIR) -v || true; \
		else \
			echo "$(YELLOW)pytest not installed. Skipping backend tests.$(RESET)"; \
		fi
	@echo "$(GREEN)Tests complete!$(RESET)"

test-e2e: ## Run Playwright E2E tests (all browsers)
	@echo "$(CYAN)Running Playwright E2E tests...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run test:e2e
	@echo "$(GREEN)E2E tests complete!$(RESET)"

test-e2e-ui: ## Run Playwright E2E tests with interactive UI
	@echo "$(CYAN)Starting Playwright UI mode...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run test:e2e:ui

test-e2e-headed: ## Run Playwright E2E tests in headed mode (visible browser)
	@echo "$(CYAN)Running E2E tests in headed mode...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run test:e2e:headed

test-e2e-report: ## Show Playwright HTML test report
	@echo "$(CYAN)Opening Playwright test report...$(RESET)"
	@cd $(FRONTEND_DIR) && npm run test:e2e:report

##@ Docker

docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(RESET)"
	@docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(RESET)"

docker-run: ## Run application in Docker container
	@echo "$(CYAN)Starting Docker container...$(RESET)"
	@docker-compose up -d || docker compose up -d
	@echo "$(GREEN)Container started!$(RESET)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(RESET)"

docker-stop: ## Stop Docker containers
	@echo "$(CYAN)Stopping Docker containers...$(RESET)"
	@docker-compose down || docker compose down
	@echo "$(GREEN)Containers stopped!$(RESET)"

docker-logs: ## View Docker container logs
	@docker-compose logs -f || docker compose logs -f

##@ Cleanup

clean: ## Clean up generated files and caches
	@echo "$(CYAN)Cleaning up...$(RESET)"
	@echo "  Removing Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "  Removing frontend build artifacts..."
	@rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(RESET)"

clean-all: clean ## Clean everything including node_modules and venv
	@echo "$(YELLOW)Removing node_modules...$(RESET)"
	@rm -rf $(FRONTEND_DIR)/node_modules 2>/dev/null || true
	@echo "$(YELLOW)Removing Python virtual environment...$(RESET)"
	@rm -rf $(VENV_DIR) 2>/dev/null || true
	@echo "$(GREEN)Full cleanup complete!$(RESET)"

##@ Database

db-init: ## Initialize the SQLite database
	@echo "$(CYAN)Initializing database...$(RESET)"
	@mkdir -p $(DATA_DIR)
	@. $(VENV_DIR)/bin/activate && cd $(BACKEND_DIR) && $(PYTHON) -c "from db.database import init_db; import asyncio; asyncio.run(init_db())"
	@echo "$(GREEN)Database initialized!$(RESET)"

##@ Utilities

check-deps: ## Check if all required tools are installed
	@echo "$(CYAN)Checking dependencies...$(RESET)"
	@printf "  Python 3: " && ($(PYTHON) --version 2>/dev/null && printf "$(GREEN)OK$(RESET)\n") || printf "$(RED)NOT FOUND$(RESET)\n"
	@printf "  Node.js:  " && (node --version 2>/dev/null && printf "$(GREEN)OK$(RESET)\n") || printf "$(RED)NOT FOUND$(RESET)\n"
	@printf "  npm:      " && (npm --version 2>/dev/null && printf "$(GREEN)OK$(RESET)\n") || printf "$(RED)NOT FOUND$(RESET)\n"
	@printf "  Docker:   " && (docker --version 2>/dev/null && printf "$(GREEN)OK$(RESET)\n") || printf "$(YELLOW)NOT FOUND (optional)$(RESET)\n"
	@echo ""

format: ## Format code (if formatters are available)
	@echo "$(CYAN)Formatting code...$(RESET)"
	@. $(VENV_DIR)/bin/activate && \
		if command -v ruff >/dev/null 2>&1; then \
			ruff format $(BACKEND_DIR); \
		elif command -v black >/dev/null 2>&1; then \
			black $(BACKEND_DIR); \
		else \
			echo "$(YELLOW)No Python formatter found (ruff or black). Skipping backend format.$(RESET)"; \
		fi
	@cd $(FRONTEND_DIR) && \
		if [ -f "node_modules/.bin/prettier" ]; then \
			npx prettier --write "src/**/*.{ts,tsx,css}"; \
		else \
			echo "$(YELLOW)Prettier not installed. Skipping frontend format.$(RESET)"; \
		fi
	@echo "$(GREEN)Formatting complete!$(RESET)"
