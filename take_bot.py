from dotenv import load_dotenv
import os
import operator
from pydantic import BaseModel, Field
import requests
from typing_extensions import TypedDict, List, Annotated

from espn_api.football import League
import praw

from langchain_anthropic import ChatAnthropic 
from langchain_core.messages import SystemMessage, HumanMessage

from langgraph.constants import Send
from langgraph.graph import END, StateGraph, START

### Helper Functions and Variables

# Load environment variables from .env file
load_dotenv()

# ESPN league info
ESPN_LEAGUE_ID = os.getenv('ESPN_LEAGUE_ID')
ESPN_S2 = os.getenv('ESPN_S2')
ESPN_SWID = os.getenv('ESPN_SWID')

# Reddit creds
reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')

# Slack webhook URL
take_bot_url = os.getenv('TAKE_BOT_SLACK_URL')
print("**SLACK URL**")
print(take_bot_url)

# Initialize the Reddit instance
reddit = praw.Reddit(client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     user_agent='Fantasy Football Loader')

# Helper function to get recent Reddit posts
def get_recent_reddit_posts(subreddit_name,
                            filter_to_use,
                            number_of_posts,
                            number_of_comments,
                           ):

    """
    Retrieve top posts and their comments from a specified subreddit.

    Args:
    subreddit_name (str): Name of the subreddit to fetch posts from.
    filter_to_use (str): Time filter for top posts (e.g., 'day', 'week', 'month', 'year', 'all').
    number_of_posts (int): Number of top posts to retrieve.
    number_of_comments (int): Number of top comments to fetch for each post.

    Returns:
    str: A formatted string containing information about the top posts and their comments.
         Each post entry includes:
         - Post title
         - Post URL
         - Post score
         - Top comments (up to the specified number) with their scores
         Posts are separated by a line of '=' characters.

    Note:
    This function requires a properly initialized 'reddit' object with necessary permissions.
    """

    # Access the subreddit
    subreddit = reddit.subreddit(subreddit_name)
    
    # Get top posts based on the specified filter
    top_posts = subreddit.top(time_filter=filter_to_use, limit=number_of_posts)
    
    # Initialize an empty string to store the output
    reddit_expert_context = ""
    
    # Process each post
    for post in top_posts:
        reddit_expert_context += f"Title: {post.title}\n"
        reddit_expert_context += f"Source Data URL: {post.url}\n"
        reddit_expert_context += f"Reddit Post URL: {post.shortlink}\n"
        reddit_expert_context += f"Score: {post.score}\n"
        
        post.comments.replace_more(limit=0)  # Flatten the comment tree
        
        # Get the specified number of top comments
        for i, comment in enumerate(post.comments[:number_of_comments]):
            reddit_expert_context += f"Top Comment {i+1}: {comment.body}\n"
            reddit_expert_context += f"Comment Score: {comment.score}\n\n"
        
        reddit_expert_context += "="*50 + "\n\n"

    return reddit_expert_context

# Mapping from teams to Slack handles
teams = ['Milwaukee Bucks',
 'Hallucinations of Nick Saban',
 "Lance's Hit Squad",
 "Harrison's Team",
 'The Tank Bigsbies',
 'Taylor-Augmented Termination',
 'Rookie Season',
 'Mookillem',
 'This is the Wei',
 "Brace's Best Lineup"]

slack_handles = [
    "@Eric Han",
    "@Ben Mangum",
    "@lance",
    "@Harrison Chase",
    "@Sam Noyes",
    "@Jacob Lee",
    "@Maddy",
    "@Mukil Loganathan",
    "@Wei Wong",
    "@Brace Sproul",
]

TEAM_TO_SLACK = {team: handle for team, handle in zip(teams, slack_handles)}

### LLM 

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0) 

### State

class Take(BaseModel):
    title: str = Field(
        description="Punchy summary title for the take",
    )
    take: str = Field(
        description="Fun, punchy observation about a specific player",
    )
    source_url: str = Field(
        description="Source data URL for information in the take (if applicable)",
    )
    reddit_url: str = Field(
        description="Reddit post URL for the post",
    )
    reasoning: str = Field(
        description="Provide your reasoning for the take, which confirms that the specific player is on the roster of the Fantasy Manager",
    )

