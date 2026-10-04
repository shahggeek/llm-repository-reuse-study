PYTHON ?= python3
SR_EVAL_DIR ?= .cache/SR-Eval
CONTAINER ?= mrgbench_container_1
TASK ?= copyToTarget
SR_EVAL_PYTHON ?= 3.13
AMENDMENT_CODEX ?= $(CURDIR)/.tools/codex-cli-0.153.0/node_modules/.bin/codex
PILOT_B_CODEX ?= $(AMENDMENT_CODEX)
PILOT_B_CONDITION ?= engineering-guardrails
PILOT_C_CODEX ?= $(AMENDMENT_CODEX)
PILOT_C_CONDITION ?= engineering-guardrails
PILOT_C_REPETITION ?=
TECTONIC ?= /opt/homebrew/opt/tectonic/bin/tectonic
TECTONIC_CACHE_DIR ?= /private/tmp/tectonic-cache
STRUCTURAL_RUN = uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "tree-sitter==0.25.2" --with "tree-sitter-java==0.23.5" --with "lizard==1.17.31"
INDUSTRY_REVIEW_RUN = uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "numbers-parser==4.19.0"
TOOL_BIN := $(CURDIR)/.tools/bin
UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
UV_PYTHON_INSTALL_DIR ?= $(CURDIR)/.tools/python
export PATH := $(TOOL_BIN):$(PATH)
export UV_CACHE_DIR
export UV_PYTHON_INSTALL_DIR

.PHONY: bootstrap check paper-check paper-pdf industry-review submission-artifact prepare doctor tasks export smoke-dry-run smoke smoke-all pilot-a pilot-a-all test-pilot-a amendment-cli amendment-validate amendment-export amendment-preflight amendment-smoke-dry-run pilot-a-amendment pilot-a-amendment-all test-pilot-a-amendment audit-prompt-context summarize-pilot-a-adjusted structural-check structural-pilot reuse-screen reuse-agreement reuse-full-review pilot-b-check pilot-b-preflight pilot-b pilot-b-all test-pilot-b summarize-pilot-b reuse-pilot-b reuse-pilot-b-final pilot-c-check pilot-c-preflight pilot-c pilot-c-all test-pilot-c summarize-pilot-c

bootstrap:
	bash scripts/bootstrap_tools.sh

check:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/pilot.py validate-manifest
	$(PYTHON) scripts/pilot_b.py
	$(PYTHON) scripts/pilot_c.py

paper-check:
	$(PYTHON) -m unittest discover -s tests -p "test_paper_claims.py" -v

paper-pdf: paper-check
	mkdir -p "$(TECTONIC_CACHE_DIR)"
	cd paper && TECTONIC_CACHE_DIR="$(TECTONIC_CACHE_DIR)" "$(TECTONIC)" --keep-logs --keep-intermediates main.tex

industry-review:
	$(INDUSTRY_REVIEW_RUN) python scripts/analyze_industry_expert_reviews.py

submission-artifact:
	$(PYTHON) scripts/build_submission_artifact.py

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

test-pilot-a:
	uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "docker==7.1.0" python scripts/evaluate_pilot_a.py --container "$(CONTAINER)" --all

amendment-cli:
	npm_config_cache=.cache/npm npm install --prefix .tools/codex-cli-0.153.0 --no-save --no-package-lock @openai/codex@0.153.0
	$(AMENDMENT_CODEX) --version

amendment-validate:
	$(PYTHON) scripts/pilot.py validate-manifest --manifest experiment/config/pilot-a-amendment.json
	$(PYTHON) scripts/pilot.py validate --manifest experiment/config/pilot-a-amendment.json --sr-eval "$(SR_EVAL_DIR)"

amendment-export:
	$(PYTHON) scripts/pilot.py export --manifest experiment/config/pilot-a-amendment.json --sr-eval "$(SR_EVAL_DIR)" --output work/amendment-task-packets

amendment-preflight:
	$(PYTHON) scripts/pilot_a.py --amendment --codex "$(AMENDMENT_CODEX)" --preflight

