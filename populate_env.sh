#!/bin/bash

# Create or overwrite the .env file using sudo
sudo tee .env > /dev/null << EOF
OPENAI_API_KEY="$OPENAI_API_KEY"
ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
ESPN_LEAGUE_ID="$ESPN_LEAGUE_ID"
ESPN_S2="$ESPN_S2"
ESPN_SWID="$ESPN_SWID"
REDDIT_CLIENT_ID="$REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET="$REDDIT_CLIENT_SECRET"
TAKE_BOT_SLACK_URL=$TAKE_BOT_SLACK_URL
EOF

echo ".env file has been created/updated with the environment variables."
