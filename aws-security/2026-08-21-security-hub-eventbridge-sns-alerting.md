# Security Hub EventBridge and SNS Alerting Lab

**Date:** August 21, 2026  
**Region:** `us-east-1`  
**Lab type:** Guided, hands-on  
**Privacy note:** Email addresses, account IDs, ARNs, finding IDs, instance IDs, and other unique resource identifiers are omitted.

## Objective

Build and verify this cloud-alerting path:

```text
GuardDuty finding
        ↓
Security Hub imports and normalizes it
        ↓
EventBridge matches selected finding fields
        ↓
SNS publishes the event
        ↓
Confirmed email subscriber receives it
```

The lab separated four concepts:

- **Finding:** a security check or detection record.
- **Event:** a new or updated finding delivered to EventBridge.
- **Rule:** matching logic that decides which events to route.
- **Notification:** the message delivered through SNS.

## SNS setup and independent test

A Standard SNS topic named `security-lab-alerts` was created.

An email subscription was added and confirmed. During setup, the unsubscribe link was selected, causing the subscription ID to display `Deleted`. The deleted row was a stale console representation of a subscription that no longer existed. A new subscription was created and confirmed correctly.

Before connecting Security Hub, SNS was tested independently:

- Subject: `Security lab test`
- Body: `SNS delivery is working.`
- Result: email arrived successfully.

This isolated the notification layer before adding EventBridge.

## Initial EventBridge rule

An active EventBridge rule named `security-hub-to-sns` was created on the default event bus.

Initial event pattern:

```json
{
  "source": ["aws.securityhub"],
  "detail-type": ["Security Hub Findings - Imported"],
  "detail": {
    "findings": {
      "Severity": {
        "Label": ["CRITICAL"]
      }
    }
  }
}
```

Target:

- AWS service: Amazon SNS
- Topic: `security-lab-alerts`
- Execution role: default role created for the rule
- Retry policy: defaults
- Dead-letter queue: none for this short lab

In production, a dead-letter queue can preserve events that could not be delivered to the target.

## Why GuardDuty required no direct EventBridge connection

GuardDuty was already connected to Security Hub. Therefore, EventBridge watched Security Hub rather than GuardDuty directly:

```text
GuardDuty
→ Security Hub
→ EventBridge
→ SNS
```

This design allows one routing layer to handle findings from GuardDuty, Security Hub controls, and other integrated products.

## Broad-filter test

GuardDuty sample findings were generated after the rule became active.

Observed result:

- Approximately eight email notifications arrived.
- Each represented a Critical Security Hub finding event matching the rule.

This proved end-to-end delivery, but it also demonstrated that a severity-only rule can create excessive notifications.

## Narrowing the event pattern

One received event contained this normalized finding type:

```text
TTPs/AttackSequence:EC2/CompromisedInstanceGroup
```

The rule was updated to require both Critical severity and that exact type:

```json
{
  "source": ["aws.securityhub"],
  "detail-type": ["Security Hub Findings - Imported"],
  "detail": {
    "findings": {
      "Severity": {
        "Label": ["CRITICAL"]
      },
      "Types": [
        "TTPs/AttackSequence:EC2/CompromisedInstanceGroup"
      ]
    }
  }
}
```

The matching logic became:

```text
Severity = CRITICAL
AND
Types contains TTPs/AttackSequence:EC2/CompromisedInstanceGroup
```

## Narrow-filter test

GuardDuty samples were generated again.

Observed result:

- Three new emails arrived.
- All three had the selected finding type.
- The three finding IDs were different.

Therefore, these were three distinct findings of the same type—not duplicate delivery of one finding.

Important lesson:

> An EventBridge rule selects every matching event. It does not automatically deduplicate, aggregate, or limit notifications to one email.

The filter reduced the notification count from approximately eight to three, but further aggregation or suppression would require additional design.

## EventBridge monitoring evidence

The rule's Monitoring view showed:

| Metric | Observed value | Meaning |
|---|---:|---|
| Matched events | 11 | Eight broad matches plus three narrow matches |
| Invocations | 11 | SNS was invoked once per matched event |
| Failed invocations | No data | No observed delivery failures were recorded |

