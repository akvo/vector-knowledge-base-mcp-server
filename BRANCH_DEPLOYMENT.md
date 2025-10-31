# 🚀 Branch-Based Service Deployment Guide

## Overview

This repository supports **branch-based service deployments**.
Each branch prefixed with `deployment`- will automatically trigger a **build, push, and rollout** process to create a **distinct running service** on the cluster — separate from the main app.

This mechanism is ideal for:
- Deploying isolated service instances (for clients, tenants, or test environments)
- Managing multiple active deployments of the same app
- Ensuring version independence between deployments

## 🧩 Branch Naming Convention

| Branch Type           | Example                | Purpose                                                            |
| --------------------- | ---------------------- | ------------------------------------------------------------------ |
| **Main branch**       | `main`                 | The default or shared deployment                                   |
| **Deployment branch** | `deployment-agriconnect` | Creates a separate instance of the app (e.g., “agriconnect” service) |


## 🧱 Deployment Architecture

Each branch creates a **self-contained service deployment** with its own namespace.

| Branch                 | App Name                  | Namespace                           |
| ---------------------- | ------------------------- | ----------------------------------- |
| `main`                 | `kb-mcp-server`           | `kb-mcp-server-namespace`           |
| `deployment-agriconnect` | `agriconnect-kb-mcp-server` | `agriconnect-kb-mcp-server-namespace` |
| `deployment-clienta`   | `clienta-kb-mcp-server`   | `clienta-kb-mcp-server-namespace`   |

All deployments share the same Docker build pipeline, but are deployed independently into Kubernetes.


## ⚙️ How It Works

The workflow file

```bash
.github/workflows/deploy.yml
```

triggers automatically on:

```yaml
on:
  push:
    branches:
      - "main"
      - "deployment-*"
```

### Pipeline Breakdown

**1. Run Tests**
- Ensures all code passes before any deployment.

**2. Build & Push**
- Builds Docker images for both `main` and `script` services.
- Tags the images with the branch ref + commit SHA.
- Pushes to container registry.

**3. Dynamic Environment Resolution**
- The app name and namespace are derived from the branch name:
```bash
if main:
  APP_NAME="kb-mcp-server"
  NAMESPACE="kb-mcp-server-namespace"
else:
  APP_NAME="<suffix>-kb-mcp-server"
  NAMESPACE="<suffix>-kb-mcp-server-namespace"
```

**4. Rollout**
- Deploys to the cluster with the generated namespace.
- Each branch gets a unique Kubernetes namespace.
- Rollouts are gated by admin approval.

---

## 🚀 Deploying a New Service

### 1. Create a Deployment Branch

```bash
git checkout -b deployment-agriconnect
git push origin deployment-agriconnect
```

This triggers:
- The **Branch Deployment** GitHub Actions workflow
- Automated test, build, push, and rollout sequence

### 2. Wait for Admin Approval
If protection rules are enabled, rollout will **pause** until an admin approves.

### 🔒 Rollout Protection (Required Review)

#### Why

To prevent unreviewed or accidental deployments, rollouts require admin approval.

#### Setup
1. Go to your repo **Settings → Environments → branch-test-deployment**
2. Under Protection Rules, enable:
   - ✅ Require reviewers before deployment
   - ✅ Select authorized reviewers (DevOps, admins)

When a deployment workflow reaches the rollout step, GitHub will pause and show this in the Actions UI:

> “This deployment requires review before proceeding."

After approval, rollout continues automatically.

### ✅ Summary

| Step | Description                                 |
| ---- | ------------------------------------------- |
| 1    | Create a branch prefixed with `deployment-` |
| 2    | Push branch → triggers CI/CD                |
| 3    | Wait for admin rollout approval             |
| 4    | Service is deployed under its own namespace |


### 🧭 Example Deployments

| Branch                 | Resulting App             | Namespace                           | Rollout Status     |
| ---------------------- | ------------------------- | ----------------------------------- | ------------------ |
| `main`                 | `kb-mcp-server`           | `kb-mcp-server-namespace`           | 🕓 Requires Review |
| `deployment-clienta`   | `clienta-kb-mcp-server`   | `clienta-kb-mcp-server-namespace`   | 🕓 Requires Review |
| `deployment-agriconnect` | `agriconnect-kb-mcp-server` | `agriconnect-kb-mcp-server-namespace` | 🕓 Requires Review |
