from redis import StrictRedis
import time
import random
import json

valid_rooms = ('okex', 'huobi', 'binance')
tickers = ['abc_usdt', 'def_usdt', 'ghi_btc']

rds = StrictRedis.from_url("redis://127.0.0.1:6379")

while True:
    room = random.choice(valid_rooms)
    ticker = random.choice(tickers)

    payload = json.dumps(dict(room=room, payload='{}:{}'.format(ticker, random.random())))
    rds.publish('ticker_update', payload)
    time.sleep(0.5)
