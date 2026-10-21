import numpy as np, json, exp, core, copy
from sklearn.metrics import roc_auc_score
M=['ccs','unordered','noorder','noiso','nodecay','lr','gbm']
seeds=list(range(10)); allr=[]
for sd in seeds:
    o=exp.run_seed(1000+sd); allr.append(o['res']); print('seed',sd,flush=True)
def agg(f):
    a=np.array([f(r) for r in allr]); return [float(a.mean()),float(a.std(ddof=1))]
summ={}
for v in M:
    summ[v]=dict(AUC=agg(lambda r:r[v]['AUC']))
    for op in ['act','warn']:
        for k in ['P','R','F1','FPR','pre','lead']:
            summ[v][op+'_'+k]=agg(lambda r:r[v][op][k])
    if 'adv_act' in allr[0][v]:
        summ[v]['adv_act']=agg(lambda r:r[v]['adv_act']); summ[v]['adv_warn']=agg(lambda r:r[v]['adv_warn'])
    summ[v]['kinds_act']={k:agg(lambda r,k=k:r[v]['act']['kinds'][k]) for k in allr[0][v]['act']['kinds']}
for rn in ['R1','R2']:
    summ[rn]={k:agg(lambda r:r['rules'][rn][k]) for k in ['P','R','F1','FPR','pre']}
json.dump(summ,open('../results/multiseed.json','w'),indent=1)
# ---- bootstrap on seed 42 ----
o=exp.run_seed(42,keep=True); ss,sc,test=o['ss'],o['sc'],o['test']; res=o['res']
rng=np.random.default_rng(7); B=1000
def pre_warn(v,sub):
    tw=res[v]['tw']; lead=[]
    for i in sub:
        S=ss[i]
        if S['label'] and S['pay'] is not None:
            ts,ci=sc[v][i]; j=np.where(ci>=tw)[0]
            if len(j): lead.append(S['pay']-ts[j[0]]>0)
    return np.mean(lead) if lead else 0
boot={v:{'AUC':[],'pre':[]} for v in ['ccs','unordered','lr','gbm']}; dAUC=[]; dPre=[]
test=np.array(test)
for b in range(B):
    sub=rng.choice(test,len(test),replace=True); y=[ss[i]['label'] for i in sub]
    for v in boot:
        boot[v]['AUC'].append(roc_auc_score(y,[sc[v][i][1].max() for i in sub])); boot[v]['pre'].append(pre_warn(v,sub))
    dAUC.append(boot['ccs']['AUC'][-1]-boot['unordered']['AUC'][-1]); dPre.append(boot['ccs']['pre'][-1]-boot['unordered']['pre'][-1])
ci=lambda a:[float(np.percentile(a,2.5)),float(np.percentile(a,97.5))]
bs={v:{k:[float(np.mean(x))]+ci(x) for k,x in d.items()} for v,d in boot.items()}
bs['diff_ccs_minus_unordered']={'AUC':[float(np.mean(dAUC))]+ci(dAUC),'pre':[float(np.mean(dPre))]+ci(dPre)}
# exposure at CCS act alerts on seed 42
ta=res['ccs']['ta']; ex=[];co=[]
for i in test:
    S=ss[i]; ts,c=sc['ccs'][i]; j=np.where(c>=ta)[0]
    if S['label'] and len(j): t=ts[j[0]]; ex.append(core.share_on(S['share'],t)); co.append(core.cam_on(S['cam'],t) and not core.share_on(S['share'],t))
bs['exposure']=dict(share=float(np.mean(ex)),cam=float(np.mean(co)),n=len(ex))
# trajectories for figure
trs={}
for i in test:
    S=ss[i]
    for key,kind in [('scam','scam_full'),('work','b_work_share'),('family','b_family_video'),('tele','b_telehealth')]:
        if key not in trs and S['kind']==kind and 95<S['end']<130:
            trs[key]=dict(ts=sc['ccs'][i][0].tolist(),ccs=sc['ccs'][i][1].tolist(),unord=sc['unordered'][i][1].tolist(),pay=S['pay'])
bs['traj']=trs; bs['thr']=dict(ccs_act=res['ccs']['ta'],ccs_warn=res['ccs']['tw'])
json.dump(bs,open('../results/bootstrap.json','w'))
# ---- weight sensitivity ----
sens=[]; r2=np.random.default_rng(11)
for d in range(30):
    W={k:(s,min(0.95,w*r2.uniform(0.7,1.3))) for k,(s,w) in core.W.items()}
    oo=exp.run_seed(42,W=W,variants=('ccs','unordered'),do_learned=False)['res']
    sens.append({v:dict(AUC=oo[v]['AUC'],pre=oo[v]['warn']['pre'],R=oo[v]['act']['R'],FPR=oo[v]['act']['FPR']) for v in ['ccs','unordered']})
json.dump(sens,open('../results/sensitivity.json','w'))
print('done')
