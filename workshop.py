# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jsonschema==4.26.0",
#     "marimo",
#     "opensyndrome==0.5.0",
#     "plotly==6.9.0",
#     "polars==1.43.2",
#     "pyyaml==6.0.3",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full", app_title="Open Syndrome Workshop")


@app.cell
def _():
    import json
    from pathlib import Path

    import jsonschema
    import marimo as mo
    import plotly.graph_objects as go
    import polars as pl
    import yaml
    from opensyndrome.artifacts import get_definition_dirs
    from opensyndrome.filter import OSDEngine, load_profile
    from opensyndrome.validators import validate_machine_readable_format

    return (
        OSDEngine,
        Path,
        get_definition_dirs,
        go,
        json,
        jsonschema,
        load_profile,
        mo,
        pl,
        validate_machine_readable_format,
        yaml,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Open Syndrome workshop 🔬

    Filter real ambulatory care data with an [Open Syndrome Definition](https://opensyndrome.org).

    **The four moving parts:** a dataset, a *mapping* (dataset columns → OSD concepts),
    a *definition* (JSON), and the `opensyndrome` engine that compiles the definition
    into filters.

    Two boxes below are yours to edit: the mapping and the definition. Change either and
    everything downstream re-runs on its own.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. The data
    """)
    return


@app.cell
def _(Path, mo, pl):
    DATA_FILE = "workshop_sia_bi.parquet"

    data_path = next(
        (
            candidate
            for candidate in (Path(DATA_FILE), (mo.notebook_dir() or Path.cwd()) / DATA_FILE)
            if candidate.exists()
        ),
        None,
    )

    mo.stop(
        data_path is None,
        mo.callout(
            mo.md(f"Upload **`{DATA_FILE}`** next to this notebook and re-run."),
            kind="danger",
        ),
    )

    df = pl.read_parquet(data_path).with_columns(
        # SIA stores ICD-10 without the dot ("A929"), OSD definitions use "A92.9".
        icd10_dotted=pl.when(pl.col("icd10").str.len_chars() > 3)
        .then(pl.col("icd10").str.slice(0, 3) + "." + pl.col("icd10").str.slice(3))
        .otherwise(pl.col("icd10")),
    )
    return (df,)


@app.cell
def _(df, mo):
    mo.vstack(
        [
            mo.md(
                "Outpatient procedures from SIA/SUS, Brazil's national ambulatory care "
                "system, for the state of Pernambuco. One row per record: an ICD-10 code, "
                "who, where and when.\n\n"
                "The last column is ours: SIA writes codes without the dot (`A929`) and "
                "OSD definitions use `A92.9`, so `icd10_dotted` bridges the two."
            ),
            mo.hstack(
                [
                    mo.stat(label="Rows", value=f"{df.height:,}"),
                    mo.stat(label="Columns", value=df.width),
                    mo.stat(
                        label="Period",
                        value=f"{df['attendance_month'].min()} → {df['attendance_month'].max()}",
                    ),
                ],
                widths="equal",
            ),
            df.head(10),
        ]
    )
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "Where this data comes from": mo.md(r"""
    DATASUS SIASUS, group `BI` (*Boletim de Produção Ambulatorial Individualizado*) — the
    patient-level outpatient record of Brazil's Unified Health System. Collected with
    [PySUS](https://github.com/AlertaDengue/PySUS) from the DATASUS public FTP for the 48
    processing months of 2014-01 to 2017-12, the years of the Zika epidemic, and published as
    [anapaulagomes/sia-pe-2014-2017](https://huggingface.co/datasets/anapaulagomes/sia-pe-2014-2017).

    **Curation.** De-identified upstream: no patient card number, birth date reduced to a year,
    ethnicity removed. Sex codes decoded to `Female` / `Male`, the six-digit DATASUS municipality
    code resolved to a city and a state through the IBGE API, `YYYYMM` dates to `YYYY-MM`.
    DATASUS stores age as a number plus a unit — days and months both mean under a year, and a
    separate unit counts the years past 100 — all collapsed into whole years, then bucketed into
    `age_group`: Infants under 1, Children and adolescents 1-15, Adults 16-59, Elderly 60+.
    DATASUS files carry no real nulls, only fill codes, so the `0000` diagnosis fill, the `99`
    ignored-age sentinel and unusable municipality codes were read as missing and their records
    dropped: 6.6M of the 17.6M raw records survive, the absent diagnosis alone accounting for 10.7M.

    **Read it carefully.** A row is a procedure billed to the SUS, not a confirmed case, and one
    patient can appear many times. The finest time resolution is the month, so there is no
    epidemiological week. Billing is retroactive, which is why 8,435 rows have an attendance month
    back in 2013. `city` is the patient's municipality of residence, not where they were seen:
    27 states appear, though 98.5% of the records are in Pernambuco. 6,704 distinct ICD-10 codes
    are present.

    **License.** The records are public data produced by the SUS under Lei 12.527/2011 and Decreto
    8.777/2016; the curation layer is CC BY 4.0. Cite DATASUS for the data.
    """)
        }
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Map your columns to OSD concepts

    A definition talks about *concepts* — `diagnosis`, `symptom`, `demographic_criteria`,
    `diagnostic_test`, `epidemiological_history` — never about your column names. The
    mapping is the bridge, and `value_encodings` translates OSD's canonical values
    (`male`) into whatever your data writes (`Male`).

    Edit and **Submit**.
    """)
    return


@app.cell
def _(mo):
    INITIAL_MAPPING = """profiles:
      - name: sia_bi
        value_encodings:
          sex:
            male: "Male"
            female: "Female"
        columns:
          icd10_dotted:
            concept: diagnosis
            system: ICD-10
            dtype: string
          age_years:
            concept: demographic_criteria
            attribute: age
            dtype: integer
          sex:
            concept: demographic_criteria
            attribute: sex
            dtype: string
    """

    mapping_editor = mo.ui.code_editor(value=INITIAL_MAPPING, language="yaml").form(
        label="Dataset → OSD mapping", bordered=True
    )
    mapping_editor
    return INITIAL_MAPPING, mapping_editor


@app.cell
def _(INITIAL_MAPPING, df, load_profile, mapping_editor, mo, yaml):
    _raw = mapping_editor.value if mapping_editor.value is not None else INITIAL_MAPPING
    _parsed = yaml.safe_load(_raw)
    _profile = _parsed["profiles"][0]

    _unknown = [name for name in _profile["columns"] if name not in df.columns]
    mo.stop(
        bool(_unknown),
        mo.callout(mo.md(f"**Columns not in the dataset:** {', '.join(_unknown)}"), kind="danger"),
    )

    profile = load_profile(_parsed, _profile["name"])
    return (profile,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. The definition

    An OSD definition is a JSON document. Everything above `inclusion_criteria` is
    metadata — who wrote it, where, for which threat — and none of it is executed. Only
    the criteria run: a row has to satisfy every inclusion criterion and no exclusion
    criterion, and groups inside combine with `AND`, `OR` or `AT_LEAST`.

    Paste your own, or tweak this one and **Submit**.
    """)
    return


@app.cell
def _(mo):
    INITIAL_DEFINITION = """{
      "title": "Arboviral illness",
      "scope": "broad",
      "category": "suspected",
      "version": "1.0.0",
      "open_syndrome_version": "1.0.0",
      "published_in": "https://opensyndrome.org",
      "published_at": "2026-01-01T12:00:00Z",
      "location": "Pernambuco, Brazil",
      "language": "English",
      "organization": "Open Syndrome workshop",
      "definition_type": "syndrome_definition",
      "status": "draft",
      "human_readable_definition": "Outpatient record coded as dengue, chikungunya, Zika or another mosquito-borne viral fever.",
      "references": [{"url": "https://icd.who.int/browse10/2019/en#/A90"}],
      "inclusion_criteria": [
        {
          "type": "criterion",
          "logical_operator": "OR",
          "values": [
            {"type": "diagnosis", "name": "Dengue fever",
             "code": {"system": "ICD-10", "code": "A90"}},
            {"type": "diagnosis", "name": "Dengue haemorrhagic fever",
             "code": {"system": "ICD-10", "code": "A91"}},
            {"type": "diagnosis", "name": "Chikungunya virus disease",
             "code": {"system": "ICD-10", "code": "A92.0"}},
            {"type": "diagnosis", "name": "Zika virus disease",
             "code": {"system": "ICD-10", "code": "A92.5"}},
            {"type": "diagnosis", "name": "Other mosquito-borne viral fevers",
             "code": {"system": "ICD-10", "code": "A92.8"}},
            {"type": "diagnosis", "name": "Mosquito-borne viral fever, unspecified",
             "code": {"system": "ICD-10", "code": "A92.9"}}
          ]
        }
      ]
    }
    """

    definition_editor = mo.ui.code_editor(value=INITIAL_DEFINITION, language="json").form(
        label="OSD definition (JSON)", bordered=True
    )
    definition_editor
    return INITIAL_DEFINITION, definition_editor


@app.cell
def _(mo):
    mo.accordion(
        {
            "Try adding a criterion": mo.md(
                """
    Narrow it down to adults, using the `demographic_criteria` mapping —
    add this to `values` and change the outer `logical_operator` to `AND`:

    ```json
    {"type": "demographic_criteria", "name": "Adults",
     "attribute": "age", "operator": ">=", "value": 18}
    ```
    """
            )
        }
    )
    return


@app.cell
def _(
    INITIAL_DEFINITION,
    definition_editor,
    json,
    jsonschema,
    mo,
    validate_machine_readable_format,
):
    _raw = definition_editor.value if definition_editor.value is not None else INITIAL_DEFINITION

    try:
        definition = json.loads(_raw)
    except json.JSONDecodeError as _error:
        mo.stop(True, mo.callout(mo.md(f"**Invalid JSON:** {_error}"), kind="danger"))

    try:
        validate_machine_readable_format(definition)
        schema_check = mo.callout(
            mo.md(f"**`{definition['title']}`** is a valid Open Syndrome Definition."),
            kind="success",
        )
    except jsonschema.ValidationError as _error:
        schema_check = mo.callout(
            mo.md(f"**Does not match the OSD schema:** {_error.message}"), kind="warn"
        )

    schema_check
    return (definition,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 4. Filter

    `engine.label` adds one boolean column per definition, so nothing is thrown away: you
    keep every row and know which ones match. Use `engine.filter(df, definition)` instead
    when you only want the matching rows.
    """)
    return


@app.cell
def _(OSDEngine, definition, df, profile):
    # skip_unresolvable: criteria with no matching column (e.g. symptoms) are ignored
    engine = OSDEngine(profile, skip_unresolvable=True)

    definition_name = definition["title"]
    labeled = engine.label(df, {definition_name: definition})
    return definition_name, engine, labeled


@app.cell
def _(definition_name, df, labeled, mo):
    _matched = labeled[definition_name].sum()

    mo.vstack(
        [
            mo.hstack(
                [
                    mo.stat(label="Matching records", value=f"{_matched:,}"),
                    mo.stat(label="Share of the dataset", value=f"{_matched / df.height:.4%}"),
                ],
                widths="equal",
            ),
            labeled.filter(labeled[definition_name]).head(10),
        ]
    )
    return


@app.cell
def _(go, pl):
    def plot_monthly(labeled_df, names, month_column="attendance_month"):
        counts = (
            labeled_df.with_columns(
                (pl.col(month_column) + "-01").str.to_date("%Y-%m-%d").alias("month")
            )
            .group_by("month")
            .agg([pl.col(name).sum().alias(name) for name in names])
            .sort("month")
        )
        figure = go.Figure()
        for name in names:
            figure.add_trace(
                go.Scatter(
                    x=counts["month"].to_list(),
                    y=counts[name].to_list(),
                    mode="lines+markers",
                    name=name,
                )
            )
        figure.update_layout(
            xaxis_title="Month of attendance",
            yaxis_title="Matching records",
            yaxis={"tickformat": "d", "rangemode": "tozero"},
            legend={"orientation": "h", "y": -0.25},
            margin={"t": 20},
        )
        return figure

    return (plot_monthly,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 5. Time series of the matches
    """)
    return


@app.cell
def _(definition_name, labeled, plot_monthly):
    plot_monthly(labeled, [definition_name])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 6. Definitions from the community repository

    Definitions are shared in [OpenSyndrome/definitions](https://github.com/OpenSyndrome/definitions).
    `get_definition_dirs()` downloads them once to `~/.open_syndrome/v1/definitions/` and
    returns the directories to read. Same data, same mapping, same engine — only the
    definitions change, and they were written by other people for other places.
    """)
    return


@app.cell
def _(json):
    def find_definitions(directories, terms):
        """Paths of the definitions whose file name, title or keywords contain any term.

        Later directories win on a name clash, so a file of yours shadows a community one.
        """
        found = {}
        for directory in directories:
            for filepath in sorted(directory.glob("**/*.json")):
                definition = json.loads(filepath.read_text())
                haystack = " ".join(
                    [
                        filepath.stem,
                        definition.get("title", ""),
                        *definition.get("keywords", []),
                        *definition.get("target_public_health_threats", []),
                    ]
                ).lower()
                if any(term in haystack for term in terms):
                    found[filepath.stem] = filepath
        return found

    return (find_definitions,)


@app.cell
def _(mo):
    search_input = mo.ui.text(
        value="arbovirosis, arbovirus, zika",
        label="Search the catalogue",
        full_width=True,
    ).form(bordered=False)
    search_input
    return (search_input,)


@app.cell
def _(find_definitions, get_definition_dirs, json, search_input):
    terms = [
        term.strip().lower()
        for term in (search_input.value or "arbovirosis, arbovirus, zika").split(",")
        if term.strip()
    ]

    repo_definitions = {
        name: json.loads(filepath.read_text())
        for name, filepath in find_definitions(get_definition_dirs(), terms).items()
    }
    return repo_definitions, terms


@app.cell
def _(df, engine, mo, pl, repo_definitions):
    mo.stop(
        not repo_definitions,
        mo.callout(mo.md("No definition matched those terms."), kind="warn"),
    )

    repo_labeled = engine.label(df, repo_definitions)

    repo_summary = pl.DataFrame(
        {
            "definition": list(repo_definitions),
            "location": [
                found.get("location", "") for found in repo_definitions.values()
            ],
            "matches": [repo_labeled[name].sum() for name in repo_definitions],
        }
    ).sort("matches", descending=True)

    repo_summary
    return repo_labeled, repo_summary


@app.cell
def _(plot_monthly, repo_labeled, repo_summary):
    plot_monthly(repo_labeled, repo_summary["definition"].to_list())
    return


@app.cell
def _(mo, repo_summary):
    _empty = repo_summary.filter(repo_summary["matches"] == 0)["definition"].to_list()

    mo.callout(
        mo.md(
            f"""
    **Zero matches for:** {", ".join(f"`{name}`" for name in _empty) or "none"}.

    Those definitions are written in terms of *symptoms* (fever, rash, arthralgia) or
    clinical judgement. This dataset has ICD-10 codes and nothing else, so the engine
    has no column to evaluate them against and skips the criteria. Same syndrome,
    different data source, different definition: that is the problem OSD exists to make explicit.
    """
        ),
        kind="info",
    )
    return


@app.cell
def _(mo, repo_definitions):
    mo.accordion(
        {
            "Definitions used": mo.accordion(
                {name: mo.json(found) for name, found in repo_definitions.items()}
            )
        }
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 7. Your own definitions, next to the catalogue

    A definition you are still drafting, or one specific to your service, does not have
    to be published on GitHub before you can use it. Since `opensyndrome` 0.5.0 the
    library also reads a directory you own: `get_definition_dirs(local_dir=...)` returns
    the community directory followed by yours, and the same search from section 6 covers
    both. Outside a notebook, set `OPENSYNDROME_DEFINITIONS_DIR=./my_definitions` instead
    of passing the argument. To skip the catalogue, and its download, altogether, add
    `OPENSYNDROME_LOCAL_DEFINITIONS_ONLY=1` or pass `local_only=True`.

    The definition below is written to `my_definitions/` next to this notebook. Zika itself
    barely shows up in outpatient billing, but its consequence does: microcephaly (`Q02`) in
    young children, the signal that made Pernambuco declare an emergency in late 2015. No
    community definition covers it, which is exactly when you write your own. It uses the
    `age` mapping from section 2. Edit it and **Submit**: the file is rewritten and
    everything below re-runs.
    """)
    return


@app.cell
def _(mo):
    INITIAL_LOCAL_DEFINITION = """{
      "title": "Microcephaly in young children",
      "scope": "broad",
      "category": "suspected",
      "version": "0.1.0",
      "open_syndrome_version": "1.0.0",
      "published_in": "https://github.com/anapaulagomes/osi-workshop",
      "published_at": "2026-09-02T12:00:00Z",
      "location": "Pernambuco, Brazil",
      "language": "English",
      "organization": "Open Syndrome workshop",
      "definition_type": "syndrome_definition",
      "status": "draft",
      "keywords": ["zika", "microcephaly", "congenital zika syndrome"],
      "target_public_health_threats": ["Zika", "Microcephaly"],
      "human_readable_definition": "Outpatient record coded as microcephaly in a child aged two or younger, a proxy for congenital Zika syndrome.",
      "references": [{"url": "https://icd.who.int/browse10/2019/en#/Q02"}],
      "inclusion_criteria": [
        {
          "type": "criterion",
          "logical_operator": "AND",
          "values": [
            {"type": "diagnosis", "name": "Microcephaly",
             "code": {"system": "ICD-10", "code": "Q02"}},
            {"type": "demographic_criteria", "name": "Aged two or younger",
             "attribute": "age", "operator": "<=", "value": 2}
          ]
        }
      ]
    }
    """

    local_editor = mo.ui.code_editor(value=INITIAL_LOCAL_DEFINITION, language="json").form(
        label="Local definition (JSON)", bordered=True
    )
    local_editor
    return INITIAL_LOCAL_DEFINITION, local_editor


@app.cell
def _(
    INITIAL_LOCAL_DEFINITION,
    Path,
    json,
    jsonschema,
    local_editor,
    mo,
    validate_machine_readable_format,
):
    _raw = local_editor.value if local_editor.value is not None else INITIAL_LOCAL_DEFINITION

    try:
        _local_definition = json.loads(_raw)
    except json.JSONDecodeError as _error:
        mo.stop(True, mo.callout(mo.md(f"**Invalid JSON:** {_error}"), kind="danger"))

    try:
        validate_machine_readable_format(_local_definition)
    except jsonschema.ValidationError as _error:
        mo.stop(
            True,
            mo.callout(
                mo.md(f"**Not written, it does not match the OSD schema:** {_error.message}"),
                kind="warn",
            ),
        )

    # The file name is what the catalogue search reports as the definition's name.
    LOCAL_DIR = ((mo.notebook_dir() or Path.cwd()) / "my_definitions").resolve()
    LOCAL_DIR.mkdir(exist_ok=True)
    local_file = LOCAL_DIR / "microcephaly_young_children.json"
    local_file.write_text(json.dumps(_local_definition, indent=2) + "\n")

    mo.callout(mo.md(f"Written to `{local_file}`."), kind="success")
    return LOCAL_DIR, local_file


@app.cell
def _(LOCAL_DIR, get_definition_dirs, local_file, mo):
    definition_dirs = get_definition_dirs(local_dir=LOCAL_DIR)

    mo.md(
        "Directories the engine reads, in lookup order:\n\n"
        + "\n".join(f"1. `{directory}`" for directory in definition_dirs)
        + f"\n\nThe local one holds `{local_file.name}`."
    )
    return (definition_dirs,)


@app.cell
def _(LOCAL_DIR, definition_dirs, df, engine, find_definitions, json, mo, pl, terms):
    _paths = find_definitions(definition_dirs, terms)
    mo.stop(
        not _paths,
        mo.callout(mo.md("No definition matched those terms."), kind="warn"),
    )

    all_definitions = {name: json.loads(path.read_text()) for name, path in _paths.items()}
    all_labeled = engine.label(df, all_definitions)

    all_summary = pl.DataFrame(
        {
            "definition": list(all_definitions),
            "source": [
                "local" if path.is_relative_to(LOCAL_DIR) else "community"
                for path in _paths.values()
            ],
            "location": [found.get("location", "") for found in all_definitions.values()],
            "matches": [all_labeled[name].sum() for name in all_definitions],
        }
    ).sort("matches", descending=True)

    all_summary
    return all_labeled, all_summary


@app.cell
def _(all_labeled, all_summary, plot_monthly):
    plot_monthly(
        all_labeled,
        all_summary.filter(all_summary["matches"] > 0)["definition"].to_list(),
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            """
    Same search, one more directory. Nothing about the local file is special: drop any
    valid OSD JSON into `my_definitions/` and it shows up here. The curve is the one
    Pernambuco saw: a handful of records a month until late 2015, hundreds a month from
    2016 on. When a definition is ready for other people, open a pull request to
    [OpenSyndrome/definitions](https://github.com/OpenSyndrome/definitions).
    """
        ),
        kind="info",
    )
    return


if __name__ == "__main__":
    app.run()
