
import os
import sys
sys.path.insert(0,"..")
import numpy as np
import matplotlib.pyplot as plt
import pyemu
print(pyemu.__file__)
import flopy
import platform
from pathlib import Path
import shutil
import pandas as pd


def plot_ies_results(m_d,tag="",casename="at",ptiter=None):

    pst = pyemu.Pst(os.path.join(m_d,f"{casename}.pst"))
    
    noise = pst.ies.noise
    itrs = pst.ies.phiactual.iteration.values
    obs = pst.observation_data
    nzobs = obs.loc[obs.obgnme=='headgroup',:]
    odict = {n:v for n,v in zip(nzobs.obsnme,nzobs.obsval)}
    if ptiter is None:
        ptiter = itrs.max()
    ptoe = pst.ies.get("obsen{0}".format(ptiter))
    proe = pst.ies.obsen0
    phivals = pst.ies.phimeas.iloc[-1,6:]
    phimean = phivals.mean()
    phistd = phivals.std()
    thresh = phimean + (phistd*1.75)
    keep = phivals[phivals<=thresh].index.values
    ptoe = ptoe.loc[keep]
    proe = proe.loc[keep]
    noise = noise.loc[keep]
    fig,ax = plt.subplots(1,1,figsize=(6,6))
    names = obs.loc[obs.obgnme=="headgroup","obsnme"].values
    for oname in names:
        if "at.csv" not in oname:
            continue
        ovals = [odict[oname] for _ in range(noise.shape[0])]
        ax.scatter(ovals,noise[oname],marker='.',c='r',s=100,alpha=0.25)
        
        ovals = [odict[oname] for _ in range(ptoe.shape[0])]
        ax.scatter(ovals,ptoe[oname],marker='.',c='b',alpha=0.5)
        #ylim = ax.get_ylim()
        ovals = [odict[oname] for _ in range(proe.shape[0])]
        ax.scatter(ovals,proe[oname],marker='.',c='0.5',alpha=0.5,zorder=0)
        #ax.set_ylim(ylim)
        #ax.set_xlim(ylim)
    mn,mx = noise.loc[:,names].values.min(),noise.loc[:,names].values.max()
    ax.plot([mn,mx],[mn,mx],"k--",lw=3)
    ax.set_xlabel("obs")
    ax.set_ylabel("sim")
    ax.set_xlim(mn,mx)
    ax.set_title(tag)
    
    _ = ax.set_ylim(mn,mx)

    kobs = obs.loc[obs.obsnme.str.contains("k_aq"),:].copy()
    kobs['i'] = kobs.i.astype(int)
    kobs['j'] = kobs.j.astype(int)

    prarr = np.zeros((kobs.i.max()+1,kobs.j.max()+1))
    prarr[kobs.i,kobs.j] = np.log10(ptoe.loc[:,kobs.obsnme].mean())
    ptarr = np.zeros((kobs.i.max()+1,kobs.j.max()+1))
    ptarr[kobs.i,kobs.j] = np.log10(ptoe.loc["base",kobs.obsnme])
    fig,axes = plt.subplots(1,2,figsize=(8,4))
    cb = axes[0].imshow(prarr,vmin=ptarr.min())
    plt.colorbar(cb,ax=axes[0])
    axes[0].set_title("mean "+tag)
    
    cb = axes[1].imshow(ptarr,vmax=prarr.max())
    plt.colorbar(cb,ax=axes[1])
    axes[1].set_title("min err var "+tag)

    prarr = np.zeros((kobs.i.max()+1,kobs.j.max()+1))
    prarr[kobs.i,kobs.j] = np.log10(proe.loc[:,kobs.obsnme].std())
    ptarr = np.zeros((kobs.i.max()+1,kobs.j.max()+1))
    ptarr[kobs.i,kobs.j] = np.log10(ptoe.loc[:,kobs.obsnme].std())
    fig,axes = plt.subplots(1,2,figsize=(8,4))
    cb = axes[0].imshow(prarr,vmin=ptarr.min())
    plt.colorbar(cb,ax=axes[0])
    axes[0].set_title("prior stdev "+tag)
    cb = axes[1].imshow(ptarr,vmax=prarr.max())
    plt.colorbar(cb,ax=axes[1])
    axes[1].set_title("posterior stdev "+tag)

    bobs = obs.loc[obs.oname=="at.budget.csv",:]
    for oname in bobs.obsnme:
        if "chd" not in oname:
            continue
        fig,ax = plt.subplots(1,1,figsize=(6,6))
        ax.hist(proe.loc[:,oname],bins=10,fc="0.5",alpha=0.5,density=True)
        ax.hist(ptoe.loc[:,oname],bins=10,fc="b",alpha=0.5,density=True)
        ax.set_title(tag+" "+oname)
        ax.set_yticks([])
    
    names = obs.loc[obs.obgnme=="headgroup","obsnme"].values
    noise = pst.ies.noise
    proe = pst.ies.obsen0
    ptoe = pst.ies.get("obsen{0}".format(pst.ies.phiactual.iteration.max()))
    phivals = pst.ies.phimeas.iloc[-1,6:]
    phimean = phivals.mean()
    phistd = phivals.std()
    thresh = phimean + (phistd*1.75)
    keep = phivals[phivals<=thresh].index.values
    fig,axes = plt.subplots(2,1,figsize=(10,20))
    actual,meas = pst.ies.phiactual.iloc[:,6:],pst.ies.phimeas.iloc[:,6:]
    actual = actual.loc[:,keep]
    meas = meas.loc[:,keep]
    
    axes[0].hist(np.log10(actual.iloc[0,:].values),fc="0.5",alpha=0.5)
    axes[0].hist(np.log10(actual.iloc[-1,:].values),fc="b",alpha=0.5)
    axes[0].set_title('log-10 phi w/o noise')

    axes[1].hist(np.log10(meas.iloc[0,:].values),fc="0.5",alpha=0.5)
    axes[1].hist(np.log10(meas.iloc[-1,:].values),fc="b",alpha=0.5)
    axes[1].set_title('log-10 phi w/ noise')
    
    
    fig,axes = plt.subplots(2,1,figsize=(10,20))
    ptoe = ptoe.loc[keep,:]
    nzobs.sort_values(by="obsval",inplace=True)
    ovals = nzobs.obsval.values
    for real in ptoe.index:
        nvals = noise.loc[real,nzobs.obsnme].values   
        prvals = proe.loc[real,nzobs.obsnme].values
        ptvals = ptoe.loc[real,nzobs.obsnme].values
        ax = axes[0]
        #ax.plot(ovals,nvals,"r-",alpha=0.5,lw=0.5)
        ax.scatter(ovals,nvals,marker='.',alpha=0.2,s=70,c='r')
        #ax.plot(ovals,prvals,"0.5",alpha=0.2,lw=0.3,dashes=(1,1))
        #ax.plot(ovals,ptvals,"b",alpha=0.5,lw=0.5)#,marker='.',ms=5)
        ax.scatter(ovals,ptvals,marker='.',s=50,c='b')
        ax = axes[1]
        ax.plot(ovals,nvals,"r-",alpha=0.5,lw=0.5,zorder=0)
        ax.scatter(ovals,nvals,marker='.',alpha=0.2,s=70,c='r')
        #ax.plot(ovals,prvals,"0.5",alpha=0.2,lw=0.3,dashes=(1,1))
        #ax.plot(ovals,ptvals,"b",alpha=0.5,lw=0.5,zorder=0)#,marker='.',ms=5)
        ax.scatter(ovals,ptvals,marker='.',s=50,c='b')
    
    mn,mx = noise.loc[:,names].values.min(),noise.loc[:,names].values.max()
    for ax in axes:
        ax.plot([mn,mx],[mn,mx],"k--",lw=3)
        ax.set_xlabel("observed")
        ax.set_ylabel("simulated")
        ax.set_xlim(mn,mx)
        ax.grid()
    
    _ = ax.set_ylim(mn,mx)
            

