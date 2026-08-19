# Open Syndrome workshop

Filtering outpatient data (SIA/SUS, Pernambuco, 2013-2017) with
[Open Syndrome Definitions](https://opensyndrome.org). Same walkthrough in two
notebooks: map your columns to OSD concepts, apply a definition, plot the matches,
then do it again with the arbovirosis and Zika definitions from the
[community catalogue](https://github.com/OpenSyndrome/definitions).

Run from the repository root — both read `workshop_sia_bi.parquet` from the working
directory. The first run downloads the catalogue into `~/.open_syndrome/`, shared by both.

## Python — `workshop.py`

[marimo](https://marimo.io) + [`opensyndrome`](https://github.com/OpenSyndrome/open-syndrome-python).
Needs [uv](https://docs.astral.sh/uv/); dependencies are inline (PEP 723).

```bash
uv run marimo edit --sandbox workshop.py   # notebook
uv run marimo run  --sandbox workshop.py   # app, code hidden
```

On [molab](https://molab.marimo.io), upload `workshop.py` with `workshop_sia_bi.parquet`.

## R — `workshop.qmd`

[Quarto](https://quarto.org) + [`opensyndrome`](https://github.com/OpenSyndrome/open-syndrome-r).
Needs R and the Quarto CLI (bundled with RStudio and Positron).

```r
install.packages(c("dplyr", "ggplot2", "jsonlite", "knitr", "nanoparquet", "remotes", "tibble", "tidyr", "yaml"))
remotes::install_github("OpenSyndrome/open-syndrome-r")
```

```bash
quarto render workshop.qmd    # writes workshop.html
```

Or open it in RStudio / Positron / VS Code and run the chunks one by one.
