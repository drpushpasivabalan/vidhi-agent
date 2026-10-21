import json,numpy as np,matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
m=json.load(open('../results/multiseed.json')); b=json.load(open('../results/bootstrap.json')); s=json.load(open('../results/sensitivity.json'))
import os; O='../figures/'; os.makedirs(O,exist_ok=True)
# Fig: warning operating point
meth=[('ccs','CCS'),('unordered','Unordered\nsum'),('lr','Logistic\nregression'),('gbm','Gradient\nboosting'),('R1','Rule R1\n(duration)'),('R2','Rule R2\n(pay in call)')]
def g(v,k):
    if v in('R1','R2'):
        kk={'R':'R','FPR':'FPR','pre':'pre'}[k]; return m[v][kk]
    return m[v]['warn_'+k]
metrics=[('R','Recall'),('FPR','False-alarm rate'),('pre','Warned before payment')]
x=np.arange(len(meth)); w=0.26; hatch=['','//','..']; col=['#4d4d4d','#a6a6a6','#ffffff']
fig,ax=plt.subplots(figsize=(8,3.6))
for j,(k,lab) in enumerate(metrics):
    vals=[g(v,k) for v,_ in meth]
    ax.bar(x+(j-1)*w,[a[0] for a in vals],w,yerr=[a[1] for a in vals],capsize=2.5,label=lab,color=col[j],edgecolor='black',hatch=hatch[j],lw=0.7)
ax.set_xticks(x); ax.set_xticklabels([n for _,n in meth]); ax.set_ylim(0,1.05); ax.set_ylabel('Proportion of test sessions')
ax.legend(frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(0.5,1.14))
ax.yaxis.grid(True,ls=':',lw=0.6); ax.set_axisbelow(True)
plt.tight_layout(); plt.savefig(O+'fig_results_warn.png',dpi=300); plt.close()
# Fig: trajectories
t=b['traj']; thr=b['thr']
fig,ax=plt.subplots(figsize=(7.5,3.4))
sty=[('scam','Scam session','-','black'),('work','Benign work call with screen share','--','#555555'),('tele','Benign telehealth consultation','-.','#555555'),('family','Benign family video call',':','#555555')]
for k,lab,ls,c in sty:
    if k in t:
        ax.plot(t[k]['ts'],t[k]['ccs'],ls=ls,color=c,lw=1.5,label=lab)
if t['scam']['pay']: ax.axvline(t['scam']['pay'],color='black',lw=0.8); ax.text(t['scam']['pay']-1,0.285,'scam payment',fontsize=8,ha='right')
ax.axhline(thr['ccs_warn'],color='gray',lw=0.8,ls=(0,(4,2))); ax.text(1,thr['ccs_warn']+0.004,'θ_warn',fontsize=8)
ax.axhline(thr['ccs_act'],color='gray',lw=0.8,ls=(0,(1,1))); ax.text(1,thr['ccs_act']+0.004,'θ_act',fontsize=8)
ax.set_xlabel('Minutes since session start'); ax.set_ylabel('Coercion index CI(t)'); ax.legend(frameon=False,fontsize=8,loc='upper right')
plt.tight_layout(); plt.savefig(O+'fig_trajectories.png',dpi=300); plt.close()
# Fig: sensitivity
fig,axs=plt.subplots(1,2,figsize=(7.5,3))
for a,(k,lab) in zip(axs,[('AUC','Session-level AUC'),('pre','Warned before payment')]):
    data=[[d[v][k] for d in s] for v in ['ccs','unordered']]
    bp=a.boxplot(data,widths=0.5,patch_artist=True,medianprops=dict(color='black'))
    for p,c in zip(bp['boxes'],['#8c8c8c','white']): p.set_facecolor(c)
    a.set_xticks([1,2]); a.set_xticklabels(['CCS','Unordered sum']); a.set_title(lab,fontsize=10); a.yaxis.grid(True,ls=':',lw=0.6)
plt.tight_layout(); plt.savefig(O+'fig_sensitivity.png',dpi=300); plt.close()
print('ok')
