# HRUN configs (stage 2, written 2026-11-11 by pkg:HRUN). Copy-and-extend of the pilot's CONFIGS table (pilots/r3/harness/runner.py)
# to the study configs of FULL_PREREG section 6 and conventions/CONVENTIONS.md section 4. Standard library only.
import dataclasses, os, re

HARNESS = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HARNESS)


@dataclasses.dataclass(frozen=True)
class Config:
    name: str
    venv: str
    mode: str          # base | cow | str | both | stroff | trace
    hash_seed: int
    pyarrow: bool


def _c(name, venv, mode, hash_seed=0, pyarrow=False):
    return Config(name, venv, mode, hash_seed, pyarrow)


CONFIGS = {c.name: c for c in [
    _c('E0a', 'pd233', 'base', 0), _c('E0b', 'pd233', 'base', 1),
    _c('E1', 'pd31x', 'base'), _c('E2', 'pd30x', 'base'),
    _c('E0pa', 'pd233pa', 'base', pyarrow=True), _c('E3', 'pd31xpa', 'base', pyarrow=True),
    _c('E4', 'pd30xpa', 'base', pyarrow=True),
    _c('A1', 'pd233', 'cow'), _c('A2', 'pd233', 'str'), _c('A3', 'pd233', 'both'), _c('A4', 'pd31x', 'stroff'),
    _c('T0', 'pd233', 'trace'), _c('T1', 'pd31x', 'trace'), _c('T2', 'pd30x', 'trace'),
    _c('C1', 'pd223', 'base'),
]}
FIXTURE_VARIANTS = ('main', 'clean', 'dirty')
VARIANT_CONFIGS = ('E0a', 'E0b', 'E1')          # the only base configs that also run on F-clean / F-dirty (section 6)
TRACE_CONFIGS = ('T0', 'T1', 'T2')
LOUD_STATUSES = ('error', 'timeout', 'cpu_limit', 'memory_limit', 'crash')   # LOUD = target raises / times out / limit

_RC = re.compile(r'^(?:V-(clean|dirty)__(E0a|E0b|E1)|(E0a|E0b|E1|E2|E0pa|E3|E4|A1|A2|A3|A4|T0|T1|T2|C1))$')


def run_config_name(config, variant='main'):
    """'E1' (main) | 'V-clean__E1'. Only E0a, E0b, E1 exist on the clean/dirty variants."""
    if config not in CONFIGS:
        raise ValueError('unknown config %r' % config)
    if variant not in FIXTURE_VARIANTS:
        raise ValueError('unknown fixture variant %r' % variant)
    if variant == 'main':
        return config
    if config not in VARIANT_CONFIGS:
        raise ValueError('config %s has no %s variant run (only %s)' % (config, variant, ', '.join(VARIANT_CONFIGS)))
    return 'V-%s__%s' % (variant, config)


def parse_run_config(name):
    """'V-clean__E1' -> ('E1', 'clean'); 'E1' -> ('E1', 'main')."""
    m = _RC.match(name)
    if not m:
        raise ValueError('not a run config name: %r' % name)
    return (m.group(2), m.group(1)) if m.group(1) else (m.group(3), 'main')


# (baseline_run_config, target_run_config), conventions section 4.2. The first group are determinism pairs.
DETERMINISM_PAIRS = [('E0a', 'E0b'), ('V-clean__E0a', 'V-clean__E0b'), ('V-dirty__E0a', 'V-dirty__E0b')]
TARGET_PAIRS = [('E0a', 'E1'), ('E0a', 'E2'), ('E0pa', 'E3'), ('E0pa', 'E4'), ('C1', 'E0a'),
                ('V-clean__E0a', 'V-clean__E1'), ('V-dirty__E0a', 'V-dirty__E1')]
COMPARISON_PAIRS = DETERMINISM_PAIRS[:1] + TARGET_PAIRS[:5] + DETERMINISM_PAIRS[1:2] + TARGET_PAIRS[5:6] + \
    DETERMINISM_PAIRS[2:] + TARGET_PAIRS[6:]


def pair_id(base, target):
    return '%s~%s' % (base, target)


def split_pair(pid):
    a, b = pid.split('~')
    return a, b


def venv_python(venv, study=None):
    return os.path.join(study or STUDY, 'envs', venv, 'bin', 'python')


def run_configs_for(configs, variants=('main',)):
    """Expand base configs x fixture variants into run-config names (variant runs only for E0a, E0b, E1)."""
    out = []
    for v in variants:
        for c in configs:
            if v != 'main' and c not in VARIANT_CONFIGS:
                continue
            out.append(run_config_name(c, v))
    return out
