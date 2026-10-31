# AI evaluation plan: feature name

Optional. Write it before tuning prompts. Keep the evaluation set and results with the project, without unmasked personal data.

| Field | Value |
|---|---|
| Feature and users | What the model does, and for whom |
| Model and version under test | Provider, model identifier and version |
| Prompt and retrieval version | Commit or tag, index and chunking settings |

## Metrics and thresholds

| Metric | Threshold | Current baseline |
|---|---|---|
| Recall at k | | |
| Groundedness | | |
| Correct refusal rate | | |
| Restricted-content leaks | 0 | |
| p95 latency and cost per request | | |

## Evaluation set

| Category | Count | Source |
|---|---|---|
| Typical tasks | | |
| No answer in the sources | | |
| Caller without access | | |
| Injected instructions in input or documents | | |
| Failed tool or dependency | | |
| Held out from tuning | | |

## When it runs

Every change to the prompt, model, retrieval settings, chunking or tools runs the fast suite, and a drop below a threshold fails the check. Before release, run the full suite and compare it case by case with the current version.

## Results

| Date | Change tested | Key metrics | Decision |
|---|---|---|---|
| | | | |
