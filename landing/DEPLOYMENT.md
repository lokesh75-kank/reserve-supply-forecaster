# Landing Page Deployment Guide

This guide explains how to deploy the landing page to GitHub Pages using GitHub Actions.

## Prerequisites

- A GitHub repository
- GitHub Pages enabled in repository settings
- Push access to the repository

## Setup Steps

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **"GitHub Actions"** (not "Deploy from a branch")
4. Save the settings

### 2. Push Your Code

The GitHub Actions workflow is already configured in `.github/workflows/deploy-landing.yml`. Simply push your code to the `main` branch:

```bash
git add .
git commit -m "Add landing page"
git push origin main
```

### 3. Monitor Deployment

1. Go to the **Actions** tab in your GitHub repository
2. You should see a workflow run named "Deploy Landing Page"
3. Wait for it to complete (usually takes 1-2 minutes)
4. Once complete, your site will be live!

### 4. Access Your Site

Your landing page will be available at:
```
https://<your-username>.github.io/<repository-name>/
```

For example, if your username is `johndoe` and repository is `reserve-supply-forecaster`:
```
https://johndoe.github.io/reserve-supply-forecaster/
```

## How It Works

The GitHub Actions workflow:

1. **Triggers** when you push changes to the `landing/` directory on `main` branch
2. **Checks out** your repository code
3. **Uploads** the `landing/` directory as a Pages artifact
4. **Deploys** it to GitHub Pages

## Manual Deployment

You can also trigger the workflow manually:

1. Go to **Actions** tab
2. Select **"Deploy Landing Page"** workflow
3. Click **"Run workflow"** button
4. Select the branch (usually `main`)
5. Click **"Run workflow"**

## Troubleshooting

### Workflow Not Running

- Make sure GitHub Pages is enabled with "GitHub Actions" as the source
- Check that you're pushing to the `main` branch
- Verify the workflow file exists at `.github/workflows/deploy-landing.yml`

### Site Not Updating

- Wait a few minutes for GitHub Pages to update (can take up to 10 minutes)
- Check the Actions tab to ensure the workflow completed successfully
- Clear your browser cache and try again

### 404 Error

- Verify the repository name matches your GitHub username/repo
- Check that the `landing/index.html` file exists
- Ensure GitHub Pages is enabled in repository settings

## Custom Domain (Optional)

If you want to use a custom domain:

1. Add a `CNAME` file in the `landing/` directory with your domain name
2. Configure DNS settings with your domain provider
3. Update GitHub Pages settings to use your custom domain

## Updating the Landing Page

To update the landing page:

1. Edit files in the `landing/` directory
2. Commit and push changes:
   ```bash
   git add landing/
   git commit -m "Update landing page"
   git push origin main
   ```
3. The workflow will automatically redeploy

## Workflow Configuration

The workflow is configured to:
- Run on pushes to `main` branch when `landing/` files change
- Allow manual triggering
- Deploy to GitHub Pages environment
- Use the latest GitHub Actions for Pages deployment

You can modify `.github/workflows/deploy-landing.yml` if you need different behavior.
