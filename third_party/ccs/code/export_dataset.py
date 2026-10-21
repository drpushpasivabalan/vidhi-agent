import numpy as np, csv, os, json, sys
import core, exp
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
STAGE={0:'S0_Contact',1:'S1_Authority',2:'S2_Isolation',3:'S3_Extraction'}
sess=open(f'{out}/sessions.csv','w',newline=''); ev=open(f'{out}/events.csv','w',newline=''); iv=open(f'{out}/intervals.csv','w',newline='')
ws=csv.writer(sess); we=csv.writer(ev); wi=csv.writer(iv)
ws.writerow(['seed','session_id','scenario','label','is_adaptive','split','duration_min','payment_time_min','n_events'])
we.writerow(['seed','session_id','time_min','event_type','stage','base_weight'])
wi.writerow(['seed','session_id','interval_type','start_min','end_min'])
def dump(seed,sid,S,split,adaptive):
    ws.writerow([seed,sid,S['kind'],S['label'],int(adaptive),split,round(S['end'],3),'' if S['pay'] is None else round(S['pay'],3),len(S['ev'])])
    for t,k in S['ev']:
        st,w=core.W[k]; we.writerow([seed,sid,round(t,3),k,STAGE[st],w])
    for a,b in S['cam']: wi.writerow([seed,sid,'camera',round(a,3),round(b,3)])
    for a,b in S['share']: wi.writerow([seed,sid,'screen_share',round(a,3),round(b,3)])
counts={}
for seed in [42]+[1000+i for i in range(10)]:
    ss,adv=exp.make(seed)
    r=np.random.default_rng(seed+1000); idx=r.permutation(len(ss)); n=len(ss)
    split={}
    for i in idx[:int(.4*n)]: split[int(i)]='train'
    for i in idx[int(.4*n):int(.6*n)]: split[int(i)]='validation'
    for i in idx[int(.6*n):]: split[int(i)]='test'
    for i,S in enumerate(ss): dump(seed,f'{seed}-{i:04d}',S,split[i],False)
    for j,S in enumerate(adv): dump(seed,f'{seed}-A{j:03d}',S,'adaptive_test',True)
    counts[seed]=dict(sessions=len(ss),scam=sum(s['label'] for s in ss),adaptive=len(adv))
for f in (sess,ev,iv): f.close()
json.dump(counts,open(f'{out}/counts.json','w'),indent=1); print(counts)
