# Blog 8: Is the Average Wait Longer Than 10 Minutes?

A reproducible simulation tutorial on bootstrap intervals, coverage, and one-sided hypothesis testing. All observations are synthetic. No download, API key, or external data is required.

## Read or publish

- Open `index.html` in a browser for the complete standalone article and sample-size explorer. It works offline; no JavaScript libraries or external fonts are required.
- For an existing Quarto blog, copy the entire `blog8` folder into `blog/posts/`, retaining the `results` subfolder. Render with `quarto render blog/posts/blog8/index.qmd` from the website root. The source article embeds `results/interactive.html` via a relative iframe.
- The standalone `index.html` is a review copy. Quarto will replace it with the rendered website version. Include the complete folder in the website build so that the embedded explorer remains available.
- The publication and GitHub submission URLs must be taken from your own site and repository after publishing; none have been invented here.

## Reproduce in Python

From this folder, with Python 3.11 or newer:

```bash
python -m pip install -r requirements.txt
python code/simulate.py
```

On Windows, use `py` instead of `python` if needed. The script locates this folder from its own path and can also be run from another working directory. It overwrites only its generated outputs and article files. The article text is generated from the results, so reported numbers stay consistent with the simulation.

To render the Quarto source after reproduction, use the existing website's Quarto installation. Python reproduction does not require R or Quarto. The separate standalone HTML can be opened without rendering.

## Folder structure

- `code/simulate.py`: complete simulation, figure generation, interactive HTML, and article generation.
- `data/sample_n*.csv`: original simulated customer samples, one record per customer.
- `results/coverage_n*.csv`: all 2,000 confidence intervals per sample size and coverage indicators.
- `results/null_means_n*.csv`: all 50,000 simulated null sample means per sample size.
- `results/summary.json`: programmatically generated numerical results.
- `results/*n200.png`: three main article figures. The explorer embeds all nine figures directly, without separate SVG files.
- `results/interactive.html`: offline explorer with three sample sizes.
- `index.qmd`: source for an existing Quarto website.
- `index.html`: standalone article for review.

## Statistical design

Population: independent Gamma(shape=4, scale=3 minutes), mean=12, standard deviation=6. This is a pedagogical assumption, not a fitted queueing model. Sample sizes: 30, 100, 200; the article uses 200 as its main example. Gamma parameters use the **shape-scale**, not shape-rate, convention.

Bootstrap illustration: 5,000 nonparametric resamples of size n from one observed sample. Interval endpoints: NumPy's default linear 2.5% and 97.5% quantiles. Coverage: 2,000 fresh independent population samples, each with 2,000 bootstrap resamples. Coverage MCSE = sqrt(coverage*(1-coverage)/2000). Coverage is measured honestly; no random seed is selected to force it to 95%.

Null test: H0 mean=10; H1 mean>10. The null model assumes Gamma(shape=4, scale=2.5), so the shape is treated as known. Simulate 50,000 independent null samples of size n. The statistic is the sample mean; the estimated rejection cutoff is the 95th percentile of simulated null means. Upper-tail p = (1 + number of simulated null statistics >= observed statistic)/(50000 + 1). This finite Monte Carlo estimate has limited tail resolution, and is not an exact analytical p-value. Reject at 5% if the p-value is <= .05. For the composite interpretation H0 mean<=10 within this fixed-shape family, the boundary mean=10 determines the upper-tail cutoff.

The two-sided percentile bootstrap interval and one-sided parametric test are separate procedures and need not produce equivalent decisions. Ordinary bootstrap assumes independent, identically distributed observations here. Actual queues can violate independence; results are not evidence about any real shop.

Random streams for each n: sample 8100+n, bootstrap 8200+n, coverage 8300+n, null 8400+n. Generator: NumPy default_rng (PCG64 in the recorded environment). Interactive controls switch between deterministic precomputed experiments; they do not rerun simulations or hold the observed sample constant. The first 100 coverage intervals are displayed without selecting successes or failures.

## Environment

Validated using Python with NumPy 2.3.5 and Matplotlib (version recorded in requirements.txt). Exact package versions are pinned for replication. Different versions may cause small output differences.

## Header image

`assets/cafe.jpg` is an AI-generated illustrative cafe scene, not a real venue or data source. It is included locally for offline viewing and website publication. Categories, author, and date use standard Quarto front matter and inherit the existing website theme.
