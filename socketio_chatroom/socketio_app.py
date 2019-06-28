import json
import time
from collections import defaultdict
from threading import Thread
from uuid import uuid4

import eventlet
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from redis import StrictRedis

eventlet.monkey_patch(socket=True)
tickers = ['abc_usdt', 'def_usdt', 'ghi_btc']

app = Flask(__name__)
app.config['SECRET_KEY'] = str(uuid4())
sio = SocketIO(app)
sio.init_app(app, async_mode='eventlet', message_queue='redis://127.0.0.1:6379')
subscribed_rooms = defaultdict(int)
valid_rooms = (1201, 1202, 1203, 1204)
sock_clients = dict()
rds = StrictRedis.from_url('redis://127.0.0.1:6379')
user_rooms = defaultdict(set)


def subscribe_push(sock):
    global subscribed_rooms
    r = rds.pubsub()
    r.subscribe('ticker_update')
    while True:
        message = r.get_message(ignore_subscribe_messages=True)
        if not message:
            time.sleep(0.1)
            continue
        data = json.loads(message['data'], encoding='utf-8')
        r_count = subscribed_rooms.copy().get(data['market_id'])
        if r_count and r_count > 0:
            sock.emit('ticker_response',
                      {'data': data, 'room': data['market_id']}, room=data['market_id'], namespace='/ticker')


@app.route('/')
def index():
    return render_template('index.html')


@sio.on('connect', namespace='/ticker')
def on_connect():
    emit('log', {'level': 'info', 'text': 'connected...'})


@sio.on('ping', namespace='/ticker')
def on_ping(_):
    emit('pong', int(time.time() * 1000))


@sio.on('join', namespace='/ticker')
def on_room(data):
    data['room'] = int(data['room'])
    global subscribed_rooms
    if data['room'] not in valid_rooms:
        emit('log', {'level': 'error', 'text': 'room [{}] not found'.format(data['room'])})
    else:
        join_room(data['room'])
        user_rooms[request.sid].add(data['room'])
        subscribed_rooms[data['room']] += 1
        emit('log',
             {'level': 'info', 'text': 'join room [{}], rooms now: {}'.format(data['room'], user_rooms[request.sid])})


@sio.on('leave', namespace='/ticker')
def off_room(data):
    data['room'] = int(data['room'])
    global subscribed_rooms
    if data['room'] not in user_rooms[request.sid]:
        emit('log', {'level': 'error', 'text': 'client not subscribe [{}]'.format(data['room'])})
    else:
        leave_room(data['room'])
        user_rooms[request.sid].remove(data['room'])
        subscribed_rooms[data['room']] -= 1
        emit('log',
             {'level': 'info', 'text': 'leave room [{}], rooms now: {}'.format(data['room'], user_rooms[request.sid])})


if __name__ == '__main__':
    Thread(target=subscribe_push, args=(sio,)).start()
    sio.run(app)
