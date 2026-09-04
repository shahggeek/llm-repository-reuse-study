#!/usr/bin/env bash
set -euo pipefail

target_dir="${1:-.cache/SR-Eval}"
benchmark_url="https://github.com/AjaxZhan/SR-Eval.git"
benchmark_commit="6cf948d69427687bf61042640223d5b318f7bc4c"

command -v git >/dev/null || { echo "git is required" >&2; exit 2; }
command -v unzip >/dev/null || { echo "unzip is required" >&2; exit 2; }
git lfs version >/dev/null 2>&1 || { echo "Git LFS is required. Install it, then run 'git lfs install'." >&2; exit 2; }

if [[ ! -d "${target_dir}/.git" ]]; then
  mkdir -p "$(dirname "${target_dir}")"
  GIT_LFS_SKIP_SMUDGE=1 git clone "${benchmark_url}" "${target_dir}"
fi

actual_url="$(git -C "${target_dir}" remote get-url origin)"
if [[ "${actual_url}" != "${benchmark_url}" && "${actual_url}" != "https://github.com/AjaxZhan/SR-Eval" ]]; then
  echo "Unexpected SR-Eval origin: ${actual_url}" >&2
  exit 2
fi

git -C "${target_dir}" fetch origin "${benchmark_commit}"
git -C "${target_dir}" checkout --detach "${benchmark_commit}"
git -C "${target_dir}" lfs pull --include="environment/java_repo/*"

java_env_dir="${target_dir}/environment/java_repo"
archive="${java_env_dir}/merged_java_env.zip"

if [[ ! -f "${archive}" ]]; then
  parts=("${java_env_dir}"/split_java_env_*)
  if [[ ! -e "${parts[0]}" ]]; then
    echo "No Java environment archive parts were found." >&2
    exit 2
  fi
  cat "${parts[@]}" > "${archive}"
fi

extract_dir="${java_env_dir}/extracted"
mkdir -p "${extract_dir}"
unzip -o "${archive}" -d "${extract_dir}"

echo "SR-Eval prepared at ${target_dir}"
echo "Pinned commit: $(git -C "${target_dir}" rev-parse HEAD)"
echo "Docker image archives:"
find "${extract_dir}" -type f -name '*.tar' -print
