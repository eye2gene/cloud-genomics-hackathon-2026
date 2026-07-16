# Which Pattern Should I Use?

This is a starting point. Fill in from your own experience as you explore the patterns.

## Example Decision Tree

```
I want to run Nextflow on AWS
│
├─ Am I new to AWS or just testing?
│  └─ YES → Laptop to Batch or AWS HealthOmics
│
├─ Do I need it to run unattended (overnight, triggered by events)?
│  └─ YES → Batch Squared or AWS HealthOmics
│
├─ Do multiple people need to submit pipelines?
│  └─ YES → EC2 Head to Batch (shared head node)
│
├─ Do I want zero infrastructure management?
│  └─ YES → AWS HealthOmics
│
└─ Not sure?
   └─ Start with Laptop to Batch. You can always migrate later.
```

## Migration Path

You can evolve from simpler to more complex patterns:

```
Laptop to Batch → EC2 Head to Batch → Batch Squared
                                    ↘
                          AWS HealthOmics (different path, managed)
```

## Example Use Cases

| Use case | Pattern | Why |
|----------|---------|-----|
| Learning AWS Batch for the first time | Laptop to Batch | Minimal setup, easy to iterate |
| Running sarek on 100+ genomes overnight | Batch Squared | Ephemeral, no laptop needed |
| Team of 5 bioinformaticians sharing infra | EC2 Head to Batch | Shared access, persistent |
| [Your use case here] | [Pattern] | [Your reasoning] |
| [Your use case here] | [Pattern] | [Your reasoning] |
| [Your use case here] | [Pattern] | [Your reasoning] |

## Key Questions to Ask Yourself

- How long does my pipeline run?
- Do I need it running when my laptop is closed?
- Am I the only user or is this shared?
- How much infrastructure am I comfortable managing?
- Is this a one-off or recurring?

## Things to Document as You Explore

- What surprised you about a pattern?
- What broke and how did you fix it?
- What would you tell someone starting with that pattern?
- When would you NOT use that pattern?

Add your findings here or in the pattern folders.
