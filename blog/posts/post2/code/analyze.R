# Blog 2: offline replication plus a small, explicit rvest refresh function.
suppressPackageStartupMessages({
  library(rvest)
  library(dplyr)
  library(stringr)
  library(ggplot2)
})
example_codes <- c("47-2061.00", "31-9092.00", "13-2011.00", "15-1252.00")
clean_title <- function(x) str_squish(str_remove_all(x, fixed("Bright Outlook")))

# Optional: six public pages, once each, sequentially with a one-second pause.
# Fresh data go into a separate folder; the original analysis snapshot is preserved.
# Stop if access is denied; do not bypass authentication, CAPTCHAs or other restrictions.
scrape_current_sources <- function(destination = "data/_refresh") {
  dir.create(file.path(destination, "_profiles"), recursive = TRUE, showWarnings = FALSE)
  fetch_table <- function(url, columns) {
    doc <- read_html(url)
    candidates <- html_elements(doc, "table") |> html_table(fill = TRUE)
    match <- which(vapply(candidates, function(x) all(columns %in% names(x)), logical(1)))
    if (length(match) != 1L) stop("Expected one occupation table; inspect the page structure.")
    Sys.sleep(1)
    tab <- candidates[[match]]
    tab$Occupation <- clean_title(tab$Occupation)
    tab
  }
  zones <- fetch_table("https://www.onetonline.org/find/zone?z=0", c("Code", "Job Zone", "Occupation"))
  bright <- fetch_table("https://www.onetonline.org/find/bright?b=0", c("Code", "Occupation", "Categories"))
  write.csv(zones, file.path(destination, "job_zones.csv"), row.names = FALSE)
  write.csv(bright, file.path(destination, "bright_outlook.csv"), row.names = FALSE)
  for (code in example_codes) {
    doc <- read_html(paste0("https://www.onetonline.org/link/summary/", code))
    xml2::write_html(doc, file.path(destination, "_profiles", paste0(code, ".html")))
    Sys.sleep(1)
  }
  writeLines(paste("Retrieved:", Sys.Date()), file.path(destination, "retrieved.txt"))
  invisible(destination)
}

analyze_blog2 <- function(input_dir = "data", output_dir = "results") {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  zones <- read.csv(file.path(input_dir, "job_zones.csv"), colClasses = "character", check.names = FALSE)
  bright <- read.csv(file.path(input_dir, "bright_outlook.csv"), colClasses = "character", check.names = FALSE)
  stopifnot(!anyDuplicated(zones$Code), !anyDuplicated(bright$Code))
  career <- bright %>% select(Code, Occupation, Categories) %>%
    mutate(Occupation = clean_title(Occupation)) %>%
    left_join(select(zones, Code, `Job Zone`), by = "Code") %>%
    mutate(rapid_growth = str_detect(Categories, fixed("Rapid Growth")),
           many_openings = str_detect(Categories, fixed("Numerous Job Openings")),
           outlook_type = case_when(rapid_growth & many_openings ~ "Both flags",
             rapid_growth ~ "Growth flag only", many_openings ~ "Openings flag only",
             TRUE ~ "Other"))
  analysis <- filter(career, !is.na(`Job Zone`), `Job Zone` != "")
  stopifnot(nrow(analysis) > 0, all(analysis$`Job Zone` %in% c("1-2", "3", "4", "5")))
  both <- filter(analysis, rapid_growth, many_openings)
  both_summary <- both %>% count(`Job Zone`, name = "occupations") %>%
    mutate(share_percent = 100 * occupations / sum(occupations))
  distribution <- analysis %>% count(`Job Zone`, outlook_type, name = "occupations")
  write.csv(career, file.path(output_dir, "career_data.csv"), row.names = FALSE)
  write.csv(both_summary, file.path(output_dir, "both_summary.csv"), row.names = FALSE)

  # rvest reads saved copies of the public occupation pages for offline replication.
  # Wages are parsed from the median-wages definition list, not manually typed.
  parse_wage <- function(code) {
    doc <- read_html(file.path(input_dir, "_profiles", paste0(code, ".html")))
    label <- html_element(doc, xpath = "//dt[contains(., 'Median wages')]")
    value <- html_element(label, xpath = "following-sibling::dd[1]") |> html_text2()
    year <- str_extract(html_text2(label), "[0-9]{4}")
    annual <- str_match(value, "\\$([0-9,]+(?:\\.[0-9]+)?)\\s+annual")[, 2]
    if (is.na(annual) || is.na(year)) stop(paste("Could not parse wage/year for", code))
    data.frame(Code = code, wage_year = as.integer(year),
      median_annual_wage = as.numeric(gsub(",", "", annual, fixed = TRUE)),
      source_url = paste0("https://www.onetonline.org/link/summary/", code))
  }
  wages <- bind_rows(lapply(example_codes, parse_wage))
  examples <- wages %>% left_join(select(analysis, Code, Occupation, `Job Zone`, rapid_growth, many_openings), by = "Code")
  stopifnot(nrow(examples) == 4L, all(examples$rapid_growth), all(examples$many_openings),
            all(examples$median_annual_wage > 0), !anyNA(examples$`Job Zone`))
  write.csv(examples, file.path(output_dir, "occupation_examples.csv"), row.names = FALSE)
  distribution$`Job Zone` <- factor(distribution$`Job Zone`, levels = c("1-2", "3", "4", "5"))
  distribution$outlook_type <- factor(distribution$outlook_type,
    levels = c("Growth flag only", "Openings flag only", "Both flags", "Other"))
  plot <- ggplot(distribution, aes(`Job Zone`, occupations, fill = outlook_type)) +
    geom_col(position = position_dodge(width = .8), width = .7) +
    geom_text(aes(label = occupations), position = position_dodge(width = .8), vjust = -.4, size = 3.7) +
    scale_fill_manual(values = c("Growth flag only" = "#7c9d9b", "Openings flag only" = "#bc866e",
      "Both flags" = "#315b76", "Other" = "#999999"), drop = TRUE) +
    scale_y_continuous(expand = expansion(mult = c(0, .12))) +
    labs(title = "Bright Outlook occupation titles by preparation level",
      subtitle = "Counts of matched occupation titles, not counts of jobs or vacancies",
      x = "O*NET Job Zone", y = "Number of occupation titles", fill = NULL,
      caption = "Source: original O*NET OnLine rvest snapshot. Only refers to the growth/openings flags;\nother designations may also apply. Titles with no matched Job Zone are excluded.") +
    theme_minimal(base_size = 12) + theme(panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(), legend.position = "top",
      plot.title = element_text(face = "bold"), plot.caption = element_text(hjust = 0, size = 9))
  ggsave(file.path(output_dir, "outlook_by_zone.png"), plot, width = 10, height = 5.8, dpi = 180, bg = "white")
  invisible(list(career = career, analysis = analysis, both = both,
    both_summary = both_summary, examples = examples, distribution = distribution))
}
