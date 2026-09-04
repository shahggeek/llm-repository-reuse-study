PYTHON ?= python3
SR_EVAL_DIR ?= .cache/SR-Eval
CONTAINER ?= mrgbench_container_1
TASK ?= between

.PHONY: check prepare doctor tasks export smoke-dry-run smoke smoke-all

check:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/pilot.py validate-manifest

prepare:
	bash scripts/prepare_sr_eval.sh "$(SR_EVAL_DIR)"

doctor:
	$(PYTHON) scripts/pilot.py doctor --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)"

tasks:
	$(PYTHON) scripts/pilot.py validate --sr-eval "$(SR_EVAL_DIR)"

export:
	$(PYTHON) scripts/pilot.py export --sr-eval "$(SR_EVAL_DIR)"

smoke-dry-run:
	$(PYTHON) scripts/pilot.py smoke-test --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --task "$(TASK)" --dry-run

smoke:
	uv run --project "$(SR_EVAL_DIR)" python scripts/pilot.py smoke-test --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --task "$(TASK)"

smoke-all:
	uv run --project "$(SR_EVAL_DIR)" python scripts/pilot.py smoke-test --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --all
