# Does Lower Rent Mean Affordable Housing?

This project compares median gross rent with rent burden across Philadelphia census tracts. The published article is `index.qmd`. The fully executed workflow uses Python; an alternative R implementation is provided for use in RStudio.

## Files and locations

| File or folder | Purpose |
|---|---|
| `index.qmd` | Website-ready Quarto article, with no visible analysis code |
| `article.md` | Same article as readable Markdown |
| `preview.html` | Standalone preview with embedded figures; open in a browser |
| `article_template.md` | Article source; selected numeric results are substituted by Python |
| `code/analyze.py` | Complete download/cache, cleaning, joining, calculation, figures, and article generation |
| `code/build_preview.py` | Rebuilds the standalone HTML preview after updating the analysis |
| `code/analyze.R` | Alternative R calculation, checks against the shipped results, and separate R figures |
| `data/raw/acs2024_5yr.json` | Unmodified ACS estimates, margins of error, geography, and release metadata |
| `data/raw/tracts_tiger2024.geojson` | Unmodified tract polygons and geographic identifiers |
| `data/processed/tract_statistics.csv` | All 408 tracts, indicators, counts, and eligibility flag |
| `results/group_summary.csv` | Household-weighted burden rates in the two tract groups |
| `results/quartile_burden.csv` | Household-weighted burden composition in four tract rent groups |
| `results/summary.json` | Main results, selected examples, and sensitivity checks |
| `results/figures/` | Programmatically generated PNGs embedded in the article |
| `requirements.txt` | Python package versions used for validation |

## Reproduce in Python 

Python 3.12 was used. From this folder (not its parent), run:

```bash
python -m pip install -r requirements.txt
python code/analyze.py
python code/build_preview.py
```

The supplied raw data are used by default, so analysis does not need an API key or internet access. To download the source data again:

```bash
python code/analyze.py --refresh
```

Refreshing requires internet access to `api.censusreporter.org`; the script checks JSON syntax before replacing the cache. The source release is fixed to `acs2024_5yr`, so refreshing does not silently switch years. No Census API key is needed for this route. Source retrieval date: October 19, 2026 (New York).

Expected results: 408 raw tracts; 376 eligible; 188 tracts per rent group; split at $1,370.50; burden rates 55.0590% in the lower-rent half and 49.1812% in the higher-rent half. The script checks unique identifiers, full boundary matches, release identity, percentage bounds, and successful article substitutions. It saves tables, figures and article text automatically. The two example figures are rounded to one decimal place in the article. The group threshold is rounded to $1,370 in the text using Python's standard rounding; use the exact split in all calculations.

## Data sources and variable definitions

Original producer: U.S. Census Bureau, ACS 2020–2024 five-year estimates. Delivery and boundary service: Census Reporter. These are estimates over five years, not October 2026 asking rents. B25064 is expressed in 2024 inflation-adjusted dollars.

