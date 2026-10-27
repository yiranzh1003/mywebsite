# Blog 7: Does Economic Growth Always Mean Longer Lives?

## Project structure
- `index.qmd`: article and metadata for the Quarto website.
- `code/analyze.py`: data validation, interactive charts and result tables.
- `data/gapminder.csv`: complete fixed input snapshot; no download required.
- `results/`: interactive chart includes (`_world_chart.md` and `_country_chart.md`), exact country values and validation metadata. The chart includes contain raw HTML blocks for Quarto; keep them with the article.

## Reproduce in Python
Use Python 3.11 or newer. In a terminal opened in this folder:

```bash
python -m pip install pandas==2.2.3 plotly==7.1.0
python code/analyze.py
```
The script resolves paths relative to its own location, validates the dataset and regenerates all files in `results/`. No random sampling or network access is used in the analysis. Result tables retain full numerical precision; the article rounds for readability. Edit the article directly in `index.qmd`.

## Data provenance and units
Source: Gapminder historical excerpt, distributed by `plotly.express.data.gapminder()` in Plotly 7.1.0. The bundled CSV was exported directly from that function. Its 1,704 rows represent 142 countries at 12 five-year dates, 1952–2007. This is a historical teaching dataset, not the latest Gapminder release. Plotly adds ISO country fields. `gdpPercap` is inflation-adjusted GDP per capita in US-dollar units; `lifeExp` is life expectancy at birth in years; `pop` is population. Documentation is deliberately followed without assigning the sample the price base of a newer Gapminder release.

- Dataset documentation: https://jennybc.github.io/gapminder/reference/gapminder.html
- Original source: https://www.gapminder.org/data/
- Plotly data API: https://plotly.com/python-api-reference/generated/plotly.express.data.html
- Plotly animations: https://plotly.com/python/animations/

The sample includes only the countries retained in this balanced historical excerpt. No extrapolation or interpolation is performed. Bubble area scales with population; no population-weighted population statistic is reported. Country comparisons are descriptive and cannot establish causality. Country selections in the second chart illustrate contrasting trajectories.
