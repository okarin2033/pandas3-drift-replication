#!/bin/bash
# ENV_TERMS / STAGE2 T1: build venvs. Written 2026-11-11. Re-runnable (skips existing venvs).
set -u
E="$(cd "$(dirname "$0")" && pwd)"
export UV_CACHE_DIR="$E/.uv-cache" UV_NO_CONFIG=1 UV_PYTHON_DOWNLOADS=never UV_NO_PROGRESS=1 UV_DEFAULT_INDEX=https://pypi.org/simple
PY="$HOME/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/bin/python3.12"
UV=/opt/homebrew/bin/uv
COMMON="numpy==2.5.4 python-dateutil==4.0.0 tzdata==2026.6"
mk() { # name, pins...
  name=$1; shift
  if [ -x "$E/$name/bin/python" ]; then echo "skip $name"; return; fi
  $UV venv --python "$PY" --no-managed-python "$E/$name" > "$E/logs_$name.venv.log" 2>&1 || { echo "venv fail $name"; return; }
  $UV pip install --python "$E/$name/bin/python" --only-binary :all: --no-config "$@" > "$E/logs_$name.install.log" 2>&1
  echo "$name install exit $?"
}
mk pd233   pandas==2.3.3 $COMMON pytz==2026.6
mk pd31x   pandas==3.1.1 $COMMON
mk pd30x   pandas==3.0.6 $COMMON
mk pd233pa pandas==2.3.3 $COMMON pytz==2026.6 pyarrow==26.0.1
mk pd31xpa pandas==3.1.1 $COMMON pyarrow==26.0.1
mk pd30xpa pandas==3.0.6 $COMMON pyarrow==26.0.1
mk pd223   pandas==2.2.3 $COMMON pytz==2026.6
# analysis-only venv; pandas pinned explicitly because statsmodels depends on it
mk tools   numpy==2.5.4 scipy==1.18.1 statsmodels==0.15.0 jsonschema==4.26.0 pandas==3.1.1 python-dateutil==4.0.0 tzdata==2026.6
