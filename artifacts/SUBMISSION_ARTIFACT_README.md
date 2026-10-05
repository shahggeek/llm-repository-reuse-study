# SANER 2027 reproducibility artifact

This package preserves the public evidence for the repository-reuse pilot study. It
covers Pilot A, the isolated Pilot A amendment, the Pilot B mechanism probe,
the Pilot C boundary check, independent reuse review, and anonymous
practitioner validation.

It is deliberately separate from the private working repository. Manuscript
sources, author metadata, private correspondence, raw returned workbooks, and
internal submission notes are not part of the public package.

## Start here

1. Read `docs/methodology.md` and `docs/pilot-protocol.md` for the study design.
2. Read `analysis/rq2/reuse-rubric.md` for the R0--R3 reuse and C0--C3 context
   scales.
3. Inspect `experiment/config/` and `experiment/prompts/` for the frozen task,
   model, and prompt configuration.
4. Inspect `data/generated-trajectories/` for prompt omission records, first
   responses, event streams, stderr, and privacy-filtered run records.
5. Inspect `results/pilot/` for frozen functional, reuse, agreement,
   replication, and practitioner summaries.
6. Read `EVIDENCE_PACKAGE_README.md` and `MANIFEST.json` for the exact public
   inventory, transformations, exclusions, and file hashes.

## Verify the package

From the extracted package root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/pilot.py validate-manifest
python3 scripts/pilot_b.py
python3 scripts/pilot_c.py
```

The archive's external `.sha256` file verifies the compressed package. The
embedded `MANIFEST.json` records the size and SHA-256 digest of every packaged
file. Tests that require the separately obtained SR-Eval checkout are reported
as skipped in the self-contained package; after placing the pinned checkout at
`.cache/SR-Eval`, those tests run normally.

Run `make evidence-check` to require the complete packaged trajectory and
functional-report inventory in addition to the core tests.

## Reconstruct omitted prompts

SR-Eval and MRG-Bench do not state a redistribution license. Their authored
task instructions and rendered prompt text are omitted from this artifact.
Each omitted instruction and prompt is bound by its original SHA-256 digest.
After separately obtaining SR-Eval at the pinned commit, reconstruct and verify
all 147 prompts locally:

```bash
python3 scripts/reconstruct_prompts.py \
  --sr-eval .cache/SR-Eval \
  --output reconstructed-prompts
```

The reconstructed files are local working material and must not be committed
to the public repository.

## Reproduce derived summaries

The committed JSON and CSV files are the frozen paper-facing results. The main
summary commands below regenerate those files byte-for-byte from the packaged
evidence:

```bash
python3 scripts/summarize_pilot_a.py
python3 scripts/summarize_reuse_full_review.py
python3 scripts/summarize_pilot_b.py
python3 scripts/finalize_pilot_b_reuse.py
python3 scripts/summarize_pilot_c.py
```

Structural metrics use Tree-sitter Java and Lizard. Spreadsheet extraction uses
the documented workbook tooling. Functional retesting requires Docker, the study's
pinned Java environment, and a separate checkout of SR-Eval at commit
`6cf948d69427687bf61042640223d5b318f7bc4c`.

## Privacy and exclusions

The public practitioner response table retains only anonymous reviewer codes,
broad experience categories, judgments, and rationales covered by consent. It
removes paths and hashes for privately returned workbooks. The raw returned
workbooks, identity/contact mappings, correspondence, and compensation records
are not included.

Reviewer-facing and completed spreadsheet workbooks are excluded. Their
deidentified extracted rows, agreement summaries, adjudications, and frozen
source hashes provide the public evidence. Provider session identifiers are
replaced by stable public pseudonyms. For every transformed file,
`MANIFEST.json` records both the public hash and the original private-source
hash.

The package also excludes local model-session directories, tool installations,
caches, containers, and pre-contact failure logs that contain machine-specific
paths. The model provider did not expose an immutable model snapshot identifier;
the recorded model name, settings, CLI version, prompt hashes, reconstructable
prompt sources, first outputs, and event streams are the available provenance.

## Third-party material and release status

The archive does not redistribute SR-Eval/MRG-Bench-authored task instructions
or rendered prompts. Upstream Apache-2.0 excerpts retained elsewhere remain
subject to their original licenses. The SR-Eval clone itself is not
redistributed.

The Apache-2.0 license applies only to study-authored material as defined in
`LICENSE_SCOPE.md`; see `THIRD_PARTY_LICENSES.md` for all exclusions and
attribution. This remains a submission candidate until it is deposited at a
stable public location. After deposit, add the permanent DOI to the
manuscript's Data Availability section.
