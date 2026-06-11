# GitHub Actions CI Pipeline

This GitHub Actions workflow triggers an Azure DevOps pipeline and monitors its execution status.

## Setup Requirements

### 1. GitHub Repository Secrets

You need to configure the following secret in your GitHub repository:

- `AZURE_DEVOPS_TOKEN`: Your Azure DevOps Personal Access Token (PAT)

To create a PAT:
1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create a new token with the following scopes:
   - **Build**: Read & Execute
   - **Project and Team**: Read
3. Copy the token and add it as a secret in your GitHub repository

### 2. Directory Structure

Ensure the workflow file is placed in the correct directory:
```
.github/
  workflows/
    ci.yaml
```

Note: GitHub Actions looks for workflows in `.github/workflows/` (plural), not `.github/workflow/` (singular).

## Workflow Features

### Triggers
- **Push events**: Triggers on pushes to `main`, `develop`, and `feature/*` branches
- **Pull requests**: Triggers on PRs targeting `main` or `develop` branches
- **Manual trigger**: Can be triggered manually via GitHub UI

### Environment Variables
All pipeline variables are configured as environment variables in the workflow:
- Azure resource names (Key Vault, Storage, Database, etc.)
- Azure DevOps organization and project details
- Application-specific configurations

### Steps
1. **Checkout code**: Downloads the repository code
2. **Setup Azure CLI**: Installs and configures Azure CLI
3. **Configure extensions**: Sets up Azure DevOps CLI extension
4. **Login to Azure DevOps**: Authenticates using the PAT
5. **Set branch name**: Determines the correct branch name for triggering
6. **Queue pipeline**: Triggers the Azure DevOps pipeline with all required variables
7. **Monitor status and stream logs**: 
   - Continuously monitors the pipeline execution until completion
   - **Real-time log streaming**: Fetches and displays Azure DevOps pipeline logs every 10 seconds
   - **Job status tracking**: Shows active and completed jobs with their states
   - **Final log capture**: Saves complete logs to `azure-devops-logs.txt`
8. **Upload artifacts**: Saves both build ID and complete Azure DevOps logs
9. **Display summary**: Shows build URL and artifact information

### Real-time Log Features
- **Live log streaming**: See Azure DevOps pipeline logs as they're generated
- **Job status updates**: Track individual job progress and results
- **Complete log capture**: Full logs saved as artifacts for later review
- **Error visibility**: Immediate access to failure details and stack traces

### Error Handling
- The workflow will fail if the Azure DevOps pipeline fails
- Proper error messages and emojis for clear status indication
- **Complete log artifacts**: Build artifacts include both build ID and full Azure DevOps logs
- **Real-time error visibility**: Failures are immediately visible in the GitHub Actions logs
- **Downloadable logs**: Complete Azure DevOps logs available as artifacts for troubleshooting

## Log Artifacts

The workflow generates two main artifacts:

1. **BuildId.txt**: Contains the Azure DevOps build ID for reference
2. **azure-devops-logs.txt**: Complete raw logs from the Azure DevOps pipeline execution

These artifacts are available for download from the GitHub Actions run page and retained for 30 days.

## Usage

Once set up, the workflow will automatically trigger based on the configured events. You can also manually trigger it from the GitHub Actions tab in your repository.

The workflow will output the Azure DevOps build ID and continuously monitor the pipeline status, providing real-time feedback on the execution progress.
