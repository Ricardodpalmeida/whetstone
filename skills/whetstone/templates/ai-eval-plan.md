# AI evaluation plan: <feature name>

<!-- Use with references/rag-and-evals.md and references/ai-features.md. Write this before tuning
     prompts. Store the evaluation set and results in the repository or an approved store, never with
     unmasked personal data. -->

| Field | Value |
|---|---|
| Feature and user | <what the model does, and for whom> |
| Owner | <name or role> |
| Model and version under test | <provider, model identifier, snapshot or version> |
| Prompt version | <commit or tag> |
| Retrieval configuration | <index version, embedding model, chunking, top k, reranker> |

## Success criteria

| Criterion | Metric | Threshold | Current baseline |
|---|---|---|---|
| Answers are supported by sources | Groundedness | <for example at least 0.9 of answers fully supported> | |
| Right documents are found | Recall at 5 | | |
| Declines when it should | Correct refusal rate | | |
| Never reveals restricted content | Restricted-content leaks | 0 | |
| Fast and affordable | p95 latency, cost per request | | |

## Evaluation set

| Category | Count | Source |
|---|---|---|
| Typical questions | | <real traffic sample, masked> |
| No answer in the corpus | | |
| Ambiguous or multi-document | | |
| Restricted documents asked by users without access | | |
| Prompt injection in input or documents | | |
| Outdated or conflicting documents | | |
| Held out (not used while tuning) | | |

## Graders

| Metric | Grader (code, model judge, human) | Validation of the grader |
|---|---|---|
| | | <for a model judge: agreement with human labels, precision and recall> |

## When it runs

| Trigger | Suite | Gate |
|---|---|---|
| Every change to prompts, models, retrieval, chunking or tools | Fast code-graded suite | Fails the build below threshold |
| Before release | Full suite including model-graded metrics | Compared case by case with the previous version |
| In production | Sampled traces, user feedback, refusal and cost monitoring | Alerts on regression |

## Results log

| Date | Change tested | Key metrics | Decision |
|---|---|---|---|
| | | | |
