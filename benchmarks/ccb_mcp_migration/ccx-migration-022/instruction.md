# Kafka Deprecated Streams/Producer API Migration Inventory

## Your Task

Find all Java source files in `apache/kafka` under the `streams/src/main/java/` and `clients/src/main/java/` directories that contain `@Deprecated` annotations on fields or methods related to producer and streams configuration or exception handling. Specifically:

1. Find deprecated configuration constants in `StreamsConfig.java` (e.g., `DEFAULT_PRODUCTION_EXCEPTION_HANDLER_CLASS_CONFIG`, `DEFAULT_DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG`, `CACHE_MAX_BYTES_BUFFERING_CONFIG`, `DEFAULT_DSL_STORE_CONFIG`).
2. Find deprecated methods in the streams exception handler interfaces and their implementations: `ProductionExceptionHandler`, `DeserializationExceptionHandler`, `DefaultProductionExceptionHandler`, `LogAndFailExceptionHandler`, `LogAndContinueExceptionHandler`.
3. Find any deprecated fields in `TopicConfig.java` (under `clients/src/main/java/`).

For each file, report the repo, file path, the deprecated symbol name, and what it was deprecated in favor of (the replacement API).

## Context

You are working on a migration inventory task to catalog deprecated APIs that must be updated before upgrading to the next Kafka major version. The Kafka 4.x codebase contains several deprecated configuration constants and exception handler methods that have newer replacements.

## Available Resources

The local `/workspace/` directory contains: sg-evals/kafka--0753c489.

**Note:** Additional repositories are accessible via Sourcegraph MCP tools:
- `sg-evals/kafka--0753c489` (apache/kafka)

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.java"}
  ],
  "symbols": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.java", "symbol": "SymbolName"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

Include only the fields relevant to this task. Your answer is evaluated against a closed-world oracle -- completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant files containing @Deprecated annotations?
- **Symbol recall**: Did you identify all deprecated fields and methods?
- **Keyword presence**: Does your answer mention the key deprecated symbols and their replacements?
