#!/usr/bin/env python3
# FreeData API example
# 2024 Kelly Keeton K7MHI

ADDRESS = 'localhost'
PORT = 5000
URL = f'http://{ADDRESS}:{PORT}'
userURL = f'{URL}/user'
radioURL = f'{URL}/radio'
messageURL = f'{URL}/freedata/messages'
RESPONSE = "Hello, I am away from the radio right now, but my FreeData BOT says Hello Back!"
TRAP = "hello"

import requests
import time
import pickle

try:
    # make a request to the API
    response = requests.get(URL)
    data = response.json()

    # extract data from response
    name = data['name']
    modemVersion = data['modem_version']
except requests.exceptions.RequestException as e:
    print(f'Failed to connect to {URL} due to {e}')
    exit(1)

# Validate the response as expected
if name != 'FreeDATA API':
    print(f'Expected FreeDATA API, got {name}')
    exit(1)

def get_radio():
    # get the radio status
    response = requests.get(radioURL)
    data = response.json()
    radio = data['radio_status']
    frequency = data['radio_frequency']

    if radio == True:
        #print ("Radio are connected Successfully detected on frequency: " + str(frequency))
        return True
    else:
        #print ("no radio detected")
        return False

def get_most_recent_message():
    response = requests.get(messageURL)
    data = response.json()
    # for each message, get the message data
    message_count = data['total_messages']
    messages = data['messages']

    # local message database
    msgDb = [] # id, timestamp, direction, origin, body

    if message_count == 0:
        return "No messages"
    else:
        for message in messages:
            # parse the message data
            id = message['id']
            timestamp = message['timestamp']
            direction = message['direction']
            orgin = message['origin']
            body = message['body']
            # add the values to the message database for today only
            if time.strftime('%Y-%m-%d') in timestamp:
                msgDb.append((id, timestamp, direction, orgin, body))

    # if no messages for today, return no messages
    if len(msgDb) == 0:
        return "No messages"
    
    # sort msdDb by timestamp
    msgDb.sort(key=lambda x: x[1])

    # get the most recent message
    mostRecent = msgDb[-1]

    if mostRecent[2] != 'receive':
        # keep looking for the most recent received message
        for msg in reversed(msgDb):
            if msg[2] == 'receive':
                mostRecent = msg
                break

    return mostRecent

def transmit_text_message(messageBody, destination):
    # send a message
    response = requests.post(messageURL, json={'body': messageBody, 'destination': destination})
    data = response.json()
    return data

def save_last_messageId(messageId):
    # save the last message id to a file
    pickle.dump(messageId, open("lastMessageId.dat", "wb"))


# Main rx loop
print(f"\nStarting FreeData BOT, connected to {URL} with modem version {modemVersion}\n CTL+C to exit\n")

while True:
    try:
        msg = get_most_recent_message() #returns: id, timestamp, direction, origin, body

        # check if the bot has already replied to this message
        try:
            lastMsgId = pickle.load(open("lastMessageId.dat", "rb"))
        except:
            # if the file does not exist, create it
            save_last_messageId(123)
            lastMsgId = 123

        if msg[0] == lastMsgId or msg[4] == "No messages" or "I am a bot" in msg[4]:
            # Bot has already replied to this message, or no messages to reply to
            time.sleep(15)
            continue
        else:
            # if the message body includes trap var then send a message
            if TRAP in msg[4].lower():
                print(f"Received message: {msg[4]}")
                print(f"Sending bot message to {msg[3]}")

                if get_radio() == True:
                    transmit_text_message(RESPONSE, msg[3])
                    # write the message unique ID to a file to prevent multiple replies
                    save_last_messageId(msg[0])
                else:
                    print("No radio detected, message not sent")
        
    except KeyboardInterrupt:
        print("\nExiting FreeData BOT")
        exit(0)
