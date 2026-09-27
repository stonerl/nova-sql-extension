#!/bin/zsh
# Rebuild/refresh the bundled sqls language server binary, including the
# keyword-hover patch (see patches/sqls/v0.2.48/keyword-hover.patch).
#
# Usage:
#   ./scripts/build-sqls.sh [version]
#
# Requires: go toolchain, python3 (docs generator), Developer ID Application
# identity in keychain (set SIGN_IDENTITY to override), curl, lipo, codesign.
#
# Produces:
#   SQL.novaextension/Executables/sqls         universal arm64+x86_64, Developer ID signed
#   SQL.novaextension/Executables/sqls.sha256  checksum sidecar for README verification

set -euxo pipefail

SQLS_VERSION="${1:-0.2.48}"
REPO="sqls-server/sqls"
WORKINGDIR=$(pwd)
PATCH="${WORKINGDIR}/patches/sqls/v${SQLS_VERSION}/keyword-hover.patch"
GEN="${WORKINGDIR}/scripts/gen-keyword-docs.py"
EXECUTABLES_DIR="${WORKINGDIR}/SQL.novaextension/Executables"

SIGN_IDENTITY="${SIGN_IDENTITY:-Developer ID Application: Toni Foerster (456BPWQ6U5)}"

# Build OUTSIDE the repository: `git apply` inside build/ would discover
# this repo's .git and silently resolve patch paths against the repo root
# instead of the source tree. /tmp (not TMPDIR=/var/folders) — binaries
# built under /var/folders get killed on exec by macOS provenance checks.
BUILD_DIR="$(mktemp -d /tmp/sqls-build-XXXXXX)"
trap 'rm -rf "${BUILD_DIR}"' EXIT

mkdir -p "${EXECUTABLES_DIR}"

# --- 1. Fetch pinned source --------------------------------------------
cd "${BUILD_DIR}"
curl -sL -o source.tar.gz "https://github.com/${REPO}/archive/refs/tags/v${SQLS_VERSION}.tar.gz"
mkdir -p src && tar -xzf source.tar.gz -C src --strip-components=1
rm source.tar.gz

# --- 2. Apply patches + generate docs ----------------------------------
for P in "${WORKINGDIR}"/patches/sqls/v"${SQLS_VERSION}"/*.patch; do
  git -C src apply "${P}"
done
# Assert the patches really landed (guards against silent no-op applies;
# note: git apply inside a nested git repo would resolve patch paths
# against the repo root — the /tmp BUILD_DIR below avoids that).
grep -q "findKeywordNode" src/internal/handler/hover.go
grep -q "func keywordHover" src/internal/handler/keyword_hover.go
grep -q "Log-only" src/internal/lsp/client.go
python3 "${GEN}" src > src/internal/handler/keyword_docs.go
grep -q "most fundamental" src/internal/handler/keyword_docs.go

# --- 3. Build both architectures (CGO for sqlite3) ---------------------
CGO_ENABLED=1 GOOS=darwin GOARCH=amd64 go build -C src -trimpath -ldflags "-s -w" -o "${BUILD_DIR}/exe-x64/sqls" ./
lipo -info exe-x64/sqls | grep x86_64
CGO_ENABLED=1 GOOS=darwin GOARCH=arm64 go build -C src -trimpath -ldflags "-s -w" -o "${BUILD_DIR}/exe-a64/sqls" ./
lipo -info exe-a64/sqls | grep arm64

# --- 4. Merge into a universal binary ----------------------------------
lipo -create exe-x64/sqls exe-a64/sqls -output sqls

# --- 5. Strip quarantine attrs, Developer ID sign, verify --------------
xattr -c sqls 2> /dev/null || true
codesign --force --timestamp --sign "${SIGN_IDENTITY}" sqls
codesign -v sqls
spctl -a -t execute -vv sqls 2> /dev/null || true

# --- 6. Install + checksum sidecar ------------------------------------
# rm BEFORE cp: overwriting in place keeps the old inode, whose stale
# Gatekeeper/AMFI verdict can SIGKILL the new binary on exec.
rm -f "${EXECUTABLES_DIR}/sqls"
cp sqls "${EXECUTABLES_DIR}/sqls"
chmod +x "${EXECUTABLES_DIR}/sqls"
"${EXECUTABLES_DIR}/sqls" --help > /dev/null # self-test: executable & runs
(cd "${EXECUTABLES_DIR}" && shasum -a 256 sqls | awk '{print $1}' > sqls.sha256)

# --- 7. Cleanup (handled by EXIT trap) ---------------------------------
cd "${WORKINGDIR}"

echo "Done: ${EXECUTABLES_DIR}/sqls (sqls v${SQLS_VERSION} + keyword-hover patch, universal, signed)"
