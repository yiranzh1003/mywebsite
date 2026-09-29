# Blog Post 2: Growth, Job Openings, and Entry Barriers

## Research question

How do rapid-growth and high-opening occupations differ across O*NET Job Zones, and what does this suggest about the relationship between career opportunities and entry barriers?

## Data source

The analysis uses publicly available data from O*NET OnLine.

Two O*NET pages are scraped using the `rvest` package in R:

- Job Zone data, which classify occupations by preparation requirements.
- Bright Outlook data, which identify occupations with rapid growth, numerous job openings, or both.

The two datasets are joined using O*NET occupation codes.

## Analysis

`index.qmd` contains the complete web scraping, data cleaning, analysis, and visualization code used in the blog post.

The analysis compares the distribution of Bright Outlook occupations across O*NET Job Zones and distinguishes among:

- Rapid Growth
- Numerous Openings
- Rapid Growth + Numerous Openings

## Reproduce

Install the required R packages:

```r
install.packages(c("rvest", "dplyr", "stringr", "ggplot2"))