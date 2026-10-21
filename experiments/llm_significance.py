"""Exact McNemar tests for the LLM experiments -> results/llm_significance.json.  Run: python -m experiments.llm_significance"""
import json, numpy as np
from scipy.stats import binomtest
from experiments import harness as Hn
from experiments.run_llm import load_llm, tuned_cfg, KB, three
from vidhi import context as C
claims, detect, stats, meta = load_llm('results/llm_results.json')
pools=Hn.load_pools(); dev=Hn.Split("dev",pools)
cal=C.Calibrator().fit([dev.ccs(x)["ci_td"] for x in dev.incs],[x["label"] for x in dev.incs])
out={}
def mcn(X,Y,lab,dec='FRAUD'):
    ids=[i for i in X if X[i]['label']==lab]
    b=sum((X[i]['decision']==dec) and (Y[i]['decision']!=dec) for i in ids); c=sum((X[i]['decision']!=dec) and (Y[i]['decision']==dec) for i in ids)
    return [b,c, float(binomtest(min(b,c), b+c, 0.5).pvalue) if b+c else 1.0]
for cond in ("standard","perfect"):
    sp=Hn.Split("test",pools,cond); sp.incs=[x for x in sp.incs if int(x["id"].rsplit("-",1)[1])<25]
    for m in ("qwen2.5:3b","llama3.2:3b"):
        V={r['id']:r for r in Hn.run_vidhi(sp,tuned_cfg(llm_claims=claims[m]),cal,KB)}
        VD={r['id']:r for r in Hn.run_vidhi(sp,tuned_cfg(llm_claims=claims[m],doc_only_requirements=True),cal,KB)}
        L={x['id']:{'label':x['label'],'decision':'FRAUD' if detect[m][x['id']]>0.5 else ('LEGITIMATE' if detect[m][x['id']]<0.5 else 'ABSTAIN_VERIFY')} for x in sp.incs}
        R={r['id']:r for r in Hn.run_vidhi(sp,tuned_cfg(),cal,KB)}
        out[f"{cond}|{m}"]=dict(vidhiD=three(list(VD.values())), same_as_vidhi=sum(V[i]['decision']!=VD[i]['decision'] for i in V),
            lawful_ff_vidhi_vs_llmonly=mcn(V,L,0), fraud_flag_vidhi_vs_llmonly=mcn(V,L,1),
            lawful_ff_vidhi_llm_vs_rules=mcn(V,R,0), fraud_flag_vidhi_llm_vs_rules=mcn(V,R,1))
        print(cond,m,out[f"{cond}|{m}"])
# real-set tests
d=json.load(open('results/llm_results_eval.json'))['real']['rows']
g=lambda k:{r['id']:r for r in d[k]}
for m in ("qwen2.5:3b","llama3.2:3b"):
    A=g(f'VIDHI-D ({m} extractor)'); B=g(f'LLM-only detector ({m})'); Rr=g('VIDHI-D (rule extractor)')
    out[f"real|{m}"]=dict(lawful_ff_vs_llmonly=mcn(A,B,0), fraud_flag_vs_llmonly=mcn(A,B,1), fraud_flag_vs_rules=mcn(A,Rr,1))
    print('real',m,out[f"real|{m}"])
json.dump(out,open('results/llm_significance.json','w'),indent=1)
