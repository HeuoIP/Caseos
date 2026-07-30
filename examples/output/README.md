# Examples Output (DEPRECATED PATH)

The canonical location for AI output JSON is:

    data/analysis/cases/<image_id>.json

The schema is CaseOS_Output_Schema_V3
(canonical per ADR-008). This folder used to hold one V1-shaped
demo (snow_playground_case.json) which has been removed.

If you want to inspect a real Vision output, look at any of:

    data/analysis/cases/0001.json
    data/analysis/cases/0002.json
    data/analysis/cases/sample_playground.json

The folder is kept for the .gitkeep so future exports have a
place to live. New exports should go to
data/analysis/cases/, not here.
