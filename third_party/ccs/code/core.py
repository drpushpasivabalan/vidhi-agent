import numpy as np, math, json
rng = np.random.default_rng(42)
# ---------------- event weights ----------------
W = {'unknown_start':(0,0.5),'voip':(0,0.3),'cam':(0,0.3),
     'file_rx':(1,0.5),'share':(1,0.3),
     'trusted_declined':(2,0.6),'dnd':(2,0.5),'redial':(2,0.4),
     'pay_live':(3,0.6),'pay_post':(3,0.45),'fin_sms':(3,0.4)}
HL = [60,60,60,20]; LAM=[math.log(2)/h for h in HL]
ALPHA=[0.1,0.2,0.3,0.4]; THETA=[0.45,0.4,0.5,0.4]; EPS=0.2; DELTA=2; KAPPA=1; D0=30
def sig(x): return 1/(1+math.exp(-x))

def gen_session(kind):
    """returns dict: events list of (t,type), cam_intervals, share_intervals, end, label, pay_time"""
    ev=[]; cam=[]; share=[]; label=0; pay=None
    u=lambda a,b: rng.uniform(min(a,b),max(a,b))
    if kind.startswith('scam'):
        label=1
        dur=u(40,180) if kind!='scam_evasive' else u(15,35)
        ev += [(0,'unknown_start'),(0,'voip')]
        video = kind!='scam_audio' 
        if video: ev.append((0,'cam')); cam=[(0,dur)]
        tf=u(3,15)
        if rng.random()<0.8: ev.append((tf,'file_rx'))
        if rng.random()<0.45: s0=u(tf,dur*0.6); share=[(s0,dur)]; ev.append((s0,'share'))
        # isolation
        for _ in range(rng.poisson(1.5 if kind!='scam_evasive' else 0.6)):
            ev.append((u(15,dur),'trusted_declined'))
        if rng.random()<0.35: ev.append((u(10,dur*0.5),'dnd'))
        if kind=='scam_evasive' or rng.random()<0.3:
            ev.append((u(10,dur*0.7),'redial'))
        # extraction
        if kind=='scam_partial':
            end=dur  # victim hangs up, no payment
        else:
            if kind=='scam_postpay' :
                pay=dur+u(2,25); ev.append((pay,'pay_post'))
            else:
                pay=u(max(dur*0.6,12),dur); ev.append((pay,'pay_live'))
            if rng.random()<0.7: ev.append((pay+u(0.5,3) if pay<dur else pay+u(0.5,3),'fin_sms'))
        end=dur
    else:
        if kind=='b_family_video':   # known contacts not usually untrusted, but include untrusted relatives/new numbers
            dur=u(30,150); ev=[(0,'unknown_start'),(0,'cam')]; cam=[(0,dur)]
            if rng.random()<0.4: ev.append((0,'voip'))
            if rng.random()<0.2: ev.append((u(5,dur),'file_rx'))
            if rng.random()<0.15: ev.append((u(10,dur),'trusted_declined'))
        elif kind=='b_work_share':
            dur=u(30,120); ev=[(0,'unknown_start'),(0,'voip'),(0,'cam')]; cam=[(0,dur)]
            s0=u(1,10); share=[(s0,dur)]; ev.append((s0,'share'))
            if rng.random()<0.6: ev.append((u(1,dur),'file_rx'))
            for _ in range(rng.poisson(0.8)): ev.append((u(5,dur),'trusted_declined'))
            if rng.random()<0.3: ev.append((u(0,dur),'dnd'))
            if rng.random()<0.1: ev.append((u(dur*0.5,dur),'pay_live'))
        elif kind=='b_pay_during_call':
            dur=u(5,40); ev=[(0,'unknown_start')]
            if rng.random()<0.3: ev.append((0,'voip'))
            if rng.random()<0.3: ev.append((0,'cam')); cam=[(0,dur)]
            if rng.random()<0.3: ev.append((u(1,dur),'file_rx'))
            pay=u(1,dur); ev.append((pay,'pay_live'))
            if rng.random()<0.8: ev.append((pay+u(0.5,2),'fin_sms'))
        elif kind=='b_delivery':
            dur=u(1,6); ev=[(0,'unknown_start')]
            if rng.random()<0.5: ev.append((dur+u(1,20),'pay_post'))
        elif kind=='b_telehealth':
            dur=u(15,60); ev=[(0,'unknown_start'),(0,'voip'),(0,'cam')]; cam=[(0,dur)]
            if rng.random()<0.7: ev.append((u(5,dur),'file_rx'))
            if rng.random()<0.2: ev.append((u(5,dur),'trusted_declined'))
            if rng.random()<0.6: ev.append((dur+u(1,15),'pay_post'))
        end=dur
    ev.sort()
    return dict(ev=ev,cam=cam,share=share,end=end,label=label,pay=pay,kind=kind)

def cam_dur(cam,t):
    return sum(max(0,min(b,t)-a) for a,b in cam)
def share_on(share,t): return any(a<=t<b for a,b in share)
def cam_on(cam,t): return any(a<=t<b for a,b in cam)

def evidence(S,t,use_decay=True,use_iso=True):
    e=[0]*4
    for s in range(4):
        prod=1
        for ti,k in S['ev']:
            if ti>t: break
            st,w=W[k]
            if st!=s: continue
            if not use_iso and s==2: continue
            dec=math.exp(-LAM[s]*(t-ti)) if use_decay else 1
            prod*=1-w*dec
        if s==2 and use_iso:
            d=cam_dur(S['cam'],t); prod*=1-0.8*(1-math.exp(-d/D0))
        e[s]=1-prod
    return e

def ci_series(S,variant='ccs',step=1.0):
    T=S['end']+30; ts=np.arange(0,T+1e-9,step)
    tau=[None]*4; peak=[0]*4; out=[]
    for t in ts:
        e=evidence(S,t,use_decay=(variant!='nodecay'),use_iso=(variant!='noiso'))
        for s in range(4):
            peak[s]=max(peak[s],e[s])
            if tau[s] is None and e[s]>=THETA[s]: tau[s]=t
        if variant=='unordered':
            ci=sum(a*x for a,x in zip(ALPHA,e))/sum(ALPHA)
        else:
            num=0
            for s in range(4):
                g=1
                for r in range(s):
                    phi=1.0
                    if variant!='noorder' and tau[r] is not None and tau[s] is not None:
                        phi=sig((tau[s]-tau[r]+DELTA)/KAPPA)
                    if variant!='noorder' and tau[r] is None and tau[s] is not None:
                        phi=0.0 if variant=='strict' else 1.0
                    g*=(EPS+(1-EPS)*peak[r])*phi
                num+=ALPHA[s]*e[s]*g
            ci=num/sum(ALPHA)
        out.append(ci)
    return ts,np.array(out)

def baseline_duration(S,thr=40):
    # alert if continuous camera/call with unknown > thr minutes
    return S['end']>=thr, (thr if S['end']>=thr else None)
def baseline_paycall(S):
    ts=[t for t,k in S['ev'] if k in('pay_live',)]
    return (len(ts)>0,(ts[0] if ts else None))

