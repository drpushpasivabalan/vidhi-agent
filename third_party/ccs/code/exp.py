import numpy as np, math, json, time, collections, sys
import core
from core import gen_session, share_on, cam_on
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

KS={'scam_full':220,'scam_postpay':80,'scam_partial':60,'scam_evasive':60,'scam_audio':40}
KB={'b_family_video':300,'b_work_share':250,'b_pay_during_call':300,'b_delivery':300,'b_telehealth':150}

def adaptive(S):
    # fraudster adapts: lets victim answer family calls, no DND, no screen share
    S=dict(S); S['ev']=[(t,k) for t,k in S['ev'] if k not in ('trusted_declined','dnd','share')]; S['share']=[]; S['kind']='scam_adaptive'; return S

def make(seed):
    core.rng=np.random.default_rng(seed)
    ss=[]
    for k,n in {**KS,**KB}.items(): ss+=[gen_session(k) for _ in range(n)]
    adv=[adaptive(gen_session('scam_full')) for _ in range(60)]
    return ss,adv

def stage_series(S,W,use_decay=True,use_iso=True,step=1.0):
    T=S['end']+30; ts=np.arange(0,T+1e-9,step)
    e=np.zeros((4,len(ts)))
    for s in range(4):
        prod=np.ones(len(ts))
        if not (s==2 and not use_iso):
            for ti,k in S['ev']:
                st,w=W[k]
                if st!=s: continue
                dt=ts-ti; dec=np.exp(-core.LAM[s]*np.clip(dt,0,None)) if use_decay else 1.0
                prod*=np.where(dt>=0,1-w*dec,1.0)
            if s==2:
                d=np.zeros(len(ts))
                for a,b in S['cam']: d+=np.clip(np.minimum(b,ts)-a,0,None)
                prod*=1-0.8*(1-np.exp(-d/core.D0))
        e[s]=1-prod
    return ts,e

def ci_from(ts,e,variant):
    A=np.array(core.ALPHA)
    if variant=='unordered': return (A[:,None]*e).sum(0)/A.sum()
    m=np.maximum.accumulate(e,axis=1)
    tau=[]
    for s in range(4):
        idx=np.where(e[s]>=core.THETA[s])[0]; tau.append(ts[idx[0]] if len(idx) else np.inf)
    num=np.zeros(len(ts))
    for s in range(4):
        g=np.ones(len(ts))
        for r in range(s):
            phi=np.ones(len(ts))
            if variant!='noorder' and np.isfinite(tau[r]) and np.isfinite(tau[s]):
                both=(ts>=tau[r])&(ts>=tau[s]); val=1/(1+math.exp(-(tau[s]-tau[r]+core.DELTA)/core.KAPPA))
                phi=np.where(both,val,1.0)
            g*=(core.EPS+(1-core.EPS)*m[r])*phi
        num+=A[s]*e[s]*g
    return num/A.sum()

def feats(ts,e):
    m=np.maximum.accumulate(e,axis=1); return np.vstack([e,m]).T  # T x 8

def score_all(ss,W,variants):
    out={v:[] for v in variants}; F=[]
    for S in ss:
        ts,e=stage_series(S,W)
        for v in variants:
            if v in('ccs','unordered','noorder'): out[v].append((ts,ci_from(ts,e,v)))
        if 'noiso' in variants:
            t2,e2=stage_series(S,W,use_iso=False); out['noiso'].append((t2,ci_from(t2,e2,'ccs')))
        if 'nodecay' in variants:
            t3,e3=stage_series(S,W,use_decay=False); out['nodecay'].append((t3,ci_from(t3,e3,'ccs')))
        F.append((ts,feats(ts,e)))
    return out,F

def learned(F,ss,train,kind):
    X=[];y=[]
    for i in train:
        ts,f=F[i]; X.append(f[::5]); y+= [ss[i]['label']]*len(f[::5])
    X=np.vstack(X); y=np.array(y)
    mdl=LogisticRegression(max_iter=2000,class_weight='balanced') if kind=='lr' else HistGradientBoostingClassifier(max_iter=200,learning_rate=0.08,max_depth=4,class_weight='balanced',random_state=0)
    mdl.fit(X,y)
    return [(ts,mdl.predict_proba(f)[:,1]) for ts,f in F], mdl

