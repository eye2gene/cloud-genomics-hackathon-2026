# Benchmarking

This chapter is about collecting real performance data: how long things take, how much they cost, and what affects both.

## What to Benchmark

- **Storage backends**: e.g. S3 vs FSx for Lustre vs EFS. What's faster for different workload profiles?
- **Compute scaling**: How do AWS Batch or AWS HealthOmics scale with increasing parallelism? Where are the bottlenecks?
- **Pipeline performance**: End-to-end timing for real pipelines at different sample counts
- **Cost**: What does it actually cost to run X samples through Y pipeline?

## How to Contribute

1. Pick a benchmark scenario (or propose a new one)
2. Run the test in your sandbox account
3. Record results using the template in `results/`
4. Document your methodology so others can reproduce it

## Example Questions to Answer

- At what sample count does FSx become worth the setup cost?
- What's the cost difference between On-Demand and Spot for a 30-sample WGS run?
- How does increasing maxRetries affect cost vs reliability?
- What's the overhead of Fusion vs traditional S3 staging?

## Results Template

Record your results using `results/results.template.csv`. One row per benchmark run.
