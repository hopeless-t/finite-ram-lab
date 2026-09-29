"""Retrospective model ladder for the canonical rare specimen census.

No physical experiment is run. Requires numpy, scipy, pandas, statsmodels.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.optimize import minimize
from scipy.special import expit, logsumexp
from scipy.stats import beta, binom, fisher_exact
from statsmodels.stats.contingency_tables import StratifiedTable


def matrix(d: pd.DataFrame, kind: str) -> np.ndarray:
    e = (d.experiment == "G0").to_numpy(dtype=float)
    step = (d.capacity_pages >= 10).to_numpy(dtype=float)
    cols = [np.ones(len(d))]
    if kind != "constant":
        cols += [step]
    if kind in ("interaction", "hierarchical", "mixture"):
        cols += [e, e * step]
    if kind == "interaction":
        cols += [(d.pre_current_pages.to_numpy(float) - 99) / 4,
                 ((d.experiment == "G0") & d.arm.isin(["P8", "P9"])).to_numpy(dtype=float)]
    return np.column_stack(cols)


def glm_fit(x: np.ndarray, y: np.ndarray):
    return sm.GLM(y, x, family=sm.families.Binomial()).fit(maxiter=200, disp=0)


def block_model(x: np.ndarray, y: np.ndarray, blocks: np.ndarray, kind: str):
    codes = pd.factorize(blocks)[0]
    nb = codes.max() + 1
    base = glm_fit(x, y).params
    if kind == "hierarchical":
        nodes, weights = np.polynomial.hermite.hermgauss(15)
        nodes, logw = nodes * np.sqrt(2), np.log(weights / np.sqrt(np.pi))

        def objective(theta):
            z = x @ theta[:-1]
            eta = z[:, None] + np.exp(theta[-1]) * nodes[None, :]
            per = y[:, None] * eta - np.logaddexp(0, eta)
            sums = np.zeros((nb, len(nodes)))
            np.add.at(sums, codes, per)
            return -np.sum(logsumexp(sums + logw, axis=1))

        fit = minimize(objective, np.r_[base, -2.0], method="L-BFGS-B",
                       bounds=[(None, None)] * len(base) + [(-7, 3)])
        theta = fit.x
        pred = lambda xx: np.sum(expit(xx @ theta[:-1, None] + np.exp(theta[-1]) * nodes) * np.exp(logw), axis=1)
        extra = {"sigma_block": float(np.exp(theta[-1]))}
    else:
        def objective(theta):
            z = x @ theta[:-2]
            shift = np.exp(theta[-2])
            mix = expit(theta[-1])
            p0, p1 = expit(z), expit(z + shift)
            sums = np.zeros((nb, 2))
            np.add.at(sums, codes, np.column_stack([y*np.log(p0)+(1-y)*np.log1p(-p0),
                                                     y*np.log(p1)+(1-y)*np.log1p(-p1)]))
            return -np.sum(logsumexp(sums + np.log([1-mix, mix]), axis=1))

        fit = minimize(objective, np.r_[base, 0.0, -1.0], method="L-BFGS-B",
                       bounds=[(None, None)] * len(base) + [(-5, 5), (-7, 7)])
        theta = fit.x
        pred = lambda xx: ((1-expit(theta[-1]))*expit(xx @ theta[:-2]) +
                            expit(theta[-1])*expit(xx @ theta[:-2] + np.exp(theta[-2])))
        extra = {"rich_block_weight": float(expit(theta[-1])), "rich_log_odds_shift": float(np.exp(theta[-2]))}
    if not fit.success:
        extra["optimizer_warning"] = str(fit.message)
    return theta, -fit.fun, pred, extra


def logscore(y, p):
    p = np.clip(p, 1e-9, 1-1e-9)
    return float(np.sum(y*np.log(p)+(1-y)*np.log1p(-p)))


def analyze(path: Path) -> dict:
    all_rows = pd.read_csv(path)
    d = all_rows[(all_rows.experiment.isin(["GF", "G0"])) &
                 (all_rows.stratum == "LOW") & (all_rows.valid == True)].copy()
    d["block_key"] = d.experiment + ":" + d.block.astype(str)
    y = d.exact_zero.to_numpy(dtype=float)
    out = {"n_natural_low": len(d), "events": int(y.sum()), "models": {}, "checks": {}}

    # 1. Raw incidence, including the explicitly controlled G0 width comparison.
    for experiment in ("GF", "G0"):
        sub = d[d.experiment == experiment]
        out["checks"][experiment.lower()+"_arm_incidence"] = {
            str(k): {"events": int(v.exact_zero.sum()), "trials": len(v)} for k,v in sub.groupby("arm")}
    for exp in ("GF", "G0"):
        sub = d[d.experiment == exp]
        lo, hi = sub[sub.capacity_pages < 10], sub[sub.capacity_pages >= 10]
        table = [[int(hi.exact_zero.sum()), len(hi)-int(hi.exact_zero.sum())],
                 [int(lo.exact_zero.sum()), len(lo)-int(lo.exact_zero.sum())]]
        out["checks"][exp.lower()+"_step_fisher"] = {"table": table, "or": float(fisher_exact(table)[0]),
                                                        "p": float(fisher_exact(table)[1])}
        # Resample whole blocks, preserving within-block arm and admission structure.
        blocks = []
        for _, b in sub.groupby("block"):
            low, high = b[b.capacity_pages < 10], b[b.capacity_pages >= 10]
            blocks.append([low.exact_zero.sum(),len(low),high.exact_zero.sum(),len(high)])
        blocks = np.asarray(blocks,dtype=float)
        rng_boot = np.random.default_rng(14014 + len(blocks))
        sampled = blocks[rng_boot.integers(0,len(blocks),(10000,len(blocks)))].sum(axis=1)
        boot = sampled[:,2]/sampled[:,3]-sampled[:,0]/sampled[:,1]
        out["checks"][exp.lower()+"_step_fisher"]["block_bootstrap_rd_ci95"] = [float(v) for v in np.quantile(boot,[.025,.975])]

    # 2. Block-conditioned common odds and block-label-preserving permutation.
    tables = []
    for _, b in d.groupby("block_key"):
        lo, hi = b[b.capacity_pages < 10], b[b.capacity_pages >= 10]
        tables.append(np.array([[int(hi.exact_zero.sum()), len(hi)-int(hi.exact_zero.sum())],
                                [int(lo.exact_zero.sum()), len(lo)-int(lo.exact_zero.sum())]]))
    cmh = StratifiedTable(tables)
    out["checks"]["block_conditioned"] = {"cmh_or": float(cmh.oddsratio_pooled),
                                            "cmh_p": float(cmh.test_null_odds().pvalue)}
    rng = np.random.default_rng(14014)
    block_groups = [(b.exact_zero.to_numpy(dtype=int), (b.capacity_pages>=10).to_numpy(dtype=bool))
                    for _,b in d.groupby("block_key")]
    observed = sum((yy[hi].mean()-yy[~hi].mean()) for yy,hi in block_groups)
    draws = np.empty(20000)
    for j in range(len(draws)):
        draws[j] = sum((lambda yp: yp[hi].mean()-yp[~hi].mean())(rng.permutation(yy)) for yy,hi in block_groups)
    out["checks"]["block_conditioned"]["permutation_p_two_sided"] = float((1+np.sum(np.abs(draws)>=abs(observed)))/(len(draws)+1))

    # 3-5. Pre-specified complexity ladder, with block-held-out log scores.
    keys = sorted(d.block_key.unique())
    fold_map = {k: i % 5 for i,k in enumerate(rng.permutation(keys))}
    folds = d.block_key.map(fold_map).to_numpy()
    for kind in ("constant", "step", "interaction", "hierarchical", "mixture"):
        x = matrix(d, kind)
        if kind in ("hierarchical", "mixture"):
            theta, ll, pred, extra = block_model(x, y, d.block_key.to_numpy(), kind)
            k = len(theta)
        else:
            fit = glm_fit(x, y)
            theta, ll, pred, extra = fit.params, fit.llf, fit.predict, {}
            k = len(theta)
        cv_ll = 0.0
        for f in range(5):
            tr, te = folds != f, folds == f
            if kind in ("hierarchical", "mixture"):
                _, _, cvpred, _ = block_model(x[tr], y[tr], d.block_key.to_numpy()[tr], kind)
            else:
                cvpred = glm_fit(x[tr], y[tr]).predict
            cv_ll += logscore(y[te], cvpred(x[te]))
        out["models"][kind] = {"parameters": [float(v) for v in theta], "log_likelihood": float(ll),
                               "aic": float(2*k-2*ll), "bic": float(k*np.log(len(d))-2*ll),
                               "block_heldout_log_loss_per_trial": float(-cv_ll/len(d)), **extra}

    # PTE and pre-current checks are within their measurement regimes.
    g0 = d[d.experiment == "G0"]
    gf = d[d.experiment == "GF"]
    cap9, cap10 = gf[gf.capacity_pages==9], gf[gf.capacity_pages==10]
    out["checks"]["gf_9_to_10"] = {"counts":[[int(cap9.exact_zero.sum()),len(cap9)],
                                                [int(cap10.exact_zero.sum()),len(cap10)]],
                                      "fisher_p":float(fisher_exact([[int(cap9.exact_zero.sum()),len(cap9)-int(cap9.exact_zero.sum())],
                                                                      [int(cap10.exact_zero.sum()),len(cap10)-int(cap10.exact_zero.sum())]])[1])}
    padded, high = g0[g0.arm.isin(["P8","P9"])], g0[g0.arm.isin(["H10","H32"])]
    out["checks"]["g0_width_controlled"] = {"counts":[[int(padded.exact_zero.sum()),len(padded)],
                                                         [int(high.exact_zero.sum()),len(high)]],
                                               "fisher_p":float(fisher_exact([[int(padded.exact_zero.sum()),len(padded)-int(padded.exact_zero.sum())],
                                                                               [int(high.exact_zero.sum()),len(high)-int(high.exact_zero.sum())]])[1])}
    pte = g0[g0.PTE_growth == True]
    no_pte = g0[g0.PTE_growth == False]
    table = [[int(pte.exact_zero.sum()), len(pte)-int(pte.exact_zero.sum())],
             [int(no_pte.exact_zero.sum()), len(no_pte)-int(no_pte.exact_zero.sum())]]
    out["checks"]["g0_pte"] = {"table": table, "fisher_p": float(fisher_exact(table)[1]),
                                "posterior_p_pte_lt_no_pte": float(np.mean(rng.beta(1+table[0][0],1+table[0][1],200000) <
                                                                 rng.beta(1+table[1][0],1+table[1][1],200000)))}
    core = g0[g0.pre_current_pages.isin([97,98,99,100])]
    out["checks"]["g0_core"] = {"trials": len(core), "events": int(core.exact_zero.sum()),
                                 "by_step": {str(k): [int(v.exact_zero.sum()),len(v)] for k,v in core.groupby(core.capacity_pages>=10)}}
    gf_core = gf[gf.pre_current_pages.isin([97,98,99,100])]
    for name, sub in (("gf",gf),("gf_core",gf_core),("g0",g0),("g0_core",core)):
        xx=np.column_stack([np.ones(len(sub)),(sub.capacity_pages>=10).to_numpy(dtype=float),
                            (sub.pre_current_pages.to_numpy(dtype=float)-99)/4])
        fit=glm_fit(xx,sub.exact_zero.to_numpy(dtype=float))
        out["checks"][name+"_precurrent_adjusted"]={"beta_per_4_pages":float(fit.params[-1]),
                                                     "wald_p":float(fit.pvalues[-1]),
                                                     "or_ci95":[float(v) for v in np.exp(fit.conf_int()[-1])],
                                                     "range":[float(sub.pre_current_pages.min()),float(sub.pre_current_pages.max())]}
    block_dummies=pd.get_dummies(gf_core.block.astype(str),drop_first=True).to_numpy(dtype=float)
    xx=np.column_stack([np.ones(len(gf_core)),(gf_core.capacity_pages>=10).to_numpy(dtype=float),
                        gf_core.pre_current_pages.to_numpy(dtype=float)-99,block_dummies])
    fit=glm_fit(xx,gf_core.exact_zero.to_numpy(dtype=float))
    out["checks"]["gf_core_block_fixed_precurrent"]={"or_per_page":float(np.exp(fit.params[2])),
                                                       "p":float(fit.pvalues[2]),
                                                       "or_ci95":[float(v) for v in np.exp(fit.conf_int()[2])]}

    # Depth mixture and conditional controlled-spawn pattern checks.
    ga = all_rows[(all_rows.experiment == "GA") & (all_rows.stratum == "LOW") & (all_rows.exact_zero == True)]
    g0z = g0[g0.exact_zero == True]
    spawn = all_rows[all_rows.experiment == "SPAWN"]
    out["checks"]["depth"] = {"ga_depth1": int((ga.depth_to_next_q64==1).sum()), "ga_total":len(ga),
                               "g0_depth1":int((g0z.depth_to_next_q64==1).sum()), "g0_total":len(g0z),
                               "ga_vs_g0_fisher_p":float(fisher_exact([[22,6],[12,7]])[1])}
    depths=ga.depth_to_next_q64.to_numpy(dtype=int)
    n1=int(np.sum(depths==1)); deep=depths[depths>1]
    p_geo=1/np.mean(depths)
    ll_geo=len(depths)*np.log(p_geo)+np.sum(depths-1)*np.log1p(-p_geo)
    q=n1/len(depths); p_tail=1/np.mean(deep-1)
    ll_mix=n1*np.log(q)+len(deep)*np.log1p(-q)+len(deep)*np.log(p_tail)+np.sum(deep-2)*np.log1p(-p_tail)
    out["checks"]["depth_model"]={"geometric_p":float(p_geo),"geometric_aic":float(2-2*ll_geo),
                                    "geometric_bic":float(np.log(len(depths))-2*ll_geo),
                                    "spike_weight":float(q),"deep_shifted_geometric_p":float(p_tail),
                                    "spike_tail_aic":float(4-2*ll_mix),
                                    "spike_tail_bic":float(2*np.log(len(depths))-2*ll_mix),
                                    "geometric_ppc_p_ge_22_depth1":float(binom.sf(n1-1,len(depths),p_geo)),
                                    "spike_weight_beta95":[float(v) for v in beta.ppf([.025,.975],1+n1,1+len(deep))]}
    qualified = spawn[spawn.primer_qualified == True]
    out["checks"]["spawn"] = {"strict_success":int(spawn.strict_exact_recovery.sum()), "all":len(spawn),
                               "qualified":len(qualified), "conditional_pattern_match":int(qualified.terminal_pattern_match.sum()),
                               "negative_sequence_events":int(spawn.negative_accounting_delta.sum()),
                               "conditional_95pct_lower":float(beta.ppf(.05,1+qualified.terminal_pattern_match.sum(),1+len(qualified)-qualified.terminal_pattern_match.sum()))}

    # Monte Carlo posterior predictive check for natural block event counts under M3.
    fit = glm_fit(matrix(d, "interaction"), y)
    p = fit.predict(matrix(d, "interaction"))
    bcodes = pd.factorize(d.block_key)[0]
    observed_var = float(np.var(np.bincount(bcodes,weights=y)))
    sim_var = np.empty(10000)
    for i in range(len(sim_var)):
        sim_var[i] = np.var(np.bincount(bcodes,weights=rng.binomial(1,p)))
    out["checks"]["ppc_block_count_variance"] = {"observed":observed_var,
                                                      "sim_median":float(np.median(sim_var)),
                                                      "two_sided_tail":float(2*min(np.mean(sim_var<=observed_var),np.mean(sim_var>=observed_var)))}
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("analysis/inputs/RARE-SPECIMEN-CENSUS-v1.csv"))
    p.add_argument("--output",type=Path,default=Path("analysis/inputs/RARE-STATE-MODEL-COMPARISON-v1.json"))
    a=p.parse_args()
    result=analyze(a.input)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"models":result["models"],"checks":result["checks"]},indent=2))


if __name__=="__main__":
    main()
