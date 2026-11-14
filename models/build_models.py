# Read-only: builds models.tsv and cost table from the saved OpenRouter list. 2026-11-11
import json,sys,os
base=sys.argv[1]
d={m['id']:m for m in json.load(open(base+'/models/downloads/openrouter_models_2026-11-11.json'))['data']}
V='vendor-documented'
# id: (open_weights, vendor cutoff, source, selected, role)
doc={
'openai/gpt-oss-20b':('yes','2024-06-01','https://developers.openai.com/api/docs/models/gpt-oss-20b (accessed 2026-11-11)'),
'google/gemma-4-31b-it':('yes','2025-01 (pre-training data)','https://huggingface.co/google/gemma-4-31b-it and https://ai.google.dev/gemma/docs/core/model_card_4 (2026-11-11)'),
'google/gemma-4-26b-a4b-it':('yes','2025-01 (pre-training data)','https://ai.google.dev/gemma/docs/core/model_card_4 (2026-11-11)'),
'anthropic/claude-haiku-4.5':('no','2025-02 reliable; 2025-07 training data','https://platform.claude.com/docs/en/models/haiku-4-5/overview (2026-11-11)'),
'openai/gpt-5.4-mini':('no','2025-08-31','https://developers.openai.com/api/docs/models/gpt-5.4-mini (2026-11-11)'),
'openai/gpt-5.6-terra':('no','2026-02-16','https://developers.openai.com/api/docs/models/gpt-5.6-terra (2026-11-11)'),
'anthropic/claude-haiku-5.5':('no','2026-06 reliable; 2026-06 training data','https://platform.claude.com/docs/en/models/overview (2026-11-11)'),
'anthropic/claude-sonnet-5.5':('no','2026-06 reliable; 2026-06 training data','https://platform.claude.com/docs/en/models/overview (2026-11-11)'),
'qwen/qwen3.5-9b':('yes','not documented','https://huggingface.co/Qwen/Qwen3.5-9B card has no cutoff (2026-11-11)'),
'mistralai/ministral-8b-2512':('yes','not documented','https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512 card has no cutoff (2026-11-11)'),
'deepseek/deepseek-v3.2':('yes','not documented','https://huggingface.co/deepseek-ai/DeepSeek-V3.2 card has no cutoff (2026-11-11)'),
'google/gemini-3.8-flash':('no','not documented','https://aistudio.google.com/docs/models/gemini-3.8-flash states none (2026-11-11)'),
'openai/gpt-oss-120b':('yes','2024-06 (OpenRouter field only; vendor page not fetched)','not verified'),
'qwen/qwen3.6-35b-a3b':('yes','not documented','https://huggingface.co/Qwen/Qwen3.6-35B-A3B card has no cutoff (2026-11-11)'),
'mistralai/mistral-small-2603':('yes','not checked','not fetched'),
'anthropic/claude-sonnet-4.6':('no','not checked','not fetched'),
'anthropic/claude-opus-5.5':('no','2026-06 reliable','https://platform.claude.com/docs/en/models/overview (2026-11-11)'),
'z-ai/glm-4.7-flash':('yes','not checked','not fetched'),
'qwen/qwen3-coder-30b-a3b-instruct':('yes','not checked','not fetched'),
'nvidia/nemotron-3-nano-30b-a3b':('yes','not checked','not fetched'),
'ibm-granite/granite-4.2-8b':('yes','not checked','not fetched'),
'google/gemma-4-26b-a4b-it ':('','','',),
}
doc.pop('google/gemma-4-26b-a4b-it ')
sel=['openai/gpt-oss-20b','qwen/qwen3.5-9b','google/gemma-4-31b-it','deepseek/deepseek-v3.2','anthropic/claude-haiku-4.5','openai/gpt-5.4-mini','openai/gpt-5.6-terra','anthropic/claude-haiku-5.5','anthropic/claude-sonnet-5.5','qwen/qwen3.6-35b-a3b']
PT,CT=390,550  # conservative: max of pilot means (see COST.md)
rows=[]
hdr=['selected','openrouter_id','open_weights','usd_per_M_prompt','usd_per_M_completion','vendor_knowledge_cutoff','cutoff_vs_pandas3_0_0_(2026-01-21)','cutoff_source','openrouter_cutoff_field_(not_vendor)','context','hf_id','usd_per_program_nothink']
for i,(ow,cut,src) in doc.items():
    m=d.get(i)
    if not m: print('missing',i);continue
    pi=float(m['pricing']['prompt'])*1e6; po=float(m['pricing']['completion'])*1e6
    c=cut[:7]
    rel='before' if c<'2026-01' and c[:2]=='20' else ('after' if c[:2]=='20' else 'unknown')
    if cut.startswith('2026-02') or cut.startswith('2026-06'): rel='after'
    pp=(PT*pi+CT*po)/1e6
    rows.append(['yes' if i in sel else 'no',i,ow,f'{pi:.3f}',f'{po:.3f}',cut,rel,src,str(m.get('knowledge_cutoff')),str(m['context_length']),str(m.get('hugging_face_id')),f'{pp:.6f}'])
rows.sort(key=lambda r:(r[0]!='yes',float(r[3])))
open(base+'/models/models.tsv','w').write('\t'.join(hdr)+'\n'+'\n'.join('\t'.join(r) for r in rows)+'\n')
# cost
out=[]
for i in sel:
    m=d[i];pi=float(m['pricing']['prompt'])*1e6;po=float(m['pricing']['completion'])*1e6
    out.append((i,pi,po))
for (N,k) in [(150,5),(200,5),(300,5)]:
    tot=0;line=[]
    for i,pi,po in out:
        c=N*k*(PT*pi+CT*po)/1e6; tot+=c; line.append((i,c))
    print(N,k,round(tot,2),[(i.split('/')[1],round(c,2)) for i,c in line])
print(rows[0])
