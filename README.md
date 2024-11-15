# Fantasy Football Take Bot

[Ambient](https://blog.langchain.dev/ux-for-agents-part-2-ambient/) agents run "in the background" and often provide useful reports or summarization of information (e.g., from a newsfeed, a Slack channel, email, etc) on a regular schedule. This is an ambient agent designed for Fantasy Football, which we use internally for our own league at LangChain. It uses LangGraph to build an agent that:

1. Scrapes recent posts from the [Reddit `fantasyfootball` sub](https://www.reddit.com/r/fantasyfootball/)
2. Generates short-summaries (or "takes") for each Fantasy team manager if any of their players are mentioned in the posts
3. Publishes the takes to a Slack channel

## Data Sources 

### Reddit 

The Take Bot is configured to scrape the [Reddit `fantasyfootball` sub](https://www.reddit.com/r/fantasyfootball/). 

After [creating a Reddit app](https://www.reddit.com/prefs/apps), add the following credentials to your environment:

* `REDDIT_CLIENT_ID`
* `REDDIT_CLIENT_SECRET`

### ESPN API

Our Fantasy Football league using the ESPN app. We'll use the [espn-api package](https://github.com/cwendt94/espn-api) to access the league data. 

Add add the following credentials to your environment:

* `ESPN_LEAGUE_ID`: get this from your ESPN url, `leagueId`: `https://fantasy.espn.com/football/team?leagueId=xxx&teamId=y&seasonId=2024`
* `ESPN_S2`: get this as shown [here](https://github.com/cwendt94/espn-api/discussions/150#discussioncomment-133615)
* `ESPN_SWID`: get this as shown [here](https://github.com/cwendt94/espn-api/discussions/150#discussioncomment-133615)

## Publishing to Slack

We publish results to an internal Slack channel. If you want to do this, create a new webhook URL:

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

## Running the notebook

Create your environment and run the notebook to test the graph and your Slack connection.
```
$ python3 -m venv take-bot-env
$ source take-bot-env/bin/activate
$ pip install -r requirements.txt
$ jupyter notebook
```

## Running Studio 

You can use the [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio) desktop app to run the graph locally. 

To do this, [download](https://github.com/langchain-ai/langgraph-studio?tab=readme-ov-file#download) the desktop app.

Have [Docker Desktop](https://docs.docker.com/engine/install/) running. 

Generate your `.env` file with the necessary credentials: 

```
$ ./populate_env.sh
```



