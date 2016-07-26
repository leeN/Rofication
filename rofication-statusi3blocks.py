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
    else:
        icon = ''
        app_color = '#cc211d'
        text_color = '#df875f'
    summary = strip_tags(message.summary)
    application = strip_tags(message.application)
    # body = strip_tags(message.body.replace("\n"," "))
    return "<span color='{app_color}'>{application}</span>: <span color='{text_color}'>{summary}</span> {icon} {count}".format(app_color = app_color, application=application, text_color= text_color, summary=summary, icon=icon, count=count)

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

msgs = []
urgent = []
low = []
for a in linesplit(client):
    if len(a) > 0:
        msg = jsonpickle.decode(a)
        msgs.append(msg)
        if Urgency(msg.urgency) is Urgency.critical:
            urgent.append(msg)
        if Urgency(msg.urgency) is Urgency.low:
            low.append(msg)
client.close()
if len(msgs) == 0:
    print('')
    print('')
    exit(0)

urgent_count = len(urgent)
if urgent_count > 0:
    top = urgent[-1]
    is_urgent = True
    ret_code = 33
else:
    top = msgs[-1]
    is_urgent = False
    ret_code = 0

mouse_button = os.getenv("BLOCK_BUTTON")
if mouse_button:
    if mouse_button in ["1", "2"]:
        cmd = "del:{mid}".format(mid=top.mid)
        send_command(cmd)
    elif mouse_button in ["3"]:
        cmd = "dela:{app}".format(app=top.application)
        send_command(cmd)


print(format_message(top, is_urgent, len(msgs)))
print(format_message(top, is_urgent, len(msgs)))
exit(ret_code)
