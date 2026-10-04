# Generated trajectories

Raw model responses and extracted methods are written here by the generation
stage. They are ignored by Git in the private working repository and copied,
after privacy filtering, into the public evidence package.

Each run directory is named by pilot batch, condition, task, and repetition.
It contains:

- `record.json`: run identity, model and protocol provenance, turn records,
  extracted code, test outcomes, usage, and cumulative-correctness status;
- `turn-N.prompt.txt`: the exact rendered prompt retained privately and the
  email-redacted prompt copy released publicly;
- `turn-N.raw.md`: the unmodified first model response;
- `turn-N.events.jsonl`: the CLI event stream; public copies replace provider
  thread identifiers with stable pseudonyms; and
- `turn-N.stderr.txt`: captured CLI diagnostics.

Run records use the schemas in `experiment/schemas/`. Pilot A uses the original
schema, Pilot B uses schema version 2 for retrieval provenance, and Pilot C uses
schema version 3 for explicit repetition numbers. The public manifest records a
SHA-256 digest for every released file and records the original private-source
digest whenever content was transformed for privacy.

Functional reports under `results/pilot/generated-tests/` are separate from
generation. Test results were not returned to the model. Use `make
evidence-check` to require the complete frozen trajectory and report inventory.
