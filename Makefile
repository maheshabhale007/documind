.PHONY: dev build clean test pull-models seed logs

dev:
	docker compose up -d
	@echo "DocuMind is running:"
	@echo "  Frontend: http://localhost:8501"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

build:
	docker compose build

clean:
	docker compose down -v
	rm -rf data/

test:
	docker compose run --rm backend pytest tests/ -v

pull-models:
	docker exec documind-ollama ollama pull llama3.2:3b
	@echo "Model ready."

pull-models-large:
	docker exec documind-ollama ollama pull mistral:7b
	@echo "Mistral 7B ready."

seed:
	bash scripts/seed_demo.sh

logs:
	docker compose logs -f backend

health:
	curl -s http://localhost:8000/api/v1/health | python -m json.tool