def plot_dsi_compare_traindata(realseq=[10,50,100,150,200,250,300]):

    fig=None
    for nreal in realseq:
        md = f"master_dsi_{nreal}"
        dpst = pyemu.Pst(os.path.join(md, "dsi.pst"))

        if fig is None:
            fig,axs = plt.subplots(dpst.ies.phiactual.iteration.nunique()-1,2,figsize=(10,12),
                                   sharex=True,sharey=False)
            
            obs = dpst.observation_data
            obsnmes = obs.loc[obs.obgnme=='rivgroup'].obsnme.tolist()
            

        for e,o in enumerate(obsnmes):
            for iiter in dpst.ies.phiactual.iteration.unique():
                if iiter==0:
                    continue
                ptoe = dpst.ies.get("obsen{0}".format(iiter))


                ax = axs[iiter-1,e]
                ax.set_title(f"iteration:{iiter}")
                #ax.hist(ptoe.loc[:,obsnmes[0]].values.flatten(), bins=20,alpha=0.5, label=f"{nreal} reals",zorder=0)
                ax.scatter(nreal*np.ones(ptoe.loc[:,obsnmes[0]].values.flatten().shape),
                        ptoe.loc[:,obsnmes[0]].values.flatten(),c='0.5', alpha=0.3, label=f"{nreal} reals",zorder=0)
                ax.set_xlabel("Number of Reals")
                ax.set_ylabel(obsnmes[0])
            
                ax.scatter([nreal],ptoe.loc[:,obsnmes[0]].quantile(.5),c='k',marker='o')
                ax.vlines(nreal, ptoe.loc[:,obsnmes[0]].quantile(.05),
                        ptoe.loc[:,obsnmes[0]].quantile(.95), color='k', linestyle='--')



    plt.tight_layout()
    return


if __name__ == "__main__":
    pass