class Takes(BaseModel):
    takes: List[Take] = Field(
        description="A list of takes, each containing a title and a take observation."
    )

class TakeGeneratorOutputState(TypedDict):
    takes: List[Take]

class TakeGeneratorState(TypedDict):
    team: dict
    context: str
    takes: List[Take]

class OverallState(TypedDict):
    league: List[dict]
    context: str
    takes: Annotated[List[Take], operator.add]

### Nodes

def build_team_rosters(state: OverallState):
    """
    Build a list of team rosters with associated Slack handles.

    Args:
    teams (list): A list of Team objects from the ESPN API.
    team_to_slack (dict): A dictionary mapping team names to Slack handles.

    Returns:
    list: A list of dictionaries, each containing a team's Slack handle and list of players.
    Each dictionary has the format:
    {
        "slack_handle": str,
        "players": list[str]
    }
    """
    # Get league data
    league = League(league_id=ESPN_LEAGUE_ID, 
                    year=2024, 
                    espn_s2=ESPN_S2, 
                    swid=ESPN_SWID)

    # Slack handle -> roster mapping
    teams = league.teams

    roster_list = []
    
    for team in teams:
        team_name = team.team_name
        slack_handle = TEAM_TO_SLACK.get(team_name, "Unknown")
        
        players = [player.name for player in team.roster]
        
        roster_dict = {
            "slack_handle": slack_handle,
            "players": players
        }
        
        roster_list.append(roster_dict)
    
    return {"league": roster_list}

def load_context(state: OverallState):
    """ Generate context from Reddit """
    
    # Replace with the subreddit you're interested in
    subreddit_name = 'fantasyfootball'
    
    # Get top comments from past <day, month, etc>
    filter_to_use = 'day'
    
    # Number of posts to gather
    number_of_posts = 10
    
    # Number of top comments to gather per post
    number_of_comments = 5

    # Pull recent posts 
    reddit_recent_posts = get_recent_reddit_posts(subreddit_name,
                                                  filter_to_use,
                                                  number_of_posts,
                                                  number_of_comments)

    return {"context": reddit_recent_posts}

take_instructions="""Your job is to generate fun, punchy takes for a Fantasy Football manager about the players on his / her team.

Carefully review and memorize the list of players on the manager's team provided by the manager at the end of these instructions. 

This list of players is definitive and should be used as the sole reference for the manager's team composition.

Examine the recent news and events in the world of the NFL provided below.

For each news item, systematically cross-reference it against the memorized list of the manager's players. 

IMPORTANT: Only generate takes for players who are EXPLICITLY and DIRECTLY mentioned by name in the news items. Do not infer, extrapolate, or generate takes based on indirect implications or general trends that might affect a player.

If and only if a news item specifically mentions a player by name, and that player is on the manager's team, generate a take about that player.

Each take should be player-specific and based solely on the provided news. Do not include speculation or information from outside the given news items.

Create a numbered list of takes and format each take as follows:

Include a concise and fun subject line
Start with "Hey {manager}:" and then provide a brief summary of the news, focusing only on what is directly stated about the player
Include the exact Source URL of the news item, if provided
Include the exact Reddit post URL of the news item
Provide your reasoning for the take, which confirms that the specific player is on the roster of the Fantasy Manager

After generating each take, double-check that the player mentioned is indeed on the manager's team by referring back to the original list.

If no news items directly mention any players on the manager's team by name, explicitly state that no relevant news was found for the team's players.

Before finalizing your response, review all generated takes and confirm once more that each mentioned player is on the manager's team as listed at the beginning of the prompt and is explicitly named in the news item.

If a player is not directly named in the news or you're unsure about whether a player is on the team, do not generate a take for that player.

Here are the recent news and events in the world of the NFL to base your takes on: {context}"""

