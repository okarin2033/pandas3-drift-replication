#!/bin/bash
# ENV_TERMS: freeze + probe every venv; log to probe_log.txt. Re-runnable.
E="$(cd "$(dirname "$0")" && pwd)"; cd "$E"
export UV_CACHE_DIR="$E/.uv-cache" UV_NO_CONFIG=1
: > probe_log.txt
echo "probe run $(date '+%Y-%m-%d %H:%M %Z'); uv $(/opt/homebrew/bin/uv --version)" >> probe_log.txt
fail=0
while read name pdv pa; do
  /opt/homebrew/bin/uv pip freeze --python $name/bin/python 2>/dev/null > $name.freeze.txt
  $name/bin/python probe_env.py $name $pdv $pa > $name.probe.json 2> $name.probe.err; rc=$?
  echo "$name expected_pandas=$pdv pyarrow=$pa exit=$rc $(python3 -I -c "import json;d=json.load(open('$name.probe.json'));print('pandas',d['pandas'],'numpy',d['numpy'],'py',d['python'],'import_pyarrow:',d['import_pyarrow'][:60],'errors:',d['errors'])" 2>&1)" >> probe_log.txt
  [ $rc -ne 0 ] && fail=1
done <<LIST
pd233 2.3.3 no
pd31x 3.1.1 no
pd30x 3.0.6 no
pd233pa 2.3.3 yes
pd31xpa 3.1.1 yes
pd30xpa 3.0.6 yes
pd223 2.2.3 no
tools 3.1.1 no
LIST
echo "overall_fail=$fail" >> probe_log.txt
