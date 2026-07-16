# AMI Strategy: Dynamic vs Custom

## Our Approach: Dynamic AMI (No Custom AMI)

This project uses `Ec2Configuration: [{ImageType: ECS_AL2023}]` on the Batch compute environments with NO `ImageId` in the launch template. This means:

- **Batch resolves the AMI at instance launch time** — always picks the latest ECS-optimized AL2023 AMI
- Security patches applied automatically (AWS publishes new AMIs monthly)
- Zero AMI maintenance burden
- Tools (AWS CLI, S3 Mountpoint, CloudWatch agent) installed at boot via UserData

## Alternative: Custom AMI

The classic AWS Batch + Nextflow model uses a custom AMI with everything pre-baked:

```yaml
# Launch template with pinned AMI
ImageId: ami-0abc123456789
```

### When to use a custom AMI:
- Compliance requirements (need to audit exactly what's on each instance)
- Faster boot time (no cloud-init package installation at startup)
- Pre-pulling large container images (eliminates first-run pull delay)
- Installing tools that take a long time to compile/configure
- Reproducibility requirements (same AMI = same behaviour every time)

### When NOT to use a custom AMI (our case):
- Workshop/sandbox environments where simplicity matters
- When you want automatic security updates
- When cloud-init adds minimal boot time (our UserData runs ~30 seconds)
- When you don't have an AMI rebuild pipeline

## Hybrid Approach (Production)

For production environments that want both auto-updates and reproducibility:

1. Use the SSM parameter to resolve the latest AMI at deploy time:
   ```yaml
   ImageId: !Sub '{{resolve:ssm:/aws/service/ecs/optimized-ami/amazon-linux-2023/recommended/image_id}}'
   ```
2. The AMI ID is captured in the launch template at stack creation
3. Redeploy monthly (or on a schedule) to pick up the latest AMI
4. Between deploys, all instances use the same pinned AMI

This gives you:
- Deterministic behaviour between deploys
- New patches on a controlled schedule
- No custom AMI build pipeline needed

## Boot Time Comparison

| Approach | Time to first task | Notes |
|----------|-------------------|-------|
| Custom AMI (everything pre-baked) | ~60 seconds | Fastest, but requires maintenance |
| Our approach (cloud-init) | ~90-120 seconds | Installs CLI, Mountpoint, mounts scratch |
| Custom AMI + container pre-pull | ~60 seconds | Even first container starts instantly |

The ~30 second difference is negligible for genomics workloads where tasks run 10-60 minutes each.

## What Our UserData Installs at Boot

1. `git`, `unzip`, `amazon-cloudwatch-agent` (via packages)
2. CloudWatch agent configuration (logs shipping)
3. ECS agent tuning (container create timeout, image pull behaviour)
4. AWS CLI v2 (for container bind-mount at `/opt/aws-cli/bin`)
5. S3 Mountpoint (for reference data at `/mnt/s3-reference`)
6. Format + mount scratch EBS volume at `/mnt/scratch`

If boot time becomes critical, these could be baked into a custom AMI instead.
