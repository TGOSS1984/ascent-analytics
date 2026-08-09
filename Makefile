# Unix-style equivalent of `python run_pipeline.py` — same 8 steps, same
# order. Windows users should use run_pipeline.py directly instead, since
# `make` isn't available on Windows without extra tooling (WSL, Git Bash
# with make installed, or Chocolatey) — this file exists for Unix/macOS
# convenience and because GitHub Actions' ubuntu-latest runner has `make`
# built in, not because it's the primary way to run this project.

.PHONY: all generate clean-pipeline warehouse export test pipeline

all: pipeline test

pipeline:
	python -m src.generation.generate_reference_data
	python -m src.generation.generate_transactions
	python -m src.generation.generate_extensions
	python -m src.cleaning.run_pipeline
	python -m src.cleaning.run_pipeline_extensions
	python -m src.warehouse.build_warehouse
	python -m src.warehouse.apply_views
	python -m src.warehouse.export_for_powerbi

generate:
	python -m src.generation.generate_reference_data
	python -m src.generation.generate_transactions
	python -m src.generation.generate_extensions

warehouse:
	python -m src.warehouse.build_warehouse
	python -m src.warehouse.apply_views
	python -m src.warehouse.export_for_powerbi

test:
	pytest tests/ -v

clean-pipeline:
	rm -f data/raw/*.csv data/cleaned/*.csv data/warehouse/*.db powerbi/data_export/*.csv