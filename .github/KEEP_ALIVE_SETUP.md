# Keep-Alive Workflow Setup

This workflow automatically pings your Streamlit app every 10 minutes to prevent it from going to sleep on Streamlit Community Cloud.

## Setup Instructions

1. **Deploy your Streamlit app** to Streamlit Community Cloud (if not already done)
   - Your app will have a URL like: `https://your-app-name.streamlit.app`

2. **Add the Streamlit app URL as a repository secret:**
   - Go to your GitHub repository
   - Click on **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `STREAMLIT_APP_URL`
   - Value: Your full Streamlit app URL (e.g., `https://brewymcbrewapp.streamlit.app`)
   - Click **Add secret**

3. **Enable GitHub Actions** (if not already enabled)
   - Go to the **Actions** tab in your repository
   - If prompted, click **I understand my workflows, go ahead and enable them**

4. **Test the workflow:**
   - Go to **Actions** tab → **Keep Streamlit App Alive**
   - Click **Run workflow** → **Run workflow** (manual trigger)
   - Check the logs to verify it's working

## How It Works

- The workflow runs automatically every 10 minutes
- It makes an HTTP request to your Streamlit app URL
- This prevents Streamlit Community Cloud from putting your app to sleep due to inactivity
- You can also trigger it manually from the Actions tab

## Notes

- The workflow uses GitHub-hosted runners (free for public repositories)
- Private repositories have limited free minutes per month
- You can adjust the frequency by modifying the cron schedule in `.github/workflows/keep-alive.yml`
- Current schedule: `*/10 * * * *` (every 10 minutes)

## Cron Schedule Examples

If you want to change the frequency:
- Every 5 minutes: `*/5 * * * *`
- Every 15 minutes: `*/15 * * * *`
- Every 30 minutes: `*/30 * * * *`
- Every hour: `0 * * * *`
