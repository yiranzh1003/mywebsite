# Yiran Zhang's Personal Website

This repository contains my personal website and blog for Computational Methods for Economists.

## Blog Post 2: Web Scraping for Actionable Insights

Blog Post 2 examines how career opportunities differ across O*NET Job Zones. I use the `rvest` package in R to scrape publicly accessible O*NET OnLine pages on Job Zones and Bright Outlook occupations, then clean, merge, analyze, and visualize the data.

### Reproduction

To reproduce the analysis:

1. Open `blog/posts/post2/index.qmd`.
2. Install the required R packages: `rvest`, `dplyr`, `stringr`, and `ggplot2`.
3. Render `index.qmd` in Quarto.

The data are collected directly from O*NET OnLine when the document is rendered.