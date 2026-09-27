#!/bin/zsh
set -euxo pipefail

BASEDIR=$1
APPBUNDLE=$2
FRAMEWORKS_PATH="${APPBUNDLE}/Contents/Frameworks/"
WORKINGDIR=$(pwd)

# - Build both arm64 (Apple Silicon) and x86_64 (Intel)
# - Require a minimum of macOS 11.0
# - Include the /src/ directory for headers (for `tree_sitter/parser.h`)
BUILD_FLAGS="-arch arm64 -arch x86_64 -mmacosx-version-min=11.0 -I${BASEDIR}/src/"

# Build in a temporary `build/` directory.
TMP_BUILD_DIR=$WORKINGDIR/build
mkdir -p $TMP_BUILD_DIR

pushd $BASEDIR

CFLAGS="${BUILD_FLAGS} -O3" \
CXXFLAGS="${BUILD_FLAGS} -O3" \
LDFLAGS="${BUILD_FLAGS} -F${FRAMEWORKS_PATH} -framework SyntaxKit -rpath @loader_path/../Frameworks" \
PREFIX="$TMP_BUILD_DIR" make install

popd

# - Sign the built dylib with a Developer ID so macOS accepts it when
#   the extension is loaded on machines other than the build machine.
# - Targets the versioned file: the .dylib in build/lib is a symlink
#   and cannot carry a signature.
DYLIB_PATH="${TMP_BUILD_DIR}/lib/libtree-sitter-sql.15.0.dylib"

if [[ -n "${SIGN_IDENTITY:-}" ]]; then
  codesign --force --timestamp --sign "$SIGN_IDENTITY" "$DYLIB_PATH"
else
  echo "SIGN_IDENTITY not set — skipping Developer ID signing (adhoc signature kept)."
fi
