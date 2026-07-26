# CaseOS scripts

Helper scripts for running CaseOS from the command line.

## run_vision.py

End-to-end image?JSON pipeline.

```bash
python backend/scripts/run_vision.py path/to/playground.png
```

Pipeline:

1. Receive an image path (or pick the first PNG inside ``data/images/``).
2. Use the registered ``VisionAnalyzer`` (currently ``QwenVisionAnalyzer``).
3. Load ``backend/prompts/vision_prompt_v1.md`` automatically.
4. Call ``Qwen3.7-Plus`` via DashScope.
5. Persist the JSON to ``data/analysis/<image>.json``.

Requirements:

- ``backend/.env`` containing ``QWEN_API_KEY=...`` (copy from
  ``backend/.env.example`` if you do not have one).
- ``python-dotenv`` and the system ``urllib`` request library (already in
  Python 3.12+) installed.
