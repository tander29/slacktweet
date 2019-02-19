# About this project:

Python program that connects two API's - slackclient and tweepy(Twiiter):

User's who have slack can access twitter firehose feed.

Creators: Travis Anderson and Aaron Jackson

Focal Points:
Tweepy - Travis
Slackclient - Aaron
Logging and logic to run both bots: both individuals

# To run locally:

This requires some work, slack and twitter requirements are below.

Python requires pipenv to replicate environment from Pipfile.  
\$pipenv install

Run program from the pipenv shell or push to heroku.

\$pipenv shell

> see set log level for next command to start up locally

#Env Variables:
Will need environment variables for slack bot, tweepy(twitter), and slack channel

# Slack Set Up:

You will need `admin` to create a bot application.

Have slack installed, create a new bot. Acquire keys as noted by .env.example file from the slack bot creation webportal:
https://api.slack.com

Create .env file, or set .env variables manually in terminal or on start up.

Slack is subscribed and listening to a single channel, but posting to a separate channel.
Why - For popular keywords the twitter stream can overwhelm the slack client commands if in same channel, so separate channels were created for ease of slack to listen to commands.

# Twitter Set-up:

You will need to set up a twitter account. You can use your own existing account, or create a new one. The important part is to register for developer API access. This is a new requirement since July 2018. You will need to fill out a short questionnaire about your intended usage of the developer account.

https://developer.twitter.com/en.html (Links to an external site.)Links to an external site.
Once you have been approved for developer access, you must create a twitter app. Then use the Keys and Tokens tab to generate a pair of Consumer keys and a pair of Access keys.

# SETTING LOG LEVEL

log level can be set at time of running file local or by update argument in the procfile for heroku.

local command ---> python slack.py -l (level)

accepts critical, error, warning, info, debug. (capitalization does not matter)

defaults to info level if nothing is provided.

# Log Info

Logs info into terminal and into log files. Log files in .gitignore, will not see on repo.

Example of items log: attempting to connect to twitter, confirmation time connected to twitter, exiting twitter, commands a user entered in slack

# Bot info

Both bots use context manager, to get the integration between the two items, the slack instance gives the twitter instance a function off of slack, that the twitter instance can run. This helps reduce multithreading

To handle the tweepy stream, needed multi-threading on the tweepy bot, had to do a monkey patch and reset one of the functions (\_start) to allow for multi-threading.

# Pushing to heroku:

Follow instructions
https://devcenter.heroku.com/articles/getting-started-with-python

Remember to set terminal sessions env variables, need proc file, runtime.txt with python version
