# Stack notes: Azure

Add these platform-specific notes to core references for Azure deployments or service calls.

## Contents

- [Authenticate with managed identities](#authenticate-with-managed-identities)
- [Preview infrastructure changes](#preview-infrastructure-changes)
- [Instrument with OpenTelemetry](#instrument-with-opentelemetry)
- [Choose model deployments for data residency](#choose-model-deployments-for-data-residency)
- [Filter Azure AI Search results by permission](#filter-azure-ai-search-results-by-permission)
- [Use Prompt Shields as one layer](#use-prompt-shields-as-one-layer)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Authenticate with managed identities

1. Use managed identities and Microsoft Entra ID authentication for service-to-service access instead of connection strings, account keys or client secrets. Turn off key-based (local) authentication on services that support Entra ID once nothing depends on keys.
2. Grant role assignments at the narrowest scope that works (a single resource rather than a subscription), with the least-privileged built-in role.
3. Use `DefaultAzureCredential` for local development only. In deployed applications, Microsoft recommends replacing it with a specific credential such as `ManagedIdentityCredential`; if you keep it, set `AZURE_TOKEN_CREDENTIALS=prod` to exclude developer-tool credentials.
4. Keep any remaining secrets in Key Vault, accessed by managed identity, with rotation planned. Never place secrets in source, pipeline variables shown in logs, or plain-text application settings checked into the repository.
5. Deploy from pipelines with workload identity federation (OIDC) rather than stored service principal secrets (see [supply-chain.md](supply-chain.md)).

## Preview infrastructure changes

1. Run Bicep `what-if` (for example `az deployment group what-if`) before every deployment, and read every delete, replace and modify operation in the output.
2. Include the what-if output, or a summary of it, in the PR or release record for T2 and T3 changes.
3. Use deployment modes that cannot silently delete resources unless deletion is intended and reviewed.

## Instrument with OpenTelemetry

Microsoft recommends the Microsoft OpenTelemetry Distro for new .NET, Node.js and Python Application Insights integrations; Java uses Azure Monitor OpenTelemetry Distro. Existing Azure Monitor distro users need not migrate.

1. Use one distro per application; do not initialise both.
2. Initialise telemetry before the application starts handling work, and supply the Application Insights connection string from configuration, not source code.
3. Follow the general rules in [observability.md](observability.md): set `service.name`, keep personal data out of telemetry, and propagate trace context.

## Choose model deployments for data residency

Microsoft Foundry (formerly Azure AI Foundry) deployment types change inference location; stored data stays in the resource's geography:

| Deployment type family | Where prompts and responses are processed |
|---|---|
| Global (Standard, Provisioned, Batch) | Any Azure region |
| Data Zone (Standard, Provisioned, Batch) | Within the Microsoft-defined data zone (United States, European Union or Asia-Pacific) |
| Standard and Regional Provisioned | Within the chosen Azure geography |
| Developer | Any region, with no data residency guarantee; for evaluating fine-tuned models only |

1. Check the project's data residency requirements before choosing a deployment type, and record the choice in a decision record when personal or regulated data is involved (see [data-and-privacy.md](data-and-privacy.md)).
2. Do not switch to a Global deployment for capacity or price without checking that cross-region processing is allowed.

## Filter Azure AI Search results by permission

Azure AI Search security filters do not authenticate users or check permissions; pass caller identities on every query.

1. Store the principals allowed to read each document in a filterable `Collection(Edm.String)` field, and keep it non-retrievable.
2. Add a filter such as `group_ids/any(g: search.in(g, 'id1, id2'))` with the caller's user and group identifiers to every query, built in one shared function.
3. Remember that marking a field non-retrievable only hides it from results; it is not access control.
4. Where the service's built-in document-level access control fits your scenario, evaluate it as an alternative, and test either approach with users who have different permissions (see [rag-and-evals.md](rag-and-evals.md)).

## Use Prompt Shields as one layer

Azure AI Content Safety Prompt Shields detect direct jailbreaks and instructions hidden in documents, emails or web pages.

1. Turn on document attack detection for retrieval and agent scenarios. User prompt attack detection is on by default in Foundry, but document attack detection is off by default.
2. When you call the standalone Content Safety API, act on the result in your code; the API only reports whether an attack was detected.
3. Treat a "no attack" result as no guarantee. Prompt Shields only detect manipulation attempts, are trained mainly on English, and do not replace the deterministic controls in [ai-features.md](ai-features.md).

## Failure modes

- Storage keys copied across application settings become impossible to rotate without outages.
- `DefaultAzureCredential` uses a developer's Azure CLI login on a build agent, deploying as the wrong identity.
- Unread Bicep what-if output hides a property change that recreates the database.
- Quota-driven Global deployments process EU personal data outside its data zone.
- Filtering only one of two query paths exposes all documents.

## Sources

- Microsoft's documentation on [credential chains in the Azure Identity library](https://learn.microsoft.com/en-us/dotnet/azure/sdk/authentication/credential-chains) recommends specific credentials in production.
- Microsoft's documentation on [Bicep what-if](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-what-if) describes previewing deployments.
- Microsoft's guide to [enabling OpenTelemetry for Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable) describes the distros.
- Microsoft's page on [Foundry Models deployment types](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/deployment-types) lists processing locations.
- Microsoft, [Security filters for trimming results in Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search), describes the query-time filter pattern.
- Microsoft's page on [Prompt Shields](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection) describes detection of user prompt and document attacks and its limitations.