def evaluate(ss,sc,thr,subset):
    tp=fp=fn=tn=0; lead=[]; kinds=collections.defaultdict(list); alerts={}
    for i in subset:
        S=ss[i]; ts,ci=sc[i]; j=np.where(ci>=thr)[0]; a=len(j)>0
        kinds[S['kind']].append(a); alerts[i]=ts[j[0]] if a else None
        if S['label']:
            if a:
                tp+=1
                if S['pay'] is not None: lead.append(S['pay']-ts[j[0]])
            else: fn+=1
        else:
            fp+=a; tn+=(not a)
    P=tp/(tp+fp) if tp+fp else 0; R=tp/(tp+fn) if tp+fn else 0
    return dict(P=P,R=R,F1=2*P*R/(P+R) if P+R else 0,FPR=fp/(fp+tn) if fp+tn else 0,
                pre=float(np.mean([x>0 for x in lead])) if lead else 0.0, lead=float(np.median(lead)) if lead else float('nan'),
                kinds={k:float(np.mean(v)) for k,v in kinds.items()}, alerts=alerts)

def calibrate(ss,sc,train,fpr):
    peaks=np.array([sc[i][1].max() for i in train]); lab=np.array([ss[i]['label'] for i in train])
    neg=np.sort(peaks[lab==0])[::-1]; k=int(math.floor(fpr*len(neg)))
    # threshold just above the (k+1)-th highest negative peak
    return float(neg[k])+1e-6 if k<len(neg) else 0.0

def rules(ss,subset):
    res={}
    for name in ['R1','R2']:
        tp=fp=fn=tn=0; lead=[]
        for i in subset:
            S=ss[i]
            if name=='R1': a=S['end']>=40; ta=40 if a else None
            else:
                t=[x for x,k in S['ev'] if k=='pay_live']; a=bool(t); ta=t[0] if a else None
            if S['label']:
                if a: tp+=1; lead+= [S['pay']-ta] if S['pay'] is not None else []
                else: fn+=1
            else: fp+=a; tn+=(not a)
        P=tp/(tp+fp); R=tp/(tp+fn)
        res[name]=dict(P=P,R=R,F1=2*P*R/(P+R),FPR=fp/(fp+tn),pre=float(np.mean([x>0 for x in lead])))
    return res

def run_seed(seed,W=None,variants=('ccs','unordered','noorder','noiso','nodecay'),do_learned=True,keep=False):
    W=W or core.W
    ss,adv=make(seed)
    r=np.random.default_rng(seed+1000); idx=r.permutation(len(ss)); n=len(ss)
    train=sorted(idx[:int(.4*n)].tolist()); val=sorted(idx[int(.4*n):int(.6*n)].tolist()); test=sorted(idx[int(.6*n):].tolist())
    sc,F=score_all(ss,W,variants)
    asc,AF=score_all(adv,W,[v for v in variants if v in('ccs','unordered')])
    if do_learned:
        sc['lr'],m1=learned(F,ss,train,'lr'); sc['gbm'],m2=learned(F,ss,train,'gbm')
        asc['lr']=[(ts,m1.predict_proba(f)[:,1]) for ts,f in AF]; asc['gbm']=[(ts,m2.predict_proba(f)[:,1]) for ts,f in AF]
    res={}
    yte=[ss[i]['label'] for i in test]
    for v,s in sc.items():
        ta=calibrate(ss,s,val,0.05); tw=calibrate(ss,s,val,0.15)
        act=evaluate(ss,s,ta,test); warn=evaluate(ss,s,tw,test)
        res[v]=dict(AUC=roc_auc_score(yte,[s[i][1].max() for i in test]),act=act,warn=warn,ta=ta,tw=tw)
        if v in asc:
            res[v]['adv_act']=float(np.mean([a[1].max()>=ta for a in asc[v]])); res[v]['adv_warn']=float(np.mean([a[1].max()>=tw for a in asc[v]]))
    res['rules']=rules(ss,test)
    out=dict(res=res)
    if keep: out.update(ss=ss,adv=adv,sc=sc,train=train,val=val,test=test,F=F,W=W)
    return out
