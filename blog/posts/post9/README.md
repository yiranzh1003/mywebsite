# Blog 9 replication

- `index.qmd` is the English blog post.
- `backtest.py` builds predictors, runs the model comparison, saves tables and a wealth chart in `results/`, and updates the marked result blocks in `index.qmd`.
- `data/tickers.txt` contains the 95 tickers in the course script and SPY.
- Yahoo Finance is the market data source. If `data/prices.csv` is present, it is the input snapshot for the delivered run. The course game summary uses 45 complete pairs from the Fall 2026 Canvas workbook (see below).

Run from this folder using Python 3.12 or newer.

```sh
python -m pip install numpy pandas matplotlib xgboost-cpu==3.4.1
python download_prices.py
python backtest.py
quarto render index.qmd
```

The download step can be skipped when using the bundled input snapshot. If Yahoo's Python endpoint is unavailable, use R with `tidyquant` and `readr` installed and run `Rscript download_prices.R`. The input has `symbol,date,open,high,low,close,volume,adjusted` fields and uses the course script's price start date with a fixed November 13, 2026 cutoff. Use plain Quarto render or copy the folder into your site's blog directory and render within that site.

The classroom baseline is a Python reimplementation of the supplied `UPenn_XGBoostStockPrediction copy.R` specification. It keeps the depth, tree count, learning rate, predictors (including the original signs of lagged price ratios), and target. The original target spans 19 close-to-close returns, from the next session's close to the 20th session's close. For a continuous, nonoverlapping wealth curve, the next allocation starts at the previous exit close. Both models use the SPY calendar, completed labels at each split, valid portfolio weights, and identical execution dates. Both use the 2024 onward test window, while tree depth is chosen from 1, 2, and 3 using only pre-2024 validation. RMSE uses all available labeled test predictions. Net wealth assumes a 10 bp charge per dollar traded, including initial establishment and subsequent adjustments based on drifted weights, and no forced terminal liquidation. The capped strategy clips allocations at 15% on rebalance dates and holds the residual in zero-yield cash. Reported drawdowns are measured at holding-period endpoints.

For the classroom summary, place the supplied `Full_Results copy.xlsx` in this directory. Run the instructor's paired comparison in R:

```r
g <- readxl::read_excel("Full_Results copy.xlsx")
d <- as.numeric(g$portfolio2) - as.numeric(g$portfolio1)
c(teams = sum(!is.na(d)), indicator_wins = sum(d > 0, na.rm = TRUE))
t.test(d)
```

The class workbook and teacher's original scripts can be obtained from the Canvas materials for AEDS 6400. The class summary describes the class game and the price-based backtest evaluates the model separately.
