# Blog Post 3: Parenthood and the Gender Earnings Gap

## Research question

How does the gender earnings gap differ between workers with and without children in the household?

## Required IPUMS extract

The analysis uses the 2025 Annual Social and Economic Supplement (ASEC) of the Current Population Survey, accessed through IPUMS CPS.

To reproduce the analysis:

1. Create an IPUMS CPS extract using the 2025 ASEC sample.
2. Include the variables used in the analysis: `AGE`, `SEX`, `INCWAGE`, `UHRSWORKLY`, `WKSWORK1`, `NCHILD`, and `ASECWT`.
3. Download the matching `.xml` DDI file and `.dat.gz` data file.
4. Place both files in `blog/posts/post3/`.
5. The analysis uses `cps_00001.xml` as the DDI filename. If the downloaded extract has a different name, update the filename in `index.qmd`.

The raw IPUMS CPS microdata are not included in this GitHub repository.

## Analysis

`index.qmd` contains the complete data cleaning, weighted summary statistics, and visualization code used in the blog post.

The analysis restricts the sample to adults ages 25–54 with positive wage and salary income who usually worked at least 35 hours per week and at least 50 weeks during the previous year. Population statistics are calculated using the CPS ASEC person weight (`ASECWT`).

## Reproduce

Install the required R packages:

```r
install.packages(c("tidyverse", "ipumsr"))
```

After placing the IPUMS extract files in the `post3` directory, render:

```bash
quarto render index.qmd
```