amendment-smoke-dry-run:
	$(PYTHON) scripts/pilot.py smoke-test --manifest experiment/config/pilot-a-amendment.json --sr-eval "$(SR_EVAL_DIR)" --task "$(TASK)" --dry-run

pilot-a-amendment:
	$(PYTHON) scripts/pilot_a.py --amendment --codex "$(AMENDMENT_CODEX)" --task "$(TASK)"

pilot-a-amendment-all:
	$(PYTHON) scripts/pilot_a.py --amendment --codex "$(AMENDMENT_CODEX)" --all

test-pilot-a-amendment:
	uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "docker==7.1.0" python scripts/evaluate_pilot_a.py --amendment --container "$(CONTAINER)" --all

audit-prompt-context:
	$(PYTHON) scripts/audit_prompt_context.py

summarize-pilot-a-adjusted:
	$(PYTHON) scripts/summarize_pilot_a.py

structural-check:
	$(STRUCTURAL_RUN) python -m unittest discover -s tests -p "test_structural_metrics.py" -v

structural-pilot: structural-check
	$(STRUCTURAL_RUN) python scripts/structural_metrics.py

reuse-screen:
	$(PYTHON) scripts/screen_reuse_candidates.py

reuse-agreement:
	@test -n "$(RESPONSES)" || (echo "Set RESPONSES to the completed Review-sheet CSV" && exit 2)
	$(PYTHON) scripts/calculate_reuse_agreement.py "$(RESPONSES)" --output results/pilot/pilot-a-reuse-review-agreement.json

reuse-full-review:
	$(PYTHON) scripts/summarize_reuse_full_review.py

pilot-b-check:
	$(PYTHON) scripts/pilot_b.py --check-dataset --sr-eval "$(SR_EVAL_DIR)"

pilot-b-preflight:
	$(PYTHON) scripts/run_pilot_b.py --codex "$(PILOT_B_CODEX)" --preflight

pilot-b:
	$(PYTHON) scripts/run_pilot_b.py --codex "$(PILOT_B_CODEX)" --condition "$(PILOT_B_CONDITION)" --task "$(TASK)"

pilot-b-all:
	$(PYTHON) scripts/run_pilot_b.py --codex "$(PILOT_B_CODEX)" --condition "$(PILOT_B_CONDITION)" --all

test-pilot-b:
	uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "docker==7.1.0" python scripts/evaluate_pilot_b.py --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --condition "$(PILOT_B_CONDITION)" --all

summarize-pilot-b:
	$(PYTHON) scripts/summarize_pilot_b.py

reuse-pilot-b:
	$(PYTHON) scripts/summarize_pilot_b_reuse.py

reuse-pilot-b-final:
	node scripts/extract_pilot_b_reuse_review.mjs
	$(PYTHON) scripts/calculate_pilot_b_reuse_agreement.py
	$(PYTHON) scripts/finalize_pilot_b_reuse.py

pilot-c-check:
	$(PYTHON) scripts/pilot_c.py --check-dataset --sr-eval "$(SR_EVAL_DIR)"

pilot-c-preflight:
	$(PYTHON) scripts/run_pilot_c.py --codex "$(PILOT_C_CODEX)" --preflight

pilot-c:
	$(PYTHON) scripts/run_pilot_c.py --codex "$(PILOT_C_CODEX)" --condition "$(PILOT_C_CONDITION)" --task "$(TASK)" $(if $(PILOT_C_REPETITION),--repetition "$(PILOT_C_REPETITION)")

pilot-c-all:
	$(PYTHON) scripts/run_pilot_c.py --codex "$(PILOT_C_CODEX)" --condition "$(PILOT_C_CONDITION)" --all $(if $(PILOT_C_REPETITION),--repetition "$(PILOT_C_REPETITION)")

test-pilot-c:
	uv run --python "$(SR_EVAL_PYTHON)" --no-project --with "docker==7.1.0" python scripts/evaluate_pilot_c.py --sr-eval "$(SR_EVAL_DIR)" --container "$(CONTAINER)" --condition "$(PILOT_C_CONDITION)" --all $(if $(PILOT_C_REPETITION),--repetition "$(PILOT_C_REPETITION)")

summarize-pilot-c:
	$(PYTHON) scripts/summarize_pilot_c.py
