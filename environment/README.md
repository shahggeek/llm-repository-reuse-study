# SR-Eval Java Environment

The study does not vendor SR-Eval or its large Java Docker image. The setup
script creates an ignored checkout at the exact revision recorded in
`experiment/config/protocol.json`.

## Prepare the benchmark

Install Docker Desktop, then install the remaining tools locally and prepare the
benchmark:

```bash
make bootstrap
make prepare
```

The script:

1. clones or verifies `.cache/SR-Eval`;
2. checks out commit `6cf948d69427687bf61042640223d5b318f7bc4c`;
3. fetches only the Java environment's Git LFS objects;
4. concatenates `split_java_env_*` into `merged_java_env.zip`;
5. extracts the archive without loading or starting containers.

Inspect the extracted files, then load the `.tar` image shown by the script:

```bash
docker load --input PATH_TO_IMAGE_TAR
docker image ls
```

Start the loaded image in a disposable, long-running container. Replace
`IMAGE:TAG` with the tag reported by `docker load`:

```bash
docker run --name mrgbench_container_1 --detach --tty IMAGE:TAG bash
```

Do not run multiple tasks concurrently in one container. SR-Eval replaces code
and test ranges temporarily; concurrent replacements can interfere.

## Verify

```bash
make doctor
make tasks
make smoke-dry-run TASK=copyToTarget
make smoke TASK=copyToTarget
```

The harness imports the pinned SR-Eval `JavaRepoClient` directly and uses a
minimal Python 3.13 environment with the same Docker SDK version locked by
SR-Eval. This avoids unrelated model-serving dependencies that do not build on
macOS. It restores the source and test files after each test. Use disposable
containers regardless, because Spring AI formatting may touch additional files
inside the container.

## Known upstream limitations

- The Java image is distributed as split Git LFS objects and is large.
- The published Java image targets `linux/amd64`; Docker Desktop emulates it on
  Apple Silicon, so Maven checks run more slowly.
- The upstream Java setup document does not publish a stable image tag; use the
  tag reported by `docker load`.
- The benchmark's default evaluator checks each checkpoint only against that
  turn's test. This study's wrapper checks all tests through the current turn.
- A later reference solution can conflict with an earlier generated test; the
  smoke test is designed to reveal that before model calls.