The exact agreement between matched events and invocations confirmed that every matched test event reached the SNS target invocation stage.

## Finding terminology: Security Hub and OpenSearch

The term **finding** is similar in both systems but does not mean the records share the same format.

- **OpenSearch Security Analytics:** a detector rule matched a log event and produced a finding.
- **Security Hub:** a security control or integrated product produced a security-related record, normalized into ASFF.

In both systems, a finding means something matched security logic and requires evaluation. It is not automatically a confirmed incident.

OpenSearch can apply alert conditions to findings and send notifications. In this lab, EventBridge applied conditions to Security Hub finding events and SNS delivered notifications.

## AWS-managed Inspector rule

An EventBridge rule beginning with `DO-NOT-DELETE` appeared during inspection.

Its owner was:

```text
inspector2.amazonaws.com
```

This proved it was an Amazon Inspector service-managed rule, not a lab resource or attacker-created rule. It was correctly left unchanged.

General rule:

> Do not manually delete service-managed resources. Disable the parent service or scan type through its own console if it is no longer wanted.

## Cleanup

Completed:

- Disabled the lab EventBridge rule.
- Deleted `security-hub-to-sns`.
- Deleted SNS topic `security-lab-alerts`.
- Deleting the topic also removed its email subscription.
- Preserved the Inspector-managed `DO-NOT-DELETE` rule.

No lab SNS topic or custom EventBridge rule remains.

## Questions and answers

### What does SNS do?

SNS is a message-distribution service. A publisher sends a message to a topic, and the topic delivers it to subscribed destinations such as email.

### Why test SNS before adding EventBridge?

It isolates delivery. If the direct SNS test fails, the issue is in SNS or the subscription—not Security Hub or EventBridge.

### What did `ID: Deleted` mean?

The subscription no longer existed. The console was temporarily displaying a deleted subscription row instead of a live subscription ARN.

### Is GuardDuty automatically linked?

GuardDuty was already connected to Security Hub in this account. EventBridge watched Security Hub events, not GuardDuty directly.

### Why did the first test send many emails?

The rule selected every Critical Security Hub finding. GuardDuty generated multiple Critical sample findings, and each produced a matching event.

### Why did the narrow filter still send three emails?

Three separate findings had the same Critical severity and selected type. Filtering by type does not impose a one-message limit.

### Does one finding always produce one event forever?

No. New findings and updates can generate events. EventBridge evaluates events, not a permanent list of unique incidents.

### What is the difference between `Title`, `Types`, and a resource type?

- `Title`: human-readable description.
- `Types`: normalized security classification.
- Resource type: kind of affected asset, such as an instance, stack, or cluster.

### Is a Security Hub finding like an OpenSearch finding?

Conceptually yes: both represent security logic matching something of interest. Their schemas, data sources, and processing paths differ.

### What does `NOTIFIED` mean in Security Hub?

It is a workflow label. It does not send email. EventBridge plus a target such as SNS performs the actual notification.

### Should `DO-NOT-DELETE` rules be removed?

No. First identify the owning service. The observed rule belonged to Amazon Inspector and was left intact.

### What does `Failed invocations: No data` mean?

No failure datapoints were observed for the selected period. It is not necessarily a separately recorded numeric zero.

## Key takeaways

1. A finding, event, rule match, invocation, and delivered email are separate stages.
2. Testing one component at a time makes troubleshooting easier.
3. Security Hub provides a central event source for findings from multiple products.
4. Severity-only routing is often too broad.
5. Multiple distinct findings can legitimately share one normalized type.
6. EventBridge filtering is not deduplication or aggregation.
7. Monitoring metrics should reconcile with observed notification counts.
8. Workflow status does not itself deliver notifications.
9. Service-managed resources should be managed through their owning service.
10. Cleanup must remove both routing rules and notification destinations.

## References

- [Configuring EventBridge for Security Hub CSPM findings](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-cwe-all-findings.html)
- [AWS Security Finding Format](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-format.html)
- [Amazon EventBridge targets](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html)
- [Amazon SNS email subscriptions](https://docs.aws.amazon.com/sns/latest/dg/sns-email-notifications.html)
- [OpenSearch Security Analytics concepts](https://docs.opensearch.org/latest/security-analytics/)
