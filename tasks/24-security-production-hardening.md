## Summary

A production-readiness / security-hardening pass covering the concrete gaps that show up in a `cdk-nag` / security review of the current stack: an unencrypted root volume, no IMDSv2 enforcement, no TLS-only bucket policy, and no private VPC endpoints. Individually small; together they move the deployment from "works" to "production-ready".

**Difficulty:** medium · **Effort:** medium

## Background

The baseline is already reasonable — the created VPC uses **private subnets with egress + NAT** (compute runs in `vpc.privateSubnets`), the S3 bucket is `S3_MANAGED`-encrypted and `RETAIN`, and idle CEs scale to zero. But a review of the code surfaces specific hardening gaps:

- **Root EBS volume is unencrypted.** In `lib/launch-template-stack.ts`, `/dev/xvdcz` and `/dev/xvdba` set `encrypted: true`, but the **root `/dev/xvda` does not** — task data and container layers on root are written in clear. Encrypt it.
- **IMDSv2 not enforced.** The launch template sets no `MetadataOptions`, so instances allow IMDSv1. Require IMDSv2 (`httpTokens: required`, hop limit 1) to reduce SSRF/credential-theft risk.
- **No TLS-only bucket policy.** `lib/s3-stack.ts` doesn't set `enforceSSL: true`, so non-HTTPS access isn't denied. Add it (a `cdk-nag` staple).
- **No VPC endpoints.** All S3/ECR/Logs traffic egresses via the NAT gateway — a cost *and* a data-exfil-surface consideration. A **gateway endpoint for S3** (and interface endpoints for ECR/Logs) keeps traffic on the AWS network and cuts NAT cost.
- **Broad security group.** The SG allows all TCP within itself and `allowAllOutbound`. Egress-all is needed for image pulls, but the self-ingress-all-TCP could be scoped; document the intent.

This issue is the umbrella "make it production-ready" checklist; it explicitly builds on and cross-references the IAM (`09`), log-retention (`08`), and CI/`cdk-nag` (`14`) issues rather than duplicating them.

## What to do

- [ ] Encrypt the root `/dev/xvda` volume in the launch template (`encrypted: true`), matching the other volumes.
- [ ] Enforce IMDSv2 on the launch template (`requireImdsv2` / `MetadataOptions` with `httpTokens: required`).
- [ ] Set `enforceSSL: true` on the created bucket; consider `versioning` and server-access logging for production.
- [ ] Add a VPC **gateway endpoint for S3** (and interface endpoints for ECR API/DKR + CloudWatch Logs) in the created-VPC path.
- [ ] Run `cdk-nag` (`AwsSolutionsChecks`, from `14-ci-github-actions.md`) and triage/suppress-with-reason the remaining findings.
- [ ] Fold the least-privilege IAM work (`09`) and explicit log retention (`08`) into the production-readiness definition of done.

## Implementation pointers

- **`lib/launch-template-stack.ts`** — add `encrypted: true` to the `/dev/xvda` `ebs(...)`; set launch-template metadata options to require IMDSv2.
- **`lib/s3-stack.ts`** — `enforceSSL: true` on the `new s3.Bucket(...)`; optionally `versioned: true` + access logs for prod.
- **`lib/vpc-stack.ts`** — `vpc.addGatewayEndpoint('S3', { service: ec2.GatewayVpcEndpointAwsService.S3 })` and interface endpoints for ECR/Logs (only in the `createVpc` branch).
- **`bin/aws_batch_squared.ts`** — a `production` profile (`19-deployment-profiles.md`) should turn these on by default.
- Drive the whole pass with `cdk-nag` so it's repeatable.

## Acceptance criteria

- All EBS volumes (incl. root) are encrypted; instances require IMDSv2.
- The bucket denies non-TLS access; S3 (at least) is reached via a VPC endpoint in the created-VPC path.
- `cdk-nag` runs clean or with documented, justified suppressions.
- A full pipeline run still succeeds end to end after hardening.

## References

- [EC2 IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) · [`requireImdsv2` in CDK launch templates](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ec2.LaunchTemplate.html)
- [S3 `enforceSSL` / TLS-only bucket policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [VPC endpoints for S3/ECR/Logs](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) · [`cdk-nag`](https://github.com/cdklabs/cdk-nag)
- Code: `lib/launch-template-stack.ts`, `lib/s3-stack.ts`, `lib/vpc-stack.ts`
- Related: `08-log-retention-lifecycle.md`, `09-tighten-iam.md`, `14-ci-github-actions.md`, `19-deployment-profiles.md`
