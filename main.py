import slack
import requests
from slackeventsapi import SlackEventAdapter
import json
from datetime import date
import os
from flask import jsonify, request


c = os.environ
SIGNING_SECRET = c['SIGNING_SECRET']
BOT_TOKEN = c['BOT_TOKEN']
ADMIN_TOKEN = c['ADMIN_TOKEN']
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

    return ('', 200)

# event listener for messages
@events_client.on('message')
def onMessage(event_data):

    try:
        channel = event_data['event']['channel']
        message = event_data['event']['text']
    except KeyError:
        return ('', 200)

    if channel == PUBLIC_CHANNEL:
        print("Message was sent in public channel!")
        return ('', 200)

    if message[0] == '!':
        return ('', 200)

    elif channel[0] == ('G'):
        print('Executing private channel')
        execPrivateChannel(event_data)

    return ('', 200)


def addReaction(reaction, channel, ts):
    web_client.reactions_add(
        name=reaction,
        token=SLACK_BOT_USER,
        channel=channel,
        timestamp=ts
    )


def updateTopic(topic, channel):  # Helper method to update channel topic
    res = web_client.conversations_setTopic(
        channel=channel,
        topic=topic
    )
    ts = getLastMessage(channel)['message'][0]['ts']
    deleteMessage(
        channel,
        ts
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
        channel=channel
    )


def pinMessage(channel, ts):
    return web_client.pins_add(
        token=BOT_TOKEN,
        timestamp=ts,
        channel=channel
    )


def getLastMessage(channel):
    return web_client.conversations_history(
        channel=channel,
        limit=1,
        token=ADMIN_TOKEN
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
