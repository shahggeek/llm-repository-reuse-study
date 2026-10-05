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
git -C "${target_dir}" lfs install --local
git -C "${target_dir}" lfs pull --include="environment/java_repo/*"

java_env_dir="${target_dir}/environment/java_repo"
archive="${java_env_dir}/merged_java_env.zip"

parts=("${java_env_dir}"/split_java_env_*)
if [[ ! -e "${parts[0]}" ]]; then
  echo "No Java environment archive parts were found." >&2
  exit 2
fi

parts_size=0
for part in "${parts[@]}"; do
  if [[ "$(LC_ALL=C head -c 42 "${part}")" == "version https://git-lfs.github.com/spec/v1" ]]; then
    echo "Git LFS pointer was not materialized: ${part}" >&2
    exit 2
  fi
  part_size="$(wc -c < "${part}")"
  parts_size=$((parts_size + part_size))
done

archive_size=0
archive_rebuilt=false
if [[ -f "${archive}" ]]; then
  archive_size="$(wc -c < "${archive}")"
fi
if [[ "${archive_size}" -ne "${parts_size}" ]]; then
  cat "${parts[@]}" > "${archive}.tmp"
  mv "${archive}.tmp" "${archive}"
  archive_rebuilt=true
fi

extract_dir="${java_env_dir}/extracted"
mkdir -p "${extract_dir}"
if [[ "${archive_rebuilt}" == true ]] || ! find "${extract_dir}" -type f -name '*.tar' -print -quit | grep -q .; then
  unzip -o "${archive}" -d "${extract_dir}"
fi

echo "SR-Eval prepared at ${target_dir}"
echo "Pinned commit: $(git -C "${target_dir}" rev-parse HEAD)"
echo "Docker image archives:"
find "${extract_dir}" -type f -name '*.tar' -print
