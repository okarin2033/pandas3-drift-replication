# Builds harness/gen_configs/<model_key>.json for the 10 selected models from models/models.tsv.
# Written 2026-11-11 by pkg:HSTAT_GEN. Run: python3 -I -B harness/gen_configs/make_configs.py   (idempotent; overwrites)
# Facts used: prices and selection from models/models.tsv; `seed` is listed by OpenRouter for the seven non-Anthropic endpoints and
# not for the three Anthropic endpoints (FULL_PREREG section 15 row 5, checked 2026-11-11). Everything that the paid calibration
# (STAGE2 T7) decides stays the placeholder __FILL_AT_T7__: pinned provider (and the provider name the response reports),
# reasoning request, per-model cap (1.5 x the calibrated estimate, section 13), k if the cost fallback reduces it.
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, '..', '..'))
PH = '__FILL_AT_T7__'
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
PILOT_HINTS = {
    # from the pilot generators (read-only): the provider slug the pilot pinned and the reasoning request it sent
    'anthropic/claude-sonnet-5.5': 'pilot: provider order [anthropic], reasoning {"effort": "low"} (pilots/r3/harness/gen_openrouter.py)',
    'qwen/qwen3.5-9b': 'pilot: served by Together (response.provider "Together"), temperature 0.7 / top_p 0.9 were sent (not in the full study)',
}


def main():
    rows = list(csv.DictReader(open(os.path.join(STUDY, 'models', 'models.tsv'), encoding='utf-8'), delimiter='\t'))
    sel = [r for r in rows if r['selected'] == 'yes']
    for r in sel:
        mid = r['openrouter_id']
        key = mid.replace('/', '__')
        cfg = {
            '_written': '2026-11-11 by pkg:HSTAT_GEN (make_configs.py); status: prepared',
            'model': mid, 'model_key': key, 'endpoint': ENDPOINT,
            'provider': PH, 'provider_response': PH,
            'reasoning': PH,
            'seed_supported': not mid.startswith('anthropic/'),
            'k': 5, 'max_tokens': 8000,
            'price_in_per_m': float(r['usd_per_M_prompt']), 'price_out_per_m': float(r['usd_per_M_completion']),
            'cap_usd': PH, 'total_cap_usd': 40.0, 'workers': 4,
            'planning_estimate_usd_k5_200_tasks': round(1000 * float(r['usd_per_program_nothink']), 4),
            'generate_first': mid == 'anthropic/claude-haiku-4.5',
            'notes': 'temperature and top_p are never sent (lead decision 2). provider, provider_response, reasoning and cap_usd are '
                     'filled at T7 (calibration); a real run refuses to start while any is %s. Haiku 4.5 is generated first '
                     '(lifecycle rule, section 4.1).' % PH,
        }
        if mid in PILOT_HINTS:
            cfg['hint_from_pilot'] = PILOT_HINTS[mid]
        with open(os.path.join(HERE, key + '.json'), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=1)
            f.write('\n')
    print('wrote %d configs' % len(sel))


if __name__ == '__main__':
    main()
