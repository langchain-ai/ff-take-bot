# Fantasy Football Take Bot

[Ambient agents](https://blog.langchain.dev/ux-for-agents-part-2-ambient/) represent a shift from chat-based AI interactions to AI that works quietly in the background, monitoring and analyzing information without requiring constant user attention. While chat interfaces limit us to one task at a time, ambient agents can handle multiple tasks simultaneously, working diligently without the pressure of real-time response expectations.

This repository demonstrates a fun internal example we use at LangChain: a Fantasy Football "Take Bot" that runs in the background to keep our league engaged. This agent:

1. Scrapes recent posts from the [Reddit `fantasyfootball` sub](https://www.reddit.com/r/fantasyfootball/)
2. Gets our Fantasy Football league data from the ESPN API
3. Generates short-summaries (or "takes") for each Fantasy team manager based on their roster
4. Publishes the takes to a Slack channel
5. The app is deployed to [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_cloud/) and scheduled to run once a day

Instead of managers having to actively seek out fantasy football insights, this ambient agent does the work for them, delivering daily insights directly to Slack. It's a practical example of moving from "human-in-the-loop" to "human-on-the-loop" - the agent works autonomously, but all its steps are observable and the output can be reviewed and adjusted as needed.

![Screenshot 2024-11-14 at 4 21 51 PM](https://github.com/user-attachments/assets/4fcf879a-74a0-45ed-b1e5-fe3dfb8bca02)

## Data Sources 

### Reddit 

The Take Bot scrapes recent posts from the [Reddit `fantasyfootball` subreddit](https://www.reddit.com/r/fantasyfootball/) to gather current fantasy football discussions and trends. To set up Reddit API access:

1. Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create Application" or "Create Another Application"
3. Fill in the following:
   - Name: `fantasy-football-take-bot` (or any name you prefer)
   - Select "script" as the application type
   - Description: Optional, but helpful for remembering the app's purpose
   - About URL: Can be left blank for personal use
   - Redirect URI: Use `http://localhost:8080`
4. Click "Create app"
5. Once created, you'll see your credentials:
   - Client ID: Found under your app name
   - Client Secret: Listed as "secret"

Add the following credentials to your environment:

* `REDDIT_CLIENT_ID`
* `REDDIT_CLIENT_SECRET`

### ESPN API

Our Fantasy Football league using the ESPN app. We used the [espn-api package](https://github.com/cwendt94/espn-api) to access the league data. 

Add add the following credentials to your environment:

* `ESPN_LEAGUE_ID`: get this from your ESPN url, `leagueId`: `https://fantasy.espn.com/football/team?leagueId=xxx&teamId=y&seasonId=2024`
* `ESPN_S2`: get this as shown [here](https://github.com/cwendt94/espn-api/discussions/150#discussioncomment-133615)
* `ESPN_SWID`: get this as shown [here](https://github.com/cwendt94/espn-api/discussions/150#discussioncomment-133615)

## Publishing to Slack

Since ambient agents work best when integrated into existing workflows, we publish the agent's insights directly to Slack where our team already communicates. This allows managers to passively monitor the agent's analysis while going about their day. To set this up:

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name your app (e.g., "Take Bot") and select your workspace
5. Once created, go to "Incoming Webhooks" in the left sidebar
6. Toggle "Activate Incoming Webhooks" to On
7. Click "Add New Webhook to Workspace"
8. Choose the channel where you want the messages to appear
9. Copy the "Webhook URL" that's generated

Add add webhook URL credentials to your environment:

* `TAKE_BOT_SLACK_URL` 

## Testing with the notebook

Create your environment and run the notebook to test the graph and your Slack connection.
```
$ python3 -m venv take-bot-env
$ source take-bot-env/bin/activate
$ pip install -r requirements.txt
$ jupyter notebook
```

## Running Studio 

You can use the [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio) desktop app to run the agent locally (on your own machine). 

To do this, first [download](https://github.com/langchain-ai/langgraph-studio?tab=readme-ov-file#download) the desktop app and have [Docker Desktop](https://docs.docker.com/engine/install/) running. 

Generate your `.env` file with the necessary credentials: 

```
$ ./populate_env.sh
```

Load this folder in the Studio app to launch it.

Simply run `submit` with default values (`[]`) passed to the input state; the app will populate these as it runs.

![Screenshot 2024-11-18 at 2 14 57 PM](https://github.com/user-attachments/assets/46d4e1b5-cab8-438e-ba3b-35c0b5362cee)

## Hosted Deployment

We deployed our app to [LangGraph Cloud](https://langchain-ai.github.io/langgraph/concepts/langgraph_cloud/), a [managed service for running LangGraph graphs](https://langchain-ai.github.io/langgraph/concepts/deployment_options/#cloud-saas). 
This makes it easy to set up a [scheduled job](https://langchain-ai.github.io/langgraph/cloud/how-tos/cron_jobs/) to run the graph on a regular basis (e.g., daily) and publish the results to Slack.
As shown in the notebook, you can use the LangGraph Python SDK to create a scheduled job: 

```
from langgraph_sdk import get_client

# URL from our LangGraph Cloud deployment
deployed_url = "https://ff-take-bot-deployment-f4901b2dbda85d9787dac18e2a977956.default.us.langgraph.app"
client = get_client(url=deployed_url)

# An assistant ID is automatically created for each deployment
await client.assistants.search(metadata={"created_by": "system"})

# Set the assistant ID you want to create a cron job for
assistant_id = 'xxx'

# Use she SDK to schedule a cron job e.g., to run at 1:00 PM PST (21:00 UTC) every day
cron_job_stateless = await client.crons.create(
    assistant_id,
    schedule="0 21 * * *",
    input={"league": []} 
)
```
