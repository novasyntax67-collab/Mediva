.PHONY: setup dev docker-up docker-down lint format clean

setup:
	cp .env.example .env
	pnpm install
	python -m venv .venv
	@echo "Setup complete. Activate your virtual environment and run 'make dev'."

dev:
	pnpm dev:web & pnpm dev:api

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

lint:
	pnpm lint
	ruff check .

format:
	pnpm format
	ruff format .

clean:
	rm -rf node_modules
	rm -rf .next
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".venv" -exec rm -r {} +
