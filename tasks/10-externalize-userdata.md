## Summary

Move the launch-template user-data out of the hand-built multipart string array and make the bootstrap resilient, so a slow or failed optional step can't stop an instance from joining ECS.

**Difficulty:** medium · **Effort:** medium

## Background

`lib/launch-template-stack.ts` builds a large multipart cloud-init as an array of string literals — hard to read and easy to break. Per `DEBUGGING.md`, a bad edit to this block caused a real outage: a hanging `runcmd` step deadlocked cloud-init and no instance could join the cluster (`ecs.service` is ordered `After=cloud-final.service`).

Two goals: make the bootstrap **maintainable** (move it to a template asset file, or a clearly structured builder) and make it **robust** (optional steps fast-fail and are non-blocking; nothing that can hang is ordered before the ECS agent).

## What to do

- [ ] Extract the cloud-init into a readable asset file (or a well-structured, commented builder) that `lib/launch-template-stack.ts` reads in.
- [ ] Ensure ECS-critical config is applied via `bootcmd` (before the agent) and that optional steps (log shipping, mounts) cannot block cloud-init from completing.
- [ ] Add guardrails: timeouts / `|| true` on non-essential steps; keep the "verify aws-cli or shutdown" behaviour intentional and documented.
- [ ] Redeploy and confirm nodes register reliably; sanity-check with `scripts/nf-debug.sh diag <i-id>`.

## Implementation pointers

- **`lib/launch-template-stack.ts`** — the entire `userData.addCommands(...)` string-array cloud-init. Move it to an asset file (e.g. read `assets/user-data.*` via `fs.readFileSync`, or use `ec2.UserData.custom(...)`), shift ECS-critical config into `bootcmd`, and make the optional steps (Mountpoint mount, `ecs-logs-collector.sh`, the S3 log copy) non-blocking / fast-failing so they can't stall cloud-init.
- Keep the intentional `command -v aws || shutdown -P now` guard, but document it.

## Acceptance criteria

- User-data is maintainable (external asset or structured builder) and reviewed.
- A failing/slow optional bootstrap step no longer prevents ECS registration.
- Nodes register reliably after redeploy.

## References

- [cloud-init modules & merging](https://cloudinit.readthedocs.io/en/latest/reference/modules.html)
- [Amazon ECS-optimized AMI / container agent](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-config.html)
- [Adding user data to a CDK asset](https://docs.aws.amazon.com/cdk/v2/guide/assets.html)
- Project docs: `DEBUGGING.md` → cloud-init deadlock; Code: `lib/launch-template-stack.ts`
