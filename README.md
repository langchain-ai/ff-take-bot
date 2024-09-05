# ff-take-bot

Generate takes for Fantasy Football based upon a given league and current / recent events.

## Reddit 

Login with your credentials and [create an app](https://www.reddit.com/prefs/apps).

Then, set these in your environment:
* `REDDIT_CLIENT_ID`
* `REDDIT_CLIENT_SECRET`

## ESPN API

We'll use the [espn-api package](https://github.com/cwendt94/espn-api) to access your league , which requires a few things set in your environment:

* `ESPN_LEAGUE_ID`: get this from your ESPN url, `leagueId`: `https://fantasy.espn.com/football/team?leagueId=xxx&teamId=y&seasonId=2024`
* `ESPN_S2`: get this as shown [here](https://github.com/cwendt94/espn-api/discussions/150#discussioncomment-133615)
* `ESPN_SWID`: get this as shown [here](https://github.com/cwendt94/espn-api/discussions/150#discussioncomment-133615)

## Slack

We created a webhook for an internal Slack channel where we publish results.

## Running the notebook

Create your environment and run the notebook to work with your graph logic.
```
$ python3 -m venv take-bot-env
$ source take-bot-env/bin/activate
$ pip install -r requirements.txt
$ jupyter notebook
```

## Running Studio 

Generate your `.env` file and load this project in LangGraph studio. 
```
$ ./populate_env.sh
```
