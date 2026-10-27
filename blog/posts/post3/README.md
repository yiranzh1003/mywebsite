# Blog 3: Parenthood and the Gender Earnings Gap

Using the 2025 IPUMS CPS ASEC, this post asks how work patterns and the gender wage-income gap differ by the presence of own children in the household. All population means and proportions use ASECWT. Work and income refer to 2024; household child presence is observed in 2025. Results are descriptive, not causal.

## Files
| Location | Contents |
| --- | --- |
| `index.qmd` | Complete article, figures and original author/date metadata; ready for Quarto rendering. |
| `code/analyze.py` | Full data cleaning, weighted calculations, three figures and article generation. The prose template is at the end of this script. |
| `data/` | Original IPUMS pair: `cps_00001.dat.gz` and its matching DDI/codebook `cps_00001.xml`. |
| `results/` | Two aggregate CSVs and three PNG figures. `group_summary.csv` contains group counts and work rates; `earnings_summary.csv` contains income means and counts for both earnings samples. PNGs correspond to Figures 1–3. |

## Reproduce
Python 3.11 or later is required to regenerate the analysis. Install dependencies once, then run from this folder:

```bash
python -m pip install pandas==2.2.3 numpy==2.3.5 matplotlib==3.10.8
python code/analyze.py
```

The script reads the original extract using field positions and implied decimals from the matching XML. It rebuilds both tables, all three figures and `index.qmd`, inserting the computed estimates into the article. Edit the prose template in the script for changes that should persist after regeneration. No network access or random sampling is used in the analysis. To display the supplied article, render `index.qmd` normally in Quarto; this does not execute Python or require R.

## Data access
The local package includes the existing extract. Raw microdata and the XML are excluded from Git by the supplied ignore rules; the public repository contains code, aggregate results and figures. IPUMS CPS requires permission for redistribution of microdata: https://cps.ipums.org/cps/terms.shtml.

A reader can render the included article immediately. To rerun the analysis without the local extract, register with IPUMS CPS and request the **2025 ASEC** with `AGE`, `SEX`, `NCHILD`, `ASECWT`, `WKSWORK1`, `UHRSWORKLY` and `INCWAGE`, plus automatic variables `YEAR` and `ASECFLAG`. Save the matching fixed-width `.dat.gz` and XML files in `data/` using the filenames above. The reader uses the new XML's field positions automatically; data-release revisions can change results.

## Measures
- **Adults:** ages 25–54, valid SEX/NCHILD, positive ASECWT; no income or work restriction. This is the ASEC adult population, not specifically the survey-week civilian labor force. Unweighted n=55,003.
- **Child presence:** NCHILD>0 includes own biological/adopted/stepchildren of any age living in the household. No co-resident children does not imply never having had children.
- **Worked during 2024:** 1–52 weeks, divided by all adults in the group. Zero weeks is outside the worked-last-year universe; such adult records in this extract have hours=999 and no positive valid wage income.
- **Part-time:** 1–34 usual weekly hours, divided by those with 1–52 work weeks, including self-employed and unpaid family workers.
- **Wage recipients:** positive INCWAGE below 99,999,998; excludes missing/out-of-universe codes. Unweighted n=44,167. Full-time, full-year additionally requires 35–99 usual hours and 50–52 weeks; n=34,996. Hours=99 is valid; 999 is out of universe.
- **Weights and gaps:** raw ASECWT has four implied decimal places, applied exactly once. Means use sum(weight × income)/sum(weight); rates use weighted numerators/denominators. Gap=100 × (1 − women's mean/men's mean). Income is annual pre-tax wage income in 2024 dollars. No causal effects or survey-design confidence intervals are estimated.
