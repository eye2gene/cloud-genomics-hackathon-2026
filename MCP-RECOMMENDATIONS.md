# MCP Server Recommendations

Model Context Protocol (MCP) servers give Kiro direct access to AWS tools and data sources. Set these up in `~/.kiro/settings/mcp.json` to enhance your hackathon experience.

Full list: https://awslabs.github.io/mcp/

## Recommended for This Hackathon

### AWS Open Data Registry (RODA)

Discover and preview public genomics datasets (1000 Genomes, PGP-UK, etc.) directly from Kiro.

```json
"awslabs.roda-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.roda-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

**Try:** "Find 1000 Genomes WGS data and generate a samplesheet for nf-core/sarek"

### AWS Documentation

Search and read AWS documentation from within Kiro. Useful for looking up Batch, S3, IAM, HealthOmics docs without leaving your editor.

```json
"awslabs.aws-documentation-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.aws-documentation-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

**Try:** "Look up the AWS Batch CreateComputeEnvironment API parameters"

### AWS HealthOmics

Interact with AWS HealthOmics workflows directly from Kiro.

```json
"awslabs.aws-healthomics-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.aws-healthomics-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

**Try:** "List my HealthOmics workflows" or "Submit a workflow run"

### AWS CDK (CloudFormation)

Generate and validate CDK infrastructure. Useful for the Ways to Run chapter.

```json
"awslabs.cfn-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.cfn-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

**Try:** "Validate my CDK stack for security issues" or "What CloudFormation resources does AWS Batch need?"

### AWS Cost Analysis

Query cost data for benchmarking and operations work.

```json
"awslabs.cost-analysis-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.cost-analysis-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

**Try:** "What did my Batch jobs cost yesterday?" or "Break down costs by service for this week"

## Optional

### AWS API MCP Server

Direct AWS CLI-style commands from Kiro. Powerful but broad.

```json
"awslabs.aws-api-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.aws-api-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

### AWS Knowledge MCP Server

Regional availability, documentation search, and reading AWS docs pages.

```json
"awslabs.aws-knowledge-mcp-server": {
  "command": "uvx",
  "args": ["awslabs.aws-knowledge-mcp-server@latest"],
  "env": { "FASTMCP_LOG_LEVEL": "ERROR" },
  "disabled": false,
  "autoApprove": []
}
```

## Setup

Add the servers you want to `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    // paste server configs here
  }
}
```

Restart Kiro after editing. Verify by asking Kiro to use one of the tools.

## Prerequisites

- `uv` or `uvx` installed (`pip install uv` or `brew install uv`)
- AWS credentials configured (`aws configure`)