- [B25064: Median gross rent](https://data.census.gov/table/ACSDT5Y2024.B25064), universe: renter-occupied housing units paying cash rent.
- [B25070: Gross rent as a percentage of household income](https://data.census.gov/table/ACSDT5Y2024.B25070), universe: renter-occupied housing units.
- [ACS definitions](https://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/2024_ACSSubjectDefinitions.pdf).
- [Census Reporter API](https://github.com/censusreporter/census-api).

Exact cached requests (percent-encoding `%7C` represents `|`):

```
https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B25064,B25070&geo_ids=140%7C05000US42101
https://api.censusreporter.org/1.0/geo/show/tiger2024?geo_ids=140%7C05000US42101
```

`42101` is Philadelphia County, Pennsylvania; `140` requests census tracts. Join by the full string `geoid`, never tract names or row order. Boundary attributes include an old population estimate; that attribute is NOT used. Only geometry and GEOID are used.

Census Reporter omits the underscore and final estimate suffix from Census variable names:

| Reporter field | Census field | Meaning |
|---|---|---|
| B25064001 | B25064_001E | Median monthly gross rent |
| B25070001 | B25070_001E | Total renter-occupied units |
| B25070007 through B25070010 | B25070_007E through _010E | Income shares 30–34.9%, 35–39.9%, 40–49.9%, and 50%+ |
| B25070011 | B25070_011E | Rent-to-income ratio not computed |

Burden count = sum of categories 007–010. Eligible denominator = category 001 minus category 011. Burden rate = 100 × burden count / denominator. The threshold is **at least 30%**, not strictly greater than 30%. This is a ratio of estimated household counts, not a ratio of two medians. No additional microdata sampling weights are applied: ACS published counts are already weighted estimates.

Missing/nonpositive median rents and absent burden measures are excluded from the common map sample. Also exclude tracts with fewer than 100 estimated households in the computed-ratio denominator. All 408 records remain in the processed CSV. The 100-household threshold is an analyst display rule, not a respondent sample-size or statistical reliability threshold. Do not interpret gray areas as zero hardship. This same common sample is used for both maps, the scatterplot and the group comparison.

The median across eligible tract rents splits the 376 tracts into two groups. Within each group sum burdened households and computed-ratio households separately, then divide; do not average tract percentages. The scatterplot instead gives one dot to each tract, so visually it is not household-weighted. The Pearson correlation is a descriptive, unweighted tract correlation and is not a causal estimate.

## Maps and interpretation

Fixed, human-readable breaks make the legends interpretable in dollars and percentages. The two metrics deliberately use different sequential palettes and units. Python maps preserve geographic proportions around latitude 40 degrees with an aspect correction; they are descriptive displays, not a basis for distance/area calculations. Point markers locate Penn and City Hall for orientation, not neighborhood boundaries. Two maps form the main evidence; the horizontal stacked bars separate burden severity within four tract rent groups, and the scatterplot shows variation within rent levels. Tracts 36 and 8.06 are illustrative cases, not statistically ranked extremes.

Do not infer household-level effects or causality from these aggregate patterns. The dataset does not identify the separate roles of income, housing size, subsidies, student populations or household composition. Ratios not computed can include no/negative household income and no-cash-rent units. Published margins of error are retained in raw JSON, but no hypothesis test or propagated confidence interval is performed; the article does not claim statistical significance. Alternative count cutoffs (0, 50, 100, 200) are saved in `summary.json`; they preserve the direction of the group comparison, but do not resolve sampling error or selection issues.

## Render and add to the existing Quarto website

With Quarto installed:

```bash
quarto render index.qmd --to html
```

For the existing site, copy this folder's contents into `blog/posts/post5/` (keep the relative `results/figures/` structure). From the website root:

```bash
quarto render blog/posts/post5/index.qmd
```

Then inspect the page and the blog listing before committing. The front matter includes a date so it can sort with previous posts. Commit the article, README, scripts, raw and processed data, figures and results. Do not commit a virtual environment, `.Rhistory`, secrets, or unrelated site changes. Follow the existing site's convention for rendered files. Submit both the published post URL and the repository folder URL. Nothing in this package has been pushed or published.

## Validation status

The Python workflow was executed against both cached source files, and a second complete run regenerated all outputs. Both figures were visually inspected. The included HTML preview embeds those figures and the article. Quarto and R were unavailable in the creation environment, so site integration and the R alternative still need local execution checks. The analysis is complete; publishing remains a separate step.

## Burden severity extension

Tracts are assigned to four equal-frequency groups using pandas `qcut` on median gross rent (94 tracts per group in this release). The breaks are saved in `summary.json`; ties and exact intervals are handled by `qcut`, not manual assignment. These are groups of **places by their median rent**, not quartiles of individual households by the rent they pay. Households in any group can pay rents outside its tract-median range.

For each group, sum B25070_002E–006E (under 30%), 007E–009E (30% to under 50%), and 010E (50% or more); divide each by the sum of 001E minus 011E. The Python implementation obtains the first category as valid minus burdened and the second as burdened minus severe. No-cash and noncomputed cases remain excluded, consistent with every other figure. All three shares are checked to sum to 100%. The third group is not lower than the first in severe burden; no monotonic relationship or statistical significance is asserted.

The R alternative also writes `quartile_burden_R.csv` and `quartile_burden_R.png` and checks its shares against the Python reference. Its execution remains unverified in this environment.
