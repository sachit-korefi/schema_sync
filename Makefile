# Run the application
run:
	@echo "Starting the application..."
	clear
	python -m uvicorn main:app --reload --host 0.0.0.0 --port 8005

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt


# Lint the code
lint:
	@echo "Linting the code..."
	flake8 .  --ignore=E203,W503,E501,W291 \
	--extend-exclude=venv,.venv,prototype_test,alembic/

migrations:
	@echo "Auto Generating Migrations for SCHEMA_SYNC Schema"
	alembic revision --autogenerate -m "initial tables" 

migrate:
	@echo "Migrating changes to SCHEMA_SYNC Schema"
	alembic upgrade head

run-tests:
	clear
	@echo "Running testcases"
	pytest tests/