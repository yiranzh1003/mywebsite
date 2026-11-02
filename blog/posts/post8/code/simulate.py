"""Run from any directory: python code/simulate.py. All data are simulated."""
from pathlib import Path
import io, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
for folder in ('data', 'results'):
    (ROOT / folder).mkdir(exist_ok=True)
SHAPE, TRUE_MEAN, NULL_MEAN = 4., 12., 10.
B, M, S = 2000, 2000, 50000
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})

def bootstrap(x, rng, reps):
    return x[rng.integers(0, len(x), size=(reps, len(x)))].mean(axis=1)

def svg(fig, name):
    fig.tight_layout()
    if name.endswith('n200'):
        fig.savefig(ROOT / 'results' / (name + '.png'), dpi=160, bbox_inches='tight')
    out = io.StringIO()
    fig.savefig(out, format='svg', bbox_inches='tight')
    plt.close(fig)
    return out.getvalue()[out.getvalue().index('<svg'):]

panels, summaries = [], []
for n in (30, 100, 200):
    # Separate deterministic random streams prevent changing one experiment from changing another.
    sample_rng, boot_rng, coverage_rng, null_rng = [np.random.default_rng(s) for s in (8100+n, 8200+n, 8300+n, 8400+n)]
    x = sample_rng.gamma(SHAPE, TRUE_MEAN / SHAPE, n)
    np.savetxt(ROOT / 'data' / f'sample_n{n}.csv', x, delimiter=',', header='wait_minutes', comments='')
    boot = bootstrap(x, boot_rng, 5000)
    lo, hi = np.quantile(boot, [.025, .975])
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.hist(boot, bins=45, color='#375e75', alpha=.85)
    ax.axvspan(lo, hi, color='#d9a441', alpha=.2, label='95% percentile interval')
    for v in (lo, hi): ax.axvline(v, color='#a66a13', linestyle='--')
    ax.axvline(x.mean(), color='#202020', label='Sample mean')
    ax.set(xlabel='Bootstrap mean waiting time (minutes)', ylabel='Number of resamples', title=f'n = {n}: mean {x.mean():.2f}; 95% CI [{lo:.2f}, {hi:.2f}]')
    ax.legend(fontsize=9)
    a = svg(fig, f'bootstrap_n{n}')
    intervals = np.empty((M, 2))
    for j in range(M):
        new_sample = coverage_rng.gamma(SHAPE, TRUE_MEAN / SHAPE, n)
        intervals[j] = np.quantile(bootstrap(new_sample, coverage_rng, B), [.025,.975])
    covered = (intervals[:,0] <= TRUE_MEAN) & (TRUE_MEAN <= intervals[:,1])
    coverage = covered.mean()
    mcse = np.sqrt(coverage*(1-coverage)/M)
    np.savetxt(ROOT / 'results' / f'coverage_n{n}.csv', np.column_stack((intervals,covered)), delimiter=',', header='lower,upper,covers_true_mean', comments='')
    fig, ax = plt.subplots(figsize=(8,4))
    for j in range(100):
        ax.plot(intervals[j], [j+1,j+1], color='#375e75' if covered[j] else '#bc493b', linewidth=1.2)
    ax.axvline(TRUE_MEAN, color='black', linestyle='--', label='True mean = 12')
    ax.set(xlabel='95% bootstrap interval (minutes)', ylabel='Repeated sample (first 100)', title=f'n = {n}: coverage {coverage:.1%} across {M:,} fresh samples')
    ax.legend(fontsize=9)
    b = svg(fig, f'coverage_n{n}')
    # H0 model assumes known Gamma shape 4; scale is 10/4. Mean is the test statistic.
    # Under independence, sums of Gamma(shape=4,scale=2.5) variables are Gamma(4*n,2.5).
    # Draw actual null samples in batches for a transparent simulation, not a normal approximation.
    null_means = np.concatenate([null_rng.gamma(SHAPE, NULL_MEAN/SHAPE, (1000,n)).mean(axis=1) for _ in range(S//1000)])
    critical = np.quantile(null_means, .95)
    extreme = int((null_means >= x.mean()).sum())
    pvalue = (extreme+1)/(S+1)
    np.savetxt(ROOT/'results'/f'null_means_n{n}.csv', null_means, delimiter=',', header='null_sample_mean',comments='')
    fig, ax = plt.subplots(figsize=(8,3.6))
    counts, edges, patches = ax.hist(null_means,bins=65,color='#375e75',alpha=.85)
    for left,patch in zip(edges[:-1],patches):
        if left >= critical: patch.set_facecolor('#bc493b')
    ax.axvline(critical,color='#bc493b',linestyle='--',label=f'5% rejection threshold: {critical:.2f}')
    ax.axvline(x.mean(),color='black',label=f'Observed mean: {x.mean():.2f}')
    ax.set_xlim(min(null_means.min(), x.mean())-.15, max(null_means.max(), x.mean())+.3)
    ax.set(xlabel='Sample mean under H0: mean = 10 (minutes)',ylabel='Number of null simulations',title=f'n = {n}: upper-tail exceedances = {extreme}/{S:,}')
    ax.legend(fontsize=9)
    c = svg(fig,f'null_n{n}')
    row=dict(n=n,sample_mean=float(x.mean()),ci_lower=float(lo),ci_upper=float(hi),coverage=float(coverage),coverage_mcse=float(mcse),null_critical=float(critical),null_extreme=extreme,pvalue=float(pvalue),mean_interval_width=float(np.diff(intervals,axis=1).mean()))
    summaries.append(row)
    panels.append(f'<section class="panel" data-n="{n}" {"hidden" if n!=200 else ""}><h3>1. Resample one observed sample</h3>{a}<h3>2. Repeat the entire experiment</h3>{b}<p>Coverage: {coverage:.2%}; Monte Carlo standard error: {mcse:.2%}. Blue intervals cover 12; red intervals miss it. The plot shows the first 100 intervals without selection.</p><h3>3. Simulate the null hypothesis</h3>{c}<p>The red tail is the 5% rejection region. The p-value uses all simulated means at least as large as the black line: ({extreme} + 1)/({S} + 1) = {pvalue:.6f}. This is a finite-simulation estimate, not an exact probability.</p></section>')
(ROOT/'results'/'summary.json').write_text(json.dumps(summaries,indent=2))
style='.quarto-categories{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}.quarto-categories span{font:12px Arial,sans-serif;text-transform:uppercase;border:1px solid #bbb;padding:4px 8px;border-radius:3px}.title-meta{display:flex;gap:80px;font:15px/1.6 Arial,sans-serif;margin:24px 0}.title-meta small{font-size:11px;color:#666}.hero{margin:25px 0}.hero img{width:100%;height:auto}.hero figcaption{font-size:13px;color:#666}body{max-width:920px;margin:35px auto;padding:0 22px;font:17px/1.65 Georgia,serif;color:#202c34}h1,h2,h3,label,select{font-family:Arial,sans-serif}h1{line-height:1.2}h2{margin-top:2em}svg{width:100%;height:auto}select{padding:7px;font-size:16px}.note{border-left:3px solid #a66a13;padding-left:16px} .panel[hidden]{display:none} table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}'
explore_intro = f'''<p>The article uses n = 200 customers. Switch between n = 30, 100, and 200 to compare sample sizes under the same population model. For n = 30, 100, and 200, average interval widths are {summaries[0]['mean_interval_width']:.2f}, {summaries[1]['mean_interval_width']:.2f}, and {summaries[2]['mean_interval_width']:.2f} minutes: larger samples estimate the mean more precisely. Compare coverage with the 95% target too; narrower intervals do not automatically guarantee correct coverage. Each setting draws a different sample, so changes in its mean and p-value reflect both sample size and the observations drawn.</p>'''
widget=explore_intro+'<label for="sample-size">Explore sample size: </label><select id="sample-size"><option>30</option><option>100</option><option selected>200</option></select><p>Each option uses a separately generated, fixed-seed experiment. Compare interval width and coverage; these are precomputed results, not live simulations.</p>'+''.join(panels)+'<script>document.getElementById("sample-size").addEventListener("change",function(){document.querySelectorAll(".panel").forEach(p=>p.hidden=p.dataset.n!==this.value)});</script>'
(ROOT/'results'/'interactive.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Waiting time simulation explorer</title><style>'+style+'</style><body><h1>Waiting time simulation explorer</h1>'+widget+'</body></html>')
r=next(row for row in summaries if row['n']==200)
article=f'''<h1>Is the Average Wait Longer Than 10 Minutes?</h1>
<div class="quarto-categories"><span>Simulation</span> <span>Bootstrap</span> <span>Confidence Intervals</span> <span>Hypothesis Testing</span></div>
<div class="title-meta"><div><small>AUTHOR</small><br>Yiran Zhang</div><div><small>PUBLISHED</small><br>November 1, 2026</div></div>
<figure class="hero"><img src="assets/cafe.jpg" alt="Illustrative coffee shop with customers waiting near the pickup counter"><figcaption>A coffee-shop setting for exploring waiting times. AI-generated illustrative image.</figcaption></figure>
<p>A coffee shop claims that orders take ten minutes on average. A few long waits do not automatically disprove that claim: samples fluctuate. How can we distinguish a real difference from sampling noise? For a customer planning a short break, an extra two minutes matters. Simulation lets us check whether a sample can reveal that difference, because we know the truth behind the data.</p>
<p>I generate independent waiting times from a Gamma distribution with shape 4 and scale 3 minutes. Its population mean is shape times scale: 12 minutes. These are synthetic data, not observations from a real shop.</p>
<p>Why Gamma? Waiting times are positive, and a right-skewed distribution captures a useful pattern: most customers receive their orders relatively quickly, while a few wait much longer. Gamma also has a simple, known mean, making it convenient for checking inference. This is a teaching model, not evidence that actual coffee-shop waits follow this distribution.</p>
<h2>What can one sample tell us?</h2>
<p>The main experiment draws 200 customers. Their average wait is {r['sample_mean']:.2f} minutes. To estimate its uncertainty, I draw 5,000 bootstrap samples from those same 200 observations, with replacement. Each resample contains 200 records; some original records appear several times and others disappear. I calculate a mean for every resample.</p>
<p>The first plot displays those bootstrap means. Their 2.5th and 97.5th percentiles give a 95% percentile bootstrap interval of [{r['ci_lower']:.2f}, {r['ci_upper']:.2f}] minutes. The sample stands in for the population: resampling estimates how much its mean could vary. It adds no new independent information and does not assume a Gamma distribution.</p>
<figure><img src="results/bootstrap_n200.png" style="width:100%;height:auto" alt="Distribution of 5000 bootstrap means with 95 percent confidence interval"><figcaption>Figure 1. Resampling one sample estimates uncertainty about its mean.</figcaption></figure>
<p>But does this interval-building method usually capture the truth? To check its coverage, I repeat the entire experiment 2,000 times. Each repetition draws a fresh sample from the population, performs 2,000 bootstrap resamples, and constructs a new interval. The resulting coverage is {r['coverage']:.1%}: approximately 95% of intervals contain the fixed true mean of 12.</p>
<p>The second plot displays the first 100 intervals, including misses. The parameter stays fixed while intervals change. The confidence level describes the long-run performance of the procedure, not a 95% probability assigned to the fixed parameter after observing one interval. Percentile bootstrap coverage is approximate, especially with small, skewed samples; neither nominal confidence nor more bootstrap draws guarantees correct coverage.</p>
<figure><img src="results/coverage_n200.png" style="width:100%;height:auto" alt="First 100 bootstrap confidence intervals with misses highlighted"><figcaption>Figure 2. Repeating the whole experiment reveals coverage; red intervals miss the true mean.</figcaption></figure>
<h2>What if the shop's claim were true?</h2>
<p>For a separate, one-sided test, I set H0: mean = 10 against H1: mean &gt; 10. The original sample comes from Gamma(4, 3), with mean twelve; ten is the shop's claim, not a consequence of skewness. To simulate a world consistent with the shop's claim, I keep shape 4 and set scale to 10/4 = 2.5: Gamma(4, 2.5) therefore has mean ten. Holding shape fixed preserves skewness and relative variability, but the standard deviation falls from six to five minutes. The test therefore assumes a specific Gamma family with known shape. Bootstrap resampling itself makes neither Gamma assumption.</p>
<p>I generate 50,000 samples of 200 customers under that null model and use their means as test statistics. The upper 5% forms the rejection region, starting at {r['null_critical']:.2f} minutes. The observed mean exceeds this threshold. The p-value estimates the probability, assuming H0 and this model, of a mean at least as large as observed. There are {r['null_extreme']} exceedances; the finite-simulation correction gives ({r['null_extreme']} + 1)/(50,000 + 1) = {r['pvalue']:.6f}. Zero simulated exceedances would not mean zero true probability. At the 5% level, I reject H0: this sample provides evidence of an average wait above ten minutes under the specified model.</p>
<figure><img src="results/null_n200.png" style="width:100%;height:auto" alt="Simulated null distribution with upper rejection region and observed mean"><figcaption>Figure 3. The observed mean lies beyond the upper 5% rejection threshold.</figcaption></figure>
<p>This one-sided 5% test and the two-sided 95% bootstrap interval are distinct procedures, not exact inverses.</p>
<p>In this simulated shop, the sample supports an average wait above ten minutes. The bootstrap interval shows its uncertainty, and repeated experiments show why a 95% method can still miss the truth. The conclusion concerns average waiting time, not every customer's wait. Real queues may have dependent observations and changing conditions, so ordinary independent resampling would need reconsideration.</p>
<p><small>All data are simulated. Code, generated data and replication instructions are provided in the accompanying repository.</small></p>'''
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Is the Average Wait Longer Than 10 Minutes?</title><style>'+style+'</style><body>'+article+'<h2>Explore the simulations</h2>'+widget+'</body></html>'
(ROOT/'index.html').write_text(html)
# Raw HTML works in Quarto without executing Python. The explorer is self-contained in its iframe.
qmd='''---
title: "Is the Average Wait Longer Than 10 Minutes?"
author: "Yiran Zhang"
date: "2026-11-01"
categories: [Simulation, Bootstrap, Confidence Intervals, Hypothesis Testing]
image: assets/cafe.jpg
resources:
  - assets/cafe.jpg
  - results/interactive.html
  - results/bootstrap_n200.png
  - results/coverage_n200.png
  - results/null_n200.png
format:
  html:
    toc: false
execute:
  enabled: false
---

'''
# Avoid duplicating the title generated by Quarto.
body=article[article.index('<figure class="hero">'):]
qmd+='```{=html}\n<style>.hero {{margin:1.5rem 0}} .hero img {{width:100%;height:auto}} .hero figcaption {{font-size:.85rem;color:#666;margin-top:.4rem}}</style>\n'.replace('{{','{').replace('}}','}')+body+'\n<h2>Explore the simulations</h2>\n<iframe src="results/interactive.html" title="Interactive bootstrap and hypothesis testing demonstrations" style="width:100%;height:1650px;border:0" loading="lazy"></iframe>\n```\n'
(ROOT/'index.qmd').write_text(qmd)
print(json.dumps(summaries,indent=2))
print('Article words:',len(__import__('re').sub('<[^>]+>',' ',article).split()))
