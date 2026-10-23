# Blog6: How Income Measurement Changes the Father–Son Earnings Link

This post uses Python and SQLite to match biological fathers and sons in the PSID and compare wage elasticities across measurement ages and income windows.

## Files

- `index.qmd`: article source for the existing Quarto website.
- `code/analyze.py`: reads the original PSID fixed-width extract using the supplied Stata column specifications, constructs data tables, executes SQL, estimates models, and saves results.
- `code/build_post.py`: inserts calculated estimates into the article. It also creates an optional local preview, which is excluded from Git.
- `sql/01_match.sql` and `sql/02_average.sql`: matching and aggregation queries.
- `data/raw/cpi_official.csv`: annual CPI table from the Federal Reserve Bank of Minneapolis.
- `data/variable_map.csv`: exact PSID variables and years used.
- `results/tables/ige_estimates.csv`: final aggregate results.
- `results/figures/ige_comparison.png`: article figure.

## Reproduce

Install Python dependencies with `python -m pip install numpy pandas matplotlib`.

Obtain your own public-use extract from the [PSID Data Center](https://simba.isr.umich.edu/). Include individual identifiers ER30001/ER30002, sex ER32000, biological-father identifiers ER32016/ER32017, and all wave-specific variables in `data/variable_map.csv`. Request individual records with linked family variables, and download the ASCII data and Stata import statements. Place the matching `J*.txt` and `J*.do` files in `data/raw/`; keep only one extract there. The script reads column positions and variable labels from the Stata file, so the extract number need not be J366590. The complete download includes the original J366590 data, Stata import statements, codebook and formats for local replication. These files are excluded from Git by `.gitignore`. Other readers should download their own extract using these instructions.

Run from this folder:

```
python code/analyze.py
python code/build_post.py
```

The first run reads the original fixed-width extract; later runs reuse a local pickle cache. Remove that cache if you change raw inputs. The script creates `data/analysis.sqlite`, runs SQL within Python, and saves tables and figures. No server or API key is needed.

## Use other survey years

Keep ER30001/ER30002, ER32000 and ER32016/ER32017 for the person and father keys. For each selected wave, obtain wages, individual age, relationship to head/reference person, sequence number and family interview number. `data/variable_map.csv` gives the fields for the current demonstration. In `code/analyze.py`, change `years` and the matching `income_vars` list together, retaining their order; the script locates the other wave variables from Stata labels. Check the codebook for relationship, residency, missing and top-code definitions; revise the filters if definitions differ. Provide CPI for every income year, usually wave minus one. The person-level SQL join need not change. Keep enough follow-up observations to satisfy all three age windows, or explicitly revise those windows and minimum counts in both code and article.

## Data and sample

PSID public-use Data Center extract J366590, downloaded October 22, 2026. The data contain 85,536 individuals. The public-use extract was obtained through an individually registered PSID account. Consult the original codebook for codes and restrictions.

The analysis uses biological father identifiers ER32016/ER32017 matched to ER30001/ER30002, male sex, positive wages and salaries, and current head/reference-person status. It uses income-year ages (interview age minus one). Fathers require at least three observed positive-wage years at ages 35–44; sons require at least two at ages 25–29 and 40–44. Every model uses the same balanced sample. Annual wages are CPI-adjusted to 2022 dollars before arithmetic averaging, then logged. Only the baseline single-year comparison uses wages nearest the target age within each window. A linear son birth-cohort control is included. Uncertainty is clustered by father. Estimates are descriptive, unweighted, and conditional on selection and positive wages.

Total-labor-income variables are retained in the original extract for documentation but are not used in the final analysis because their treatment of farm/business income changes across waves. Wage variables from 1968–1969 were not requested because they are brackets rather than dollar values. Special-code and top-code endpoints are excluded. The analysis is not a national or lifetime-income estimate.

CPI source: https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator/consumer-price-index-1800- (annual index; its base scale cancels in the adjustment ratio).

## Data availability

The repository includes the CPI input, PSID variable map, aggregate estimates, and code used to generate the analysis and figure. PSID respondent-level data, including the matched father–son analysis file, are excluded under the [PSID Conditions of Use](https://simba.isr.umich.edu/U/CondUse.aspx). These restrictions also apply to user-created extracts; removing identifiers does not make an analysis file freely redistributable. Registered readers can obtain the required variables from the PSID Data Center and follow the replication steps above. PSID directs shared extracts and analysis files to its [Public Data Extract Repository](https://www.icpsr.umich.edu/sites/psid/home); no repository deposit has been made for this project.
