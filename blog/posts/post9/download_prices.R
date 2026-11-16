# Run from the Blog9 directory.
tickers <- readLines("data/tickers.txt")
prices <- tidyquant::tq_get(
  tickers, get = "stock.prices", from = "2022-01-01", to = "2026-11-14",
  complete_cases = FALSE
)
required <- c("symbol", "date", "open", "high", "low", "close", "volume", "adjusted")
stopifnot(all(required %in% names(prices)))
prices <- prices[complete.cases(prices[, required]), required]
missing <- setdiff(tickers, prices$symbol)
if (length(missing)) stop("Missing prices for: ", paste(missing, collapse = ", "))
readr::write_csv(prices, "data/prices.csv")
