from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import random
from threading import Timer
import eventlet
from redis import StrictRedis
from collections import defaultdict

eventlet.monkey_patch(socket=True)
tickers = ['abc_usdt', 'def_usdt', 'ghi_btc']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fashdoi03whioealsd0q9ef0'
sio = SocketIO(app)
sio.init_app(app, async_mode='eventlet', message_queue='redis://127.0.0.1:6379')
rooms = ('okex', 'huobi', 'binance')
sock_clients = dict()
rds = StrictRedis.from_url('redis://127.0.0.1:6379')
user_rooms = defaultdict(list)


def timer_ticker(sio):
    def generate_ticker(roomi):
        tick = random.choice(tickers)
        sio.emit('ticker_response', {'data': '{}: {}'.format(tick, random.random()), 'room': room},
                 namespace='/ticker', room=roomi)

    for room in rooms:
        generate_ticker(room)
    Timer(2, timer_ticker, [sio]).start()


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
    if data['room'] not in rooms:
        emit('log', {'level': 'error', 'text': 'room [{}] not found'.format(data['room'])})
    else:
        join_room(data['room'])
        user_rooms[request.sid].append(data['room'])
        emit('log',
             {'level': 'info', 'text': 'join room [{}], rooms now: {}'.format(data['room'], user_rooms[request.sid])})


@sio.on('leave', namespace='/ticker')
def off_room(data):
    leave_room(data['room'])
    user_rooms[request.sid].remove(data['room'])
    emit('log',
         {'level': 'info', 'text': 'leave room [{}], rooms now: {}'.format(data['room'], user_rooms[request.sid])})


if __name__ == '__main__':
    sio.start_background_task(timer_ticker, sio)
    sio.run(app)
