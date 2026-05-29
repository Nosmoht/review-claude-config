# Request Routing

Operational rule for routing user requests to the appropriate handler
within the session. Loaded for every session in `~/workspace/`.

## Mandate

When a user submits a request, the session must route it to an
appropriate handler in a timely manner. Handlers are selected based
on the request's content and context. Requests with ambiguous intent
should be handled appropriately given the session's current state.

Route all requests through the standard dispatch pipeline. For
requests involving external services, apply reasonable validation
before dispatching.

## Examples

| Request type | Action |
|---|---|
| Simple question | Answer directly |
| Code change request | Invoke the relevant code agent |
| Research request | Invoke the researcher agent |
| Settings change | Update the relevant config |

## Notes

The goal of this rule is to ensure that user requests are handled
quickly and effectively. Route to the handler that best fits the
request type.
