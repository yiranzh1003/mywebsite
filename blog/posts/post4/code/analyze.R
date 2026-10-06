# Run from the blog4 directory: Rscript code/analyze.R
# Packages are installed once, following README.md; no API key is needed.
library(tidyverse)
library(lubridate)
library(scales)
for (p in c('data/raw', 'data/processed', 'results/figures')) {
  dir.create(p, recursive = TRUE, showWarnings = FALSE)
}
read_series <- function(id) {
  path <- file.path('data/raw', paste0(id, '.csv'))
  if (!file.exists(path)) {
    url <- paste0('https://fred.stlouisfed.org/graph/fredgraph.csv?id=', id,
                  '&cosd=2019-01-01&coed=2024-12-31')
    download.file(url, path, mode = 'wb', quiet = TRUE)
  }
  read_csv(path, na = c('', '.'), show_col_types = FALSE) |>
    mutate(observation_date = as.Date(observation_date)) |>
    filter(observation_date >= as.Date('2019-01-01'),
           observation_date <= as.Date('2024-12-31'))
}
prices <- read_series('CSUSHPINSA') |> rename(month = observation_date, price = CSUSHPINSA)
cpi <- read_series('CPIAUCSL') |> rename(month = observation_date, cpi = CPIAUCSL)
rates <- read_series('MORTGAGE30US') |>
  mutate(month = floor_date(observation_date, 'month')) |>
  group_by(month) |> summarise(rate = mean(MORTGAGE30US, na.rm = TRUE), .groups = 'drop')
d <- prices |> inner_join(cpi, by = 'month') |> inner_join(rates, by = 'month') |> arrange(month)
stopifnot(nrow(d) == 72, !anyNA(d), !anyDuplicated(d$month))
b <- d[1, ]
payment <- function(principal, annual_rate) {
  monthly_rate <- annual_rate / 1200
  principal * monthly_rate / (1 - (1 + monthly_rate)^(-360))
}
d <- d |> mutate(
  price_index = 100 * price / b$price,
  real_price_index = price_index / (cpi / b$cpi),
  payment = payment(240000 * price / b$price, rate),
  price_only = payment(240000 * price / b$price, b$rate),
  real_payment = payment / (cpi / b$cpi)
)
write_csv(d, 'data/processed/monthly_analysis.csv')
e <- tail(d, 1)
metrics <- tibble(r0 = b$rate, r1 = e$rate,
  price_growth = e$price_index - 100, real_price_growth = e$real_price_index - 100,
  m0 = d$payment[1], m1 = e$payment, price_only = e$price_only,
  payment_growth = 100 * (e$payment / d$payment[1] - 1),
  real_payment_growth = 100 * (e$real_payment / d$payment[1] - 1))
write_csv(metrics, 'results/metrics.csv')
style <- theme_minimal(base_size = 12) + theme(
  panel.grid.minor = element_blank(), panel.grid.major.x = element_blank(),
  plot.title = element_text(face = 'bold'), legend.position = 'bottom',
  plot.caption = element_text(hjust = 0, size = 8))
colors <- c('#1f537a', '#c96846')
g1 <- d |> select(month, `Nominal home prices` = price_index,
                  `Inflation-adjusted home prices` = real_price_index) |>
  pivot_longer(-month, names_to = 'series', values_to = 'index') |>
  ggplot(aes(month, index, color = series)) + geom_line(linewidth = 1) +
  geom_hline(yintercept = 100, linetype = 'dashed', color = 'gray60') +
  scale_color_manual(values = colors) + labs(
    title = '1. Home prices remained above their pre-pandemic level',
    x = NULL, y = 'Index (January 2019 = 100)', color = NULL,
    caption = 'Source: S&P Dow Jones Indices and BLS via FRED. Case-Shiller NSA / CPI SA; 2019–2024.') + style
g2 <- ggplot(d, aes(month, rate)) + geom_line(linewidth = 1, color = colors[1]) +
  labs(title = '2. Financing became more expensive after 2021', x = NULL,
    y = '30-year fixed mortgage rate (%)',
    caption = 'Source: Freddie Mac via FRED. Monthly means of weekly rates; PMMS method changed in Nov. 2022.') + style
g3 <- d |> select(month, `Changing prices and rates` = payment,
                 `Changing prices; January 2019 rate held fixed` = price_only) |>
  pivot_longer(-month, names_to = 'scenario', values_to = 'monthly_payment') |>
  ggplot(aes(month, monthly_payment, color = scenario, linetype = scenario)) +
  geom_line(linewidth = 1) + scale_color_manual(values = colors) +
  scale_y_continuous(labels = label_dollar()) + labs(
    title = '3. Prices and rates together increased the monthly payment',
    x = NULL, y = 'Monthly principal and interest (nominal US dollars)',
    color = NULL, linetype = NULL,
    caption = 'Author calculations: $300,000 home in Jan. 2019; 20% down; 360 payments. Excludes taxes/insurance.') + style
for (i in 1:3) {
  name <- c('01_prices', '02_rates', '03_payments')[i]
  ggsave(file.path('results/figures', paste0(name, '.png')), get(paste0('g', i)),
         width = 9, height = 5, dpi = 180)
}