take_format_instructions="""Your job is to review and then format a final list of fun, punchy takes for a Fantasy Football manager about the players on his / her team.

Review Phase:
1. First, check if any takes are provided in the list of takes. If the list of takesis empty or contains no takes, provide no output and end the process.

2. If there are takes provided, then carefully review and memorize the list of players on the manager's team provided at the end of these instructions. This list is definitive and should be used as the sole reference for the manager's team composition.

3. For each take in the list of takes, verify that:
   a) The player mentioned is EXPLICITLY and DIRECTLY named in the take.
   b) The player is on the manager's team (as per the provided list).
   c) The take is based solely on the information provided within the list of takes.

4. Discard any takes that do not meet ALL of the above criteria.

Here is the list of takes to review:

{context}

---

Formatting Phase:
If any takes remain after the review phase, format each take as follows:

1. Include a concise and fun subject line
2. Start the summary with "Hey {manager}:" and then provide a brief summary of the news, focusing only on what is directly stated about the player
3. Include the exact Source URL of the news item, if provided
4. Include the exact Reddit post URL of the news item
5. End with your reasoning for the take, which confirms that the specific player is on the roster of the Fantasy Manager

Final Check:

Before finalizing your response, review ALL formatted takes once more to ensure they meet all criteria.

Ensure that the summary of EACH formatted take starts with "Hey {manager}:".

If no takes remain after the review process, provide no output."""

def generate_takes(state: TakeGeneratorState) -> TakeGeneratorOutputState:
    """ Node to generate takes, and review / format them """

    # Get team
    team = state["team"]
    context = state["context"]

    # Get player and manager
    manager = team['slack_handle']
    players = ' // '.join(player for player in team['players'])

    # Instructions
    take_system_promot = take_instructions.format(manager=manager, context=context)
    take_human_message = "Only generate takes if any of these players are EXPLICITLY and DIRECTLY in the news. Here are the players: {players}".format(players=players)
    
    # Generate takes
    takes = llm.invoke([SystemMessage(content=take_system_promot)]+[HumanMessage(content=take_human_message)])

    # Enforce structured output
    structured_llm = llm.with_structured_output(Takes)
    take_formatting_system_promot = take_format_instructions.format(manager=manager, context=takes.content)
    take_formatting_human_message = "Only generate your final, formatted takes if any of these players are EXPLICITLY and DIRECTLY in the provided list of takes. Here are the players: {players}".format(players=players)
 
    # Generate takes
    formatted_takes = structured_llm.invoke([SystemMessage(content=take_formatting_system_promot)]+[HumanMessage(content=take_formatting_human_message)])
    
    # Write to state  
    return {"takes": [formatted_takes]}

def initiate_all_takes(state: OverallState):
    """ This is the "map" step to initiate takes per team """    

    league = state["league"]
    context = state["context"]
    return [Send("generate_takes", {"team": team,
                                    "context": context}) for team in league]

def write_to_slack(state: OverallState):
    """ Write takes to Slack """
    
    # Full set of interview reports
    takes = state["takes"]

    # Write to your Slack Channel via webhook
    true = True
    headers = {
        'Content-Type': 'application/json',
    }

    # Write to slack
    for t in takes:
        for take in t.takes:
            
            # Blocks
            blocks = []
            
            # Block 1: Title section
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{take.title}*"
                }
            })
            
            # Block 2: Divider
            blocks.append({
                "type": "divider"
            })
            
            # Block 3: Content section
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{take.take}"
                }
            })

            # Block 4: Divider
            blocks.append({
                "type": "divider"
            })

            # Block 5: Source
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Source: {take.source_url}" 
                }
            })

            # Block 6: Divider
            blocks.append({
                "type": "divider"
            })

            # Block 7: Reddit post
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Reddit post: {take.reddit_url}"
                }
            })
            
            blocks.insert(0, {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":fire: :robot_face: Take-Bot is heating up ...",
                    "emoji": true
                }
            })
            
            data = {
                "blocks": blocks,
                "unfurl_links": True,
                "unfurl_media": True,
            }
            
            response = requests.post(take_bot_url, headers=headers, json=data)

# Add nodes and edges 
overall_builder = StateGraph(OverallState)

# Add nodes and edges 
overall_builder.add_node("build_team_rosters", build_team_rosters)
overall_builder.add_node("load_context", load_context)
overall_builder.add_node("generate_takes", generate_takes)
overall_builder.add_node("write_to_slack",write_to_slack)

# Flow
overall_builder.add_edge(START, "build_team_rosters")
overall_builder.add_edge("build_team_rosters", "load_context")
overall_builder.add_conditional_edges("load_context", initiate_all_takes, ["generate_takes"])
overall_builder.add_edge("generate_takes", "write_to_slack")
overall_builder.add_edge("write_to_slack", END)

# Compile without interruption for cron job writing to Slack 
graph = overall_builder.compile()
