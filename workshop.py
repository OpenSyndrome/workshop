# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jsonschema==4.26.0",
#     "marimo",
#     "opensyndrome==0.4.0",
#     "plotly==6.9.0",
#     "polars==1.43.2",
#     "pyyaml==6.0.3",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium", app_title="Open Syndrome Workshop")


@app.cell
def _():
    import json
    from pathlib import Path

    import jsonschema
    import marimo as mo
    import plotly.graph_objects as go
    import polars as pl
    import yaml
    from opensyndrome.artifacts import get_definition_dir
    from opensyndrome.filter import OSDEngine, load_profile
    from opensyndrome.validators import validate_machine_readable_format

    return (
        OSDEngine,
        Path,
        get_definition_dir,
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
    `get_definition_dir()` downloads them once to `~/.open_syndrome/`. Same data, same
    mapping, same engine — only the definitions change, and they were written by other
    people for other places.
    """)
    return


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
def _(get_definition_dir, json, search_input):
    terms = [
        term.strip().lower()
        for term in (search_input.value or "arbovirosis, arbovirus, zika").split(",")
        if term.strip()
    ]

    repo_definitions = {}
    for _filepath in sorted(get_definition_dir().glob("**/*.json")):
        _found = json.loads(_filepath.read_text())
        _haystack = " ".join(
            [
                _filepath.stem,
                _found.get("title", ""),
                *_found.get("keywords", []),
                *_found.get("target_public_health_threats", []),
            ]
        ).lower()
        if any(term in _haystack for term in terms):
            repo_definitions[_filepath.stem] = _found
    return (repo_definitions,)


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


if __name__ == "__main__":
    app.run()
