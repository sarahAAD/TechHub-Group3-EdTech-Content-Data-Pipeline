"""Entry point for the full ETL pipeline.

Placeholder only. At the integration stage this will chain together the
functions refactored into src/ (extract -> profile/clean -> schema validate
-> join/transform) so the whole pipeline can be run end-to-end starting from
an empty data/ folder.
"""


def main() -> None:
    raise NotImplementedError("Pipeline will be assembled at the integration stage.")


if __name__ == "__main__":
    main()
