# Operations

This chapter covers what happens after your pipeline runs: monitoring, cost management, troubleshooting, and keeping things running smoothly.

## Topics

- **Monitoring**: CloudWatch dashboards, Batch job status, pipeline health
- **Cost management**: Tagging, budgets, Spot vs On-Demand decisions
- **Troubleshooting**: When things fail, how do you find out why?
- **Automation**: Alerts, auto-scaling policies, scheduled runs

## Start With

- `reference/TROUBLESHOOTING.md` - Common failures and fixes
- `DEBUGGING.md` - How to triage a failed pipeline run

## Things to Build

- Example CloudWatch dashboard config
- Cost allocation tag strategy
- Alerting rules (failed jobs, stuck queues, budget thresholds)
- Runbook: "my pipeline failed, now what?"
- Log analysis patterns (where to look, what to grep for)

## Example Questions to Answer

- What's the minimum monitoring setup everyone should have?
- How do you track cost per pipeline run?
- What are the most common failure modes and how do you recover?
- When should you use Spot vs On-Demand?
