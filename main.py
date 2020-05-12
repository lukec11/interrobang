import slack
import requests
from slackeventsapi import SlackEventAdapter
import json
from datetime import date
import os


c = os.environ
SIGNING_SECRET = c['SIGNING_SECRET']
BOT_TOKEN = c['BOT_TOKEN']
#ADMIN_TOKEN = c['ADMIN_TOKEN']
WORKSPACE_NAME = c['WORKSPACE_NAME']
PUBLIC_CHANNEL = c['SLACK_CHANNEL']
PRIVATE_CHANNEL = c['PRIVATE_CHANNEL']
SLACK_BOT_USER = c['SLACK_UID']

events_client = SlackEventAdapter(SIGNING_SECRET, endpoint='/slack/events')
web_client = slack.WebClient(token=BOT_TOKEN)


def execPrivateChannel(event_data):
    channel = event_data['event']['channel']

    if channel != PRIVATE_CHANNEL:
        return None

    text = event_data['event']['text']
    ts = event_data['event']['ts']
    # ts without the '.' - the format that the link takes for some reason
    tss = ts.replace('.', '')
    user = event_data['event']['user']

    res = postQuestion(
        question=text,
        topic=f'''<https://{WORKSPACE_NAME}.slack.com/archives/{PUBLIC_CHANNEL}/p{tss}|Today\'s Topic!> 
        Respond in threads only please! 
        :hackclub: 
        :wave::skin-tone-4: 
        :revolving_hearts:'''
    )

    addReaction('heavy_check_mark', channel, ts)

    print(res)

    pinMessage(
        PUBLIC_CHANNEL,
        res['ts']
    )


def execPublicChannel(event_data):

    print('Message was in channel!')
    message = event_data['event']['text']
    ts = event_data['event']['ts']
    user = event_data['event']['user']

    # if 'set the channel topic' in message:
    #     print('Deleting channel topic message')
    #     deleteMessage(ts)

    # if user != SLACK_BOT_USER:
    #     print('Deleting non-slackbot message')
    #     #deleteMessage(PUBLIC_CHANNEL, ts)
    #     warnUser(user)
    # Currently removed because I don't have an admin token


# event listener for messages
@events_client.on('message')
def onMessage(event_data):

    channel = event_data['event']['channel']
    message = event_data['event']['text']

    if message[0] == '!':
        return None

    if channel[0] == ('C'):
        return None
    elif channel[0] == ('G'):
        print('Executing private channel')
        execPrivateChannel(event_data)

    return ('', 200)


def warnUser(user):
    print('Sending warning message to user!')
    postEphemeralMessage(
        """Hi! All top level messages must be questions (asked by the bot). 
        \nIf you want to respond to a question, please do it in that question's thread. 
        \nLet <@UE8DH0UHM> know if if you have questions or if i made a mistake.""",
        PUBLIC_CHANNEL,
        user
    )


def addReaction(reaction, channel, ts):
    web_client.reactions_add(
        name=reaction,
        token=SLACK_BOT_USER,
        channel=channel,
        timestamp=ts
    )


def updateTopic(topic, channel):  # Helper method to update channel topic
    web_client.conversations_setTopic(
        channel=channel,
        topic=topic
    )


def postPlainMessage(text, channel):
    return web_client.chat_postMessage(
        token=BOT_TOKEN,
        text=text,
        channel=channel,
        as_user=True
    )


def postEphemeralMessage(text, channel, uid):
    return web_client.chat_postEphemeral(
        channel=channel,
        user=uid,
        text=text,
        as_user=True
    )


def deleteMessage(channel, ts):
    return web_client.chat_delete(
        token=ADMIN_TOKEN,
        ts=ts,
        channel=channel)


def pinMessage(channel, ts):
    return web_client.pins_add(
        token=BOT_TOKEN,
        timestamp=ts,
        channel=channel
    )


def postQuestion(question, topic):
    day = str(date.today())  # gets today's date
    res = postPlainMessage(
        text=f'Topic for {day}: \n\n {question}',
        channel=PUBLIC_CHANNEL
    )

    channel = res['channel']
    ts = res['message']['ts'].replace('.', '')  # returns ts sans-period

    updateTopic(
        topic=f'<https://{WORKSPACE_NAME}.slack.com/archives/{channel}/p{ts}|*Today\'s topic!*> Respond in threads only please :D', channel=channel
    )

    return res


# starting server?
events_client.start(host='0.0.0.0', port=3000, debug=False)
