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


def onNewQuestion(event_data):
    channel = event_data['event']['channel']

    if channel != PRIVATE_CHANNEL:
        return None

    text = event_data['event']['text']
    ts = event_data['event']['ts']
    # ts without the '.' - the format that the link takes for some reason
    tss = ts.replace('.', '')
    user = event_data['event']['user']

    if not checkReaction:
        return None

    res = postQuestion(
        question=text[1:],
        topic=f'''<https://{WORKSPACE_NAME}.slack.com/archives/{PUBLIC_CHANNEL}/p{tss}|Today\'s Topic!>
        Respond in threads only please!
        :hackclub:
        :wave::skin-tone-4:
        :revolving_hearts:'''
    )

    addReaction('heavy_check_mark', channel, ts)

    pinMessage(
        PUBLIC_CHANNEL,
        res
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
        print("Message was sent in public channel, ignoring!")
        return ('', 200)

    if message[0] != '?':
        print('Message started with !, ignore!')
        return ('', 200)

    elif channel[0] == ('G'):
        print('New Question was posted!')
        onNewQuestion(event_data)

    return ('', 200)


def addReaction(reaction, channel, ts):
    web_client.reactions_add(
        name=reaction,
        token=SLACK_BOT_USER,
        channel=channel,
        timestamp=ts
    )


def checkReaction(reaction, channel, ts):
    reactions = web_client.reactions_get(
        token=BOT_TOKEN,
        channel=channel,
        timestamp=ts
    )
    if reactions['message']['reactions'][0]['count'] == 1:
        print('Reaction found!')
        return True
    else:
        return False


def updateTopic(topic, channel):  # Helper method to update channel topic
    return web_client.conversations_setTopic(
        channel=channel,
        topic=topic
    )


def postPlainMessage(text, channel):
    web_client.chat_postMessage(
        token=BOT_TOKEN,
        text=text,
        channel=channel,
        icon_emoji='interrobang',
        username='Interrobang'

    )


def postEphemeralMessage(text, channel, uid):
    return web_client.chat_postEphemeral(
        channel=channel,
        user=uid,
        text=text,
        as_user=True
    )


def deleteMessage(channel, ts):
    return json.loads(
        requests.get(
            f'https://slack.com/api/chat.delete?token={ADMIN_TOKEN}&ts={ts}&channel={channel}&pretty=1'
        ).text
    )


def pinMessage(channel, ts):
    return web_client.pins_add(
        token=BOT_TOKEN,
        timestamp=ts,
        channel=channel
    )


def getLastMessage(channel):
    res = json.loads(
        requests.get(
            f'https://slack.com/api/conversations.history?token={BOT_TOKEN}&channel={channel}&limit=1&pretty=1'
        ).text
    )
    return res


def postQuestion(question, topic):
    day = str(date.today())  # gets today's date
    postPlainMessage(
        text=f'Topic for {day}: \n\n {question}',
        channel=PUBLIC_CHANNEL
    )

    tss = getLastMessage(PUBLIC_CHANNEL)['messages'][0]['ts'].replace(
        '.', '')  # returns ts sans-period

    updateTopic(
        topic=f'<https://{WORKSPACE_NAME}.slack.com/archives/{PUBLIC_CHANNEL}/p{tss}|*Today\'s topic!*> Respond in threads only please :D',
        channel=PUBLIC_CHANNEL
    )

    deleteMessage(
        channel=PUBLIC_CHANNEL,
        ts=getLastMessage(PUBLIC_CHANNEL)['messages'][0]['ts']
    )

    return getLastMessage(PUBLIC_CHANNEL)['messages'][0]['ts']


# starting server?
events_client.start(host='0.0.0.0', port=3000, debug=True)
