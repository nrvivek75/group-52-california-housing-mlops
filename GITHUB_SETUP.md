# 🔐 GitHub Setup Guide - California Housing MLOps

This guide explains how to set up the required GitHub secrets for the CI/CD pipeline to work correctly.

## 📋 Required GitHub Secrets

To enable the CI/CD pipeline to build and push Docker images, you need to set up the following secrets in your GitHub repository:

### 1. Docker Hub Credentials

#### DOCKER_USERNAME
- **Description**: Your Docker Hub username
- **Value**: Your Docker Hub username (e.g., `johndoe`)
- **Required**: Yes (for pushing to Docker Hub)

#### DOCKER_PASSWORD
- **Description**: Your Docker Hub password or access token
- **Value**: Your Docker Hub password or access token
- **Required**: Yes (for pushing to Docker Hub)
- **Note**: It's recommended to use an access token instead of your password

### 2. How to Set Up GitHub Secrets

#### Step 1: Go to Your Repository Settings
1. Navigate to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

#### Step 2: Add Each Secret
1. Click **New repository secret**
2. Enter the secret name (e.g., `DOCKER_USERNAME`)
3. Enter the secret value
4. Click **Add secret**
5. Repeat for all required secrets

### 3. Creating Docker Hub Access Token

If you want to use an access token instead of your password:

#### Step 1: Log into Docker Hub
1. Go to [hub.docker.com](https://hub.docker.com)
2. Sign in to your account

#### Step 2: Create Access Token
1. Click on your username → **Account Settings**
2. Go to **Security** tab
3. Click **New Access Token**
4. Give it a name (e.g., "GitHub Actions")
5. Set permissions to **Read & Write**
6. Click **Generate**
7. **Copy the token** (you won't see it again!)

#### Step 3: Use Token in GitHub
- Set `DOCKER_PASSWORD` to this access token value

### 4. Verifying Secrets Are Set

After setting the secrets, you can verify they're configured:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. You should see your secrets listed (values will be hidden)
3. The secrets will be automatically available to your GitHub Actions

### 5. Testing the Setup

Once secrets are configured:

1. **Push to main branch** to trigger the CI/CD pipeline
2. **Monitor the Actions tab** to see the pipeline progress
3. **Check for success** in the build-and-push job

## 🚀 What Happens After Setup

### CI/CD Pipeline Flow:
1. **Push to GitHub** → Triggers workflow
2. **Lint and Test** → Runs code quality checks
3. **Build and Push** → Creates Docker image and pushes to Docker Hub
4. **Success** → Image available for local deployment

### Docker Image Tags:
- `latest` → Always points to the most recent build
- `{commit-sha}` → Specific version tied to a commit

## 🔍 Troubleshooting

### Common Issues:

#### 1. "Authentication failed" Error
- **Cause**: Invalid Docker Hub credentials
- **Solution**: Verify username and password/token are correct

#### 2. "Permission denied" Error
- **Cause**: Insufficient Docker Hub permissions
- **Solution**: Ensure your account can push to Docker Hub

#### 3. "Repository not found" Error
- **Cause**: Repository doesn't exist on Docker Hub
- **Solution**: Create the repository on Docker Hub first

#### 4. Secrets Not Available
- **Cause**: Secrets not properly configured
- **Solution**: Check secret names match exactly (case-sensitive)

### Debugging Steps:
1. **Check Actions logs** for specific error messages
2. **Verify secret names** match exactly
3. **Test Docker Hub login** locally
4. **Check repository permissions** on Docker Hub

## 📝 Example Secret Configuration

Here's what your secrets should look like:

| Secret Name | Example Value |
|-------------|---------------|
| `DOCKER_USERNAME` | `johndoe` |
| `DOCKER_PASSWORD` | `dckr_pat_abc123...` |

## 🔒 Security Best Practices

1. **Use Access Tokens** instead of passwords
2. **Limit Token Permissions** to minimum required
3. **Rotate Tokens** periodically
4. **Never Commit Secrets** to your code
5. **Use Repository Secrets** (not environment secrets unless needed)

## 🎯 Next Steps

After setting up secrets:

1. **Push your code** to trigger the pipeline
2. **Monitor the build** in GitHub Actions
3. **Pull the image** locally once built
4. **Deploy and test** using the deployment scripts

---

**Need Help?** Check the main README.md or open an issue in your repository. 