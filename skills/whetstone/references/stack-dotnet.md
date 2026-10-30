# Stack notes: .NET

Add these stack-specific notes to core references for C#/.NET, ASP.NET Core and Entity Framework Core.

## Contents

- [Use HttpClient correctly](#use-httpclient-correctly)
- [Add resilience once, deliberately](#add-resilience-once-deliberately)
- [Return problem details](#return-problem-details)
- [Apply EF Core migrations safely](#apply-ef-core-migrations-safely)
- [Audit NuGet packages](#audit-nuget-packages)
- [Authenticate to Azure deterministically](#authenticate-to-azure-deterministically)
- [Other .NET traps](#other-net-traps)
- [Sources](#sources)

## Use HttpClient correctly

1. Do not create and dispose an `HttpClient` per request. Each instance owns a connection pool, and disposed connections linger in TIME-WAIT, so high request rates can exhaust ports.
2. Use either a long-lived client with `SocketsHttpHandler.PooledConnectionLifetime` set (so DNS changes are picked up), or `IHttpClientFactory` with typed clients. Avoid the factory when the app depends on cookies, because pooled handlers share cookie containers.
3. Set timeouts deliberately. The default `HttpClient.Timeout` is 100 seconds, which is far too long for most dependencies on a request path.
4. Pass a `CancellationToken` from the incoming request through every asynchronous call, so abandoned requests stop consuming resources.

## Add resilience once, deliberately

`Microsoft.Extensions.Http.Resilience` supplies `AddStandardResilienceHandler`, a preconfigured `HttpClient` pipeline with these documented defaults:

| Strategy (outermost first) | Default |
|---|---|
| Rate limiter | 1,000 concurrent permits, no queue |
| Total timeout | 30 seconds, including retries |
| Retry | 3 retries, exponential backoff with jitter, 2-second base delay |
| Circuit breaker | Opens at a 10 percent failure ratio over 30 seconds with at least 100 requests; breaks for 5 seconds |
| Attempt timeout | 10 seconds per attempt |

1. Retries apply to all HTTP methods by default. Call `options.Retry.DisableForUnsafeHttpMethods()` unless every unsafe operation is idempotent or carries an idempotency key (see [api-design.md](api-design.md)).
2. Tune the timeouts to the dependency's measured latency rather than accepting the defaults blindly (see [reliability-performance.md](reliability-performance.md)).
3. Add only one resilience handler per client. Stacked handlers multiply retries.

## Return problem details

1. Call `builder.Services.AddProblemDetails()`, then `app.UseExceptionHandler()` and `app.UseStatusCodePages()`, so unhandled exceptions and empty error responses become RFC 9457 problem details.
2. Keep the developer exception page to the Development environment only, so stack traces never reach production clients.
3. Return `Results.Problem(...)` or `TypedResults.Problem(...)` for expected failures, with a stable `type` URI per problem kind.

## Apply EF Core migrations safely

Microsoft recommends migration bundles for automated production deployments, SQL scripts for SQL review, and startup migration only as a last resort.

1. Generate a migration bundle, or an idempotent SQL script with `dotnet ef migrations script --idempotent`, and apply it as a separate, logged release step with a credential that has schema rights. The application's runtime identity should not need them.
2. Review the generated SQL for every migration, especially renames, column type changes and anything that rewrites or locks a large table (see [data-and-privacy.md](data-and-privacy.md)).
3. Do not call `Database.Migrate()` or `MigrateAsync()` on start-up in production, and never call `EnsureCreated()` in an application that uses migrations.
4. Keep migrations backward compatible with the previous application version, so a code rollback does not need a schema rollback.

## Audit NuGet packages

NuGet Audit defaults on during restore: vulnerability warnings NU1901 (low) through NU1904 (critical). Targets `net10.0`+ also audit transitive packages (`NuGetAuditMode=all` by default).

1. Keep auditing on, and set `NuGetAuditMode` to `all` for older target frameworks.
2. Treat high and critical findings as errors with `<WarningsAsErrors>$(WarningsAsErrors);NU1903;NU1904</WarningsAsErrors>`, and triage the rest (see [supply-chain.md](supply-chain.md)).
3. Use central package management and a lock file (`packages.lock.json` with locked-mode restore in CI) so builds are reproducible.

## Authenticate to Azure deterministically

`DefaultAzureCredential` tries multiple credentials, useful in development. Microsoft recommends a specific deployed credential such as `ManagedIdentityCredential`: chains are slower, harder to debug and sensitive to environment changes. If retained, set `AZURE_TOKEN_CREDENTIALS=prod` to exclude developer-tool credentials. See [stack-azure.md](stack-azure.md).

## Other .NET traps

- Enable nullable reference types in new projects and treat nullable warnings as errors, rather than suppressing them with `!`.
- Avoid `async void` except for event handlers, and never block on asynchronous code with `.Result` or `.Wait()` in request paths; both can deadlock or exhaust the thread pool.
- Never use `BinaryFormatter`, and keep Json.NET's `TypeNameHandling` at `None`; OWASP's deserialisation guidance explains why.
- Use parameterised queries or EF Core LINQ; treat `FromSqlRaw` and `ExecuteSqlRaw` with string concatenation as an injection risk and prefer their interpolated, parameterising counterparts.
- Use property-based testing with FsCheck and mutation testing with Stryker.NET for critical logic (see [testing.md](testing.md)).

## Sources

- Microsoft, [HttpClient.Timeout](https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclient.timeout) and [HttpClient guidelines](https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/http/httpclient-guidelines).
- Microsoft's documentation on [resilient HTTP apps](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience) describes the standard resilience handler and its defaults.
- Microsoft's ASP.NET Core documentation on [handling errors in APIs](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling-api) covers `AddProblemDetails`.
- Microsoft, [Applying migrations](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying), compares bundles, SQL scripts and runtime migration.
- Microsoft, [Auditing package dependencies for security vulnerabilities](https://learn.microsoft.com/en-us/nuget/concepts/auditing-packages).
- Microsoft, [Credential chains in the Azure Identity library](https://learn.microsoft.com/en-us/dotnet/azure/sdk/authentication/credential-chains).
- OWASP, [Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html); [FsCheck](https://fscheck.github.io/FsCheck/); [Stryker](https://stryker-mutator.io/).
