# Open Syndrome workshop

These files are part of the workshop "Composable Case Definitions", where the Open Syndrome Definition format is showcased 
in a real-world data setting.

Questions? Be in touch: opensyndrome@anapaulagomes.me

## Data

Outpatient (ambulatory) records from the Brazilian Unified Health System (SUS) for the state of Pernambuco (PE) from 2014 to 2017,
the period of the Zika epidemic. The data come from DATASUS SIASUS (Sistema de Informações Ambulatoriais do SUS),
and it is republished here with friendly English column names, a data dictionary, and pinned provenance.

* Technical note: ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/Informe_Tecnico_SIASUS_2019_07.pdf
* Temporal coverage: 2014-01 to 2017-12 (by processing / competence month, the month each file was billed).
* Extraction date: 2026-06-12

Both notebooks, Python or R, read `workshop_sia_bi.parquet` from the working directory.

## Python — `workshop.py`

You will need [uv](https://docs.astral.sh/uv/). The dependencies are inline (PEP 723), so you don't need to worry about it.
We will use the following:

* [marimo](https://marimo.io)
* [opensyndrome](https://pypi.org/project/opensyndrome/)

```bash
uv run marimo edit --sandbox workshop.py   # notebook
uv run marimo run  --sandbox workshop.py   # app, code hidden
```

On [molab](https://molab.marimo.io), upload `workshop.py` with `workshop_sia_bi.parquet`.

> Don't wanna install things on your machine? Use marimo to follow the code. [![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/notebooks/nb_yAMMhdQm1tzkpCcirih3xX)

## R — `workshop.qmd`

You will need R (from version 4.5.0) and the [Quarto](https://quarto.org) CLI (bundled with RStudio and Positron).
We will use the following:

* [opensyndrome-r](https://github.com/OpenSyndrome/open-syndrome-r)

```r
install.packages(c("dplyr", "ggplot2", "jsonlite", "knitr", "nanoparquet", "remotes", "tibble", "tidyr", "yaml"))
remotes::install_github("OpenSyndrome/open-syndrome-r")
```

```bash
quarto render workshop.qmd    # writes workshop.html
```

Or open it in RStudio / Positron / VS Code and run the chunks one by one.
