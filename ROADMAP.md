# Roadmap

Traxy stays intentionally small. Work is prioritized when it supports a real
maintainer or deployment-verification use case.

## Near term

- Add opt-in request headers sourced from environment variables without writing
  secret values to configuration files or output.
- Add retry policies with bounded backoff for transient endpoint failures.
- Publish reusable GitHub Actions documentation and copy-paste examples.

## Later, with demonstrated demand

- Add response-time thresholds.
- Add a stable plugin boundary for custom assertions.
- Publish signed release provenance.

Large dashboards, hosted alerting, and a persistent control plane are outside
the current scope.
