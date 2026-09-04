PYTHON ?= python3
SR_EVAL_DIR ?= .cache/SR-Eval
CONTAINER ?= mrgbench_container_1
TASK ?= copyToTarget
SR_EVAL_PYTHON ?= 3.13
TOOL_BIN := $(CURDIR)/.tools/bin
UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
UV_PYTHON_INSTALL_DIR ?= $(CURDIR)/.tools/python
export PATH := $(TOOL_BIN):$(PATH)
export UV_CACHE_DIR
export UV_PYTHON_INSTALL_DIR

.PHONY: bootstrap check prepare doctor tasks export smoke-dry-run smoke smoke-all pilot-a pilot-a-all

bootstrap:
	bash scripts/bootstrap_tools.sh

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
	uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "docker==7.1.0" python scripts/pilot.py smoke-test --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --task "$(TASK)"

smoke-all:
	uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "docker==7.1.0" python scripts/pilot.py smoke-test --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --all

pilot-a:
	$(PYTHON) scripts/pilot_a.py --task "$(TASK)"

pilot-a-all:
	$(PYTHON) scripts/pilot_a.py --all
