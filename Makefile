PYTHON ?= python3
SR_EVAL_DIR ?= .cache/SR-Eval

.PHONY: check evidence-check reconstruct-prompts summarize-pilot-a summarize-reuse-pilot-a summarize-pilot-b summarize-reuse-pilot-b summarize-pilot-c

check:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/pilot.py validate-manifest
	$(PYTHON) scripts/pilot_b.py
	$(PYTHON) scripts/pilot_c.py

evidence-check: check
	$(PYTHON) scripts/build_submission_artifact.py --verify-inputs

reconstruct-prompts:
	$(PYTHON) scripts/reconstruct_prompts.py --sr-eval "$(SR_EVAL_DIR)" --output reconstructed-prompts

summarize-pilot-a:
	$(PYTHON) scripts/summarize_pilot_a.py

summarize-reuse-pilot-a:
	$(PYTHON) scripts/summarize_reuse_full_review.py

summarize-pilot-b:
	$(PYTHON) scripts/summarize_pilot_b.py

summarize-reuse-pilot-b:
	$(PYTHON) scripts/finalize_pilot_b_reuse.py

summarize-pilot-c:
	$(PYTHON) scripts/summarize_pilot_c.py
