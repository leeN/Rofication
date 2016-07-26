#!/usr/bin/env python3
import re
import os
import socket
import jsonpickle
from msg import Urgency


def strip_tags(value):
    "Return the given HTML with all tags stripped."
    return re.sub(r'<[^>]*?>', '', value)


def format_message(message, is_urgent, count):
    if not is_urgent:
        icon = ''
        app_color = '#5fafdf'
        text_color = '#8a8a8a'
        icon_color = '#5fafdf'
    else:
        icon = ''
        app_color = '#cc211d'
        text_color = '#df875f'
        icon_color = '#cc211d'
    summary = strip_tags(message.summary)
    application = strip_tags(message.application)
    # body = strip_tags(message.body.replace("\n"," "))
    return "<span color='{app_color}'>{application}</span>: <span color='{text_color}'>{summary}</span> <span color='{icon_color}'>{icon} {count}</span>".format(app_color = app_color, application=application, text_color= text_color, summary=summary, icon_color=icon_color, icon=icon, count=count)

def send_command(cmd):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect("/tmp/rofi_notification_daemon")
    #print("Send: {cmd}".format(cmd=cmd))
    client.send(bytes(cmd, 'utf-8'))
    client.close()

def linesplit(sock):
    buffer = sock.recv(16)
    buffer = buffer.decode("UTF-8")
    buffering = True
    while buffering:
        if '\n' in buffer:
            (line, buffer) = buffer.split("\n", 1)
            yield line
        else:
            more = sock.recv(16)
            more = more.decode("UTF-8")
            if not more:
                buffering = False
            else:
                buffer += more
    if buffer:
        yield buffer

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect("/tmp/rofi_notification_daemon")
client.sendall(bytes("list", 'utf-8'))

messages = []
urgent = []
#low = []
for line in linesplit(client):
    if len(line) > 0:
        message = jsonpickle.decode(line)
        messages.append(message)
        if Urgency(message.urgency) is Urgency.critical:
            urgent.append(message)
#        if Urgency(message.urgency) is Urgency.low:
#            low.append(message)
client.close()
message_count = len(messages)
if message_count == 0:
    print('')
    print('')
    exit(0)

urgent_count = len(urgent)
if urgent_count > 0:
    message_top = urgent[-1]
    is_urgent = True
    return_code = 0
else:
    message_top = messages[-1]
    is_urgent = False
    return_code = 0

mouse_button = os.getenv("BLOCK_BUTTON")
if mouse_button:
    if mouse_button in ["1", "2"]:
        command_text = "del:{message_id}".format(message_id=message_top.mid)
        send_command(command_text)
    elif mouse_button in ["3"]:
        command_text = "dela:{application}".format(application=message_top.application)
        send_command(command_text)

message_out = format_message(message_top, is_urgent, message_count)
print(message_out)
print(message_out)
exit(return_code)
