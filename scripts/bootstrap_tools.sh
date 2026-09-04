#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tool_bin="${repo_root}/.tools/bin"
download_dir="${repo_root}/.tools/downloads"

git_lfs_version="3.8.0"
git_lfs_sha256="caff76a7d070d8160c89bc39b6e85d98f24135b6fed038a3b4de2590d25102d8"
uv_version="0.12.9"
uv_sha256="301f72afaf54060f92da7016cb0115bd077f43a9c8e39c1d8170a0bac80fd398"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This bootstrap currently supports Apple Silicon macOS only." >&2
  exit 2
fi

for command_name in curl shasum tar unzip; do
  command -v "${command_name}" >/dev/null || {
    echo "${command_name} is required" >&2
    exit 2
  }
done

mkdir -p "${tool_bin}" "${download_dir}"

git_lfs_archive="${download_dir}/git-lfs-darwin-arm64-v${git_lfs_version}.zip"
if [[ ! -f "${git_lfs_archive}" ]]; then
  curl -fsSL \
    -o "${git_lfs_archive}" \
    "https://github.com/git-lfs/git-lfs/releases/download/v${git_lfs_version}/git-lfs-darwin-arm64-v${git_lfs_version}.zip"
fi

actual_git_lfs_sha256="$(shasum -a 256 "${git_lfs_archive}" | awk '{print $1}')"
if [[ "${actual_git_lfs_sha256}" != "${git_lfs_sha256}" ]]; then
  echo "Git LFS checksum mismatch" >&2
  exit 2
fi

unzip -jo \
  "${git_lfs_archive}" \
  "git-lfs-${git_lfs_version}/git-lfs" \
  -d "${tool_bin}" >/dev/null
chmod +x "${tool_bin}/git-lfs"

uv_archive="${download_dir}/uv-aarch64-apple-darwin-${uv_version}.tar.gz"
if [[ ! -f "${uv_archive}" ]]; then
  curl -fsSL \
    -o "${uv_archive}" \
    "https://github.com/astral-sh/uv/releases/download/${uv_version}/uv-aarch64-apple-darwin.tar.gz"
fi

actual_uv_sha256="$(shasum -a 256 "${uv_archive}" | awk '{print $1}')"
if [[ "${actual_uv_sha256}" != "${uv_sha256}" ]]; then
  echo "uv checksum mismatch" >&2
  exit 2
fi

uv_extract_dir="${download_dir}/uv-${uv_version}"
mkdir -p "${uv_extract_dir}"
tar -xzf "${uv_archive}" -C "${uv_extract_dir}"
install -m 0755 "${uv_extract_dir}/uv-aarch64-apple-darwin/uv" "${tool_bin}/uv"
install -m 0755 "${uv_extract_dir}/uv-aarch64-apple-darwin/uvx" "${tool_bin}/uvx"

PATH="${tool_bin}:${PATH}" git lfs install --local

echo "Installed project-local tools:"
"${tool_bin}/git-lfs" version
"${tool_bin}/uv" --version
