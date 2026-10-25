# Retrieval and evaluations

Read this when you build retrieval-augmented generation (RAG) over documents, tickets or knowledge bases, and whenever you need to measure the quality of a model-backed feature. Model risks, tools and agents are covered in [ai-features.md](ai-features.md). Plan the work with [the AI evaluation plan template](../templates/ai-eval-plan.md).

## Contents

- [Define what good means first](#define-what-good-means-first)
- [Ingest documents with permissions and provenance](#ingest-documents-with-permissions-and-provenance)
- [Enforce permissions at query time](#enforce-permissions-at-query-time)
- [Retrieve well](#retrieve-well)
- [Generate grounded answers with citations](#generate-grounded-answers-with-citations)
- [Keep the index fresh and complete](#keep-the-index-fresh-and-complete)
- [Build the evaluation set from real data](#build-the-evaluation-set-from-real-data)
- [Choose graders you can trust](#choose-graders-you-can-trust)
- [Measure retrieval and generation separately](#measure-retrieval-and-generation-separately)
- [Run evaluations as regression tests](#run-evaluations-as-regression-tests)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Define what good means first

Anthropic's guidance on building evaluations asks for success criteria that are specific, measurable, achievable and relevant. "Answers questions well" is not a criterion; "at least 90 percent of answers on the evaluation set are fully supported by the cited documents, and the correct document is in the top five results for 95 percent of questions" is.

Apply it:

1. Write criteria for answer quality, grounding, refusal behaviour, latency, cost per question and privacy before you build.
2. Record a baseline (the current system, a simple keyword search, or a human answer) so improvements are measured, not felt.

## Ingest documents with permissions and provenance

Apply it:

1. Capture, for every document, its source system, stable identifier, version or modification time, owner, classification and the list of principals (users or groups) allowed to read it.
2. Split documents along their structure (headings, sections, list items) rather than at arbitrary character counts, keep the heading path with each chunk, and keep chunks small enough to be specific but large enough to stand alone.
3. Deduplicate near-identical documents, and decide which version wins when copies disagree.
4. Scan for secrets and personal data during ingestion, and exclude or mask what should not be retrievable.
5. Treat document content as untrusted. A document can contain instructions aimed at the model, so it must never be able to change the system's behaviour beyond supplying facts.

## Enforce permissions at query time

The most damaging RAG failure is answering a user with content they are not allowed to see. Prompts cannot enforce access control.

Apply it:

1. Filter retrieval by the caller's identities on every query, inside the search request, before ranking and generation. Search services do not know who the caller is; your application must pass the caller's user and group identifiers into the filter each time.
2. Resolve group memberships from the identity provider at query time or with a short cache, so revoked access takes effect quickly.
3. Keep tenants in separate indexes or enforce a mandatory tenant filter in one place in code.
4. Do not return permission fields or hidden metadata in results. Hiding a field from responses is not the same as enforcing access.
5. Include the permission scope in any cache key for retrieved results or generated answers.
6. Test with at least two users who have different permissions, and assert that each one's answers never cite the other's restricted documents.

## Retrieve well

Apply it:

1. Start with hybrid retrieval (keyword and vector search combined), because vector search alone misses exact terms such as error codes, product names and identifiers.
2. Add a reranking step over the top candidates when relevance matters more than a few tens of milliseconds.
3. Use metadata filters (product, version, date, language) where the question implies them.
4. Tune the number of chunks passed to the model with the evaluation set: too few misses facts, too many dilutes them and raises cost.
5. Measure retrieval on its own (see below) before blaming the prompt.

## Generate grounded answers with citations

Apply it:

1. Instruct the model to answer only from the supplied context, and to say plainly when the context does not contain the answer.
2. Return citations that link to the exact source document and section, and show users enough of the source to check the claim.
3. Delimit retrieved content as data, and keep the instructions outside it.
4. Validate and encode the output before rendering it, as described in [ai-features.md](ai-features.md).
5. Prefer "I could not find this in the documents" over a fluent guess. A wrong answer with a citation is more harmful than no answer.

## Keep the index fresh and complete

Apply it:

1. Sync incrementally from each source, and monitor the lag between a source change and its appearance in the index.
2. Propagate deletions and permission changes as reliably as additions. A deleted or restricted document that remains retrievable is a data leak (see [data-and-privacy.md](data-and-privacy.md)).
3. Version the index together with the embedding model and chunking settings. Changing either requires re-embedding into a new index, evaluating it, then switching over.

## Build the evaluation set from real data

Hamel Husain's advice on evaluations is to look at real traces relentlessly: error analysis on actual data finds the failure modes that matter.

Apply it:

1. Collect real or realistic questions, and label the documents that answer them and an acceptable answer.
2. Include hard cases: questions with no answer in the corpus, ambiguous questions, questions that need two documents, questions about restricted documents asked by users without access, outdated documents, and prompt injection planted in a document.
3. Favour volume: many automatically graded cases beat a few hand-graded ones. Start with tens of cases, grow to hundreds as failures are found.
4. Keep a held-out portion that is not used while tuning prompts, to detect overfitting.
5. Add every production failure you find to the set, so it can never silently return.

## Choose graders you can trust

| Grader | Use for | Watch out for |
|---|---|---|
| Code (exact match, regular expression, schema validation, citation presence) | Anything objectively checkable | Too strict for free text |
| Model as judge with a written rubric | Groundedness, relevance, tone, completeness | Must be validated against human labels |
| Human review | Calibrating judges, sampling production, high-stakes cases | Slow and expensive; use sparingly |

Apply it:

1. Prefer code-based checks wherever they work.
2. For a model judge, write a specific rubric, ask for a binary or small-scale verdict, and use a different model from the one being graded where possible.
3. Measure the judge's agreement with human labels on a sample, using precision and recall rather than raw agreement when classes are imbalanced, and re-check periodically.

## Measure retrieval and generation separately

| Stage | Metric | Question it answers |
|---|---|---|
| Retrieval | Recall at k | Is a document that answers the question among the top k results? |
| Retrieval | Context relevance | Are the retrieved chunks related to the question? |
| Generation | Groundedness | Is every claim in the answer supported by the retrieved context? |
| Generation | Answer relevance | Does the answer address the question that was asked? |
| Whole system | Correct refusal rate | Does it decline when the corpus has no answer or the user lacks access? |

Context relevance, groundedness and answer relevance together form what TruLens calls the RAG triad. Separating the stages tells you whether to fix retrieval or generation.

## Run evaluations as regression tests

Apply it:

1. Run the fast, code-graded evaluations in CI on every change to prompts, models, retrieval settings, chunking or tools, and fail the build when a key metric drops below its threshold.
2. Run the slower, model-graded evaluations before release, and compare them with the previous version, case by case.
3. In production, sample traces for review, collect user feedback, and watch refusal rates, citation clicks and cost per answer.
4. Use A/B tests only for mature products with enough traffic, after offline evaluations pass.

Check:

- [ ] Permission filtering happens inside retrieval on every query, and a two-user test proves it.
- [ ] Answers cite their sources, and the system refuses when the context has no answer.
- [ ] Deletions and permission changes reach the index within a measured time.
- [ ] An evaluation set with hard cases exists, and it runs on every relevant change.

## Failure modes

- An intern's question retrieves a confidential salary spreadsheet, because the index had no permission filter and the prompt "told" the model not to share it.
- A document deleted months ago still appears in answers, because the sync only handled additions.
- The team tunes prompts by trying a few questions by hand, and every change fixes one case and breaks two others.
- A model judge rates every answer as good, and nobody ever checked it against human labels.
- A planted sentence in a wiki page instructs the assistant to send users to a phishing link, and the assistant complies.

## Sources

- Anthropic, [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests), covers success criteria, evaluation design and grading methods.
- Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/), describes levels of evaluation, error analysis and aligning model judges with humans.
- TruLens, [The RAG Triad](https://www.trulens.org/getting_started/core_concepts/rag_triad/), defines context relevance, groundedness and answer relevance.
- Microsoft, [Security filters for trimming results in Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search), shows the query-time permission filter pattern and why hiding a field is not access control.
