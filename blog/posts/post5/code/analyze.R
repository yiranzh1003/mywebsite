# Alternative R workflow. Run from blog5: Rscript code/analyze.R
# Creates separate *_R outputs, preserving the verified Python figures.
pkgs <- c('jsonlite', 'sf', 'ggplot2')
missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop('Install packages first: ', paste(missing, collapse = ', '))
library(ggplot2)
stopifnot(file.exists('data/raw/acs2024_5yr.json'))
x <- jsonlite::fromJSON('data/raw/acs2024_5yr.json', simplifyVector = FALSE)
num <- function(a, key) if (is.null(a[[key]])) NA_real_ else as.numeric(a[[key]])
rows <- lapply(names(x$data), function(g) {
  a <- x$data[[g]]$B25070$estimate
  total <- num(a, 'B25070001'); nc <- num(a, 'B25070011')
  valid <- total - nc
  count <- sum(vapply(sprintf('B25070%03d', 7:10), function(k) num(a, k), numeric(1)))
  rent <- num(x$data[[g]]$B25064$estimate, 'B25064001')
  if (!is.na(rent) && rent <= 0) rent <- NA_real_
  data.frame(geoid = g, rent = rent, total = total, not_computed = nc,
             valid = valid, burden_count = count,
             burden = if (!is.na(valid) && valid > 0) 100 * count / valid else NA_real_)
})
d <- do.call(rbind, rows)
d$eligible <- !is.na(d$rent) & !is.na(d$burden) & d$valid >= 100
s <- d[d$eligible, ]; cutoff <- median(s$rent)
s$group <- ifelse(s$rent < cutoff, 'Lower-rent half', 'Higher-rent half')
groups <- do.call(rbind, lapply(split(s, s$group), function(z) {
  data.frame(group = z$group[1], tracts = nrow(z), eligible_households = sum(z$valid),
             burdened_households = sum(z$burden_count),
             burden_pct = 100 * sum(z$burden_count) / sum(z$valid),
             median_tract_rent = median(z$rent))
}))
# Compare against the independently generated, shipped Python statistics.
reference <- read.csv('data/processed/tract_statistics.csv', stringsAsFactors = FALSE)
reference <- reference[match(d$geoid, reference$geoid), ]
stopifnot(isTRUE(all.equal(d$burden, reference$burden, tolerance = 1e-8)),
          nrow(s) == 376, length(unique(d$geoid)) == nrow(d))
write.csv(d, 'data/processed/tract_statistics_R.csv', row.names = FALSE)
write.csv(groups, 'results/group_summary_R.csv', row.names = FALSE)
boundary <- sf::st_read('data/raw/tracts_tiger2024.geojson', quiet = TRUE)
stopifnot(setequal(boundary$geoid, d$geoid))
boundary <- boundary[, 'geoid', drop = FALSE]
boundary <- merge(boundary, d, by = 'geoid', all.x = TRUE, sort = FALSE)
# Project to Pennsylvania South (metres) for mapping.
boundary <- sf::st_transform(boundary, 2272)
boundary$rent_band <- cut(ifelse(boundary$eligible, boundary$rent, NA),
  breaks = c(0, 1000, 1250, 1500, 1750, Inf), right = FALSE,
  labels = c('Under $1,000', '$1,000–1,249', '$1,250–1,499', '$1,500–1,749', '$1,750+'))
boundary$burden_band <- cut(ifelse(boundary$eligible, boundary$burden, NA),
  breaks = c(0, 30, 40, 50, 60, 101), right = FALSE,
  labels = c('Under 30%', '30–39%', '40–49%', '50–59%', '60%+'))
map <- function(variable, title, palette, filename) {
  p <- ggplot(boundary) + geom_sf(aes(fill = .data[[variable]]), color = 'white', linewidth = .08) +
    scale_fill_manual(values = palette, na.value = 'grey85', drop = FALSE, name = NULL) +
    labs(title = title, subtitle = 'Philadelphia census tracts | ACS 2020–2024',
      caption = 'Gray: unavailable or fewer than 100 estimated households with a computed ratio.\nSource: ACS B25064/B25070; Census Reporter TIGER 2024.') +
    theme_void(base_size = 12) + theme(plot.title = element_text(face = 'bold'),
      legend.position = 'right', plot.caption = element_text(hjust = 0))
  ggsave(filename, p, width = 8, height = 8, dpi = 200, bg = 'white')
}
map('rent_band', 'Median monthly gross rent', c('#eff3ff','#bdd7e7','#6baed6','#3182bd','#08519c'), 'results/figures/rent_map_R.png')
map('burden_band', 'Rent-burdened households (30%+ of income)', c('#fff5eb','#fdd0a2','#fdae6b','#e6550d','#a63603'), 'results/figures/burden_map_R.png')
p <- ggplot(s, aes(rent, burden)) + geom_point(color = '#326b87', alpha = .55) +
  labs(x = 'Median monthly gross rent ($)', y = 'Rent-burdened households (%)',
       title = 'Rent alone does not rank affordability') + theme_minimal()
ggsave('results/figures/rent_burden_scatter_R.png', p, width = 9, height = 5.6, dpi = 200)
print(groups)
writeLines(capture.output(sessionInfo()), 'results/sessionInfo_R.txt')
# Severity by quartile: use quantile breaks on TRACT median rents.
s$severe_count <- vapply(s$geoid, function(g) num(x$data[[g]]$B25070$estimate, 'B25070010'), numeric(1))
breaks <- quantile(s$rent, probs = seq(0, 1, .25), names = FALSE)
stopifnot(length(unique(breaks)) == 5)
s$quartile <- cut(s$rent, breaks = breaks, include.lowest = TRUE, labels = FALSE)
qtab <- do.call(rbind, lapply(split(s, s$quartile), function(z) {
 den <- sum(z$valid)
 data.frame(quartile = z$quartile[1], tracts = nrow(z),
   below30 = 100 * sum(z$valid - z$burden_count) / den,
   from30to50 = 100 * sum(z$burden_count - z$severe_count) / den,
   atleast50 = 100 * sum(z$severe_count) / den)
}))
ref <- read.csv('results/quartile_burden.csv')
stopifnot(max(abs(qtab$atleast50 - ref$atleast50)) < 1e-8,
          max(abs(rowSums(qtab[, c('below30','from30to50','atleast50')]) - 100)) < 1e-8)
write.csv(qtab, 'results/quartile_burden_R.csv', row.names = FALSE)
long <- reshape(qtab[, c('quartile','below30','from30to50','atleast50')],
 varying = c('below30','from30to50','atleast50'), v.names = 'share',
 timevar = 'category', times = c('Under 30%','30% to under 50%','50% or more'), direction = 'long')
long$category <- factor(long$category, levels = c('Under 30%','30% to under 50%','50% or more'))
p <- ggplot(long, aes(x = share, y = factor(quartile, levels = 4:1), fill = category)) +
 geom_col(position = position_stack(reverse = TRUE)) +
 scale_fill_manual(values = c('#d9e3e8','#f6b477','#b94a23')) +
 labs(x = 'Share of households with a computed ratio (%)', y = 'Tract rent quartile (1 = lowest)',
 title = 'Severe rent burdens persist in lower-rent areas', fill = 'Income share spent on housing') +
 theme_minimal() + theme(legend.position = 'bottom')
ggsave('results/figures/quartile_burden_R.png', p, width = 10, height = 5.5, dpi = 200)
