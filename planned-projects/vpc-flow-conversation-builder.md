# Future project: VPC Flow Logs conversation builder

Recorded: October 22, 2026
Status: Backlog idea; implementation deferred.

## Purpose

Turn directional VPC Flow Log records into bidirectional conversation summaries that make network investigations easier. The motivating question is: who communicated with whom, over what period, and how much data moved in each direction?

## Initial scope

- Start with the existing EC2-to-Internet learning lab and a small saved dataset.
- Match reverse-direction records using protocol and paired IP/port endpoints, retaining the observed ENI and account context.
- Preserve ephemeral ports when distinguishing connections; offer broader client-to-service summaries separately.
- Show first/last observed times, packets and bytes in each direction, and whether both directions were observed.
- Keep one-sided traffic visible and retain references to the source records.
- Define a time-window or inactivity-timeout rule explicitly; call the output derived conversations rather than exact reconstructed sessions.

## Accuracy challenges to explore

- Aggregation intervals, approximate timestamps, missing records, and late arrivals.
- Reused ports, overlapping activity, and long-lived connections.
- Inferring initiator/client/server roles without assuming that lower port numbers prove those roles.
- Duplicate observations when logging multiple interfaces, and address changes across NAT or other network paths.
- Distinguishing observed duration from actual connection duration and network acceptance from application success.

## Implementation direction to evaluate later

Start with a query-based prototype using Logs Insights or Athena before deciding whether Python processing is needed. Use boto3 for AWS query submission and result retrieval. Consider stateful Python processing if inactivity-based grouping across aggregation intervals becomes necessary. S3 and Athena are options for retained historical data; no additional infrastructure is needed to record this idea.

## Useful validation

Compare summaries against a few controlled connections and, if captured, packet traces. Include a missing reverse direction, a connection spanning aggregation intervals, and port reuse. Preserve packet/byte totals without double counting and make uncertain matches visible.

## Learning value

Practice converting noisy security telemetry into trustworthy investigative evidence: data modeling, correlation, time handling, provenance, and appropriate remote versus local processing. Detection rules and a production pipeline can wait until the conversation view is useful and validated.
