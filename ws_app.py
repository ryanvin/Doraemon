from websocket_server import WebsocketServer
from threading import Thread
import time
import random

clients = dict()
ticker_clients = dict()


def ping(server):
    while True:
        for cid, client in clients.items():
            server.send_message(client, 'ping to [{}]: {}'.format(cid, time.time()))
        time.sleep(2)


def ticker(server):
    while True:
        for _, client in ticker_clients.items():
            server.send_message(client, 'abc_usdt: {}'.format(random.random()))
        time.sleep(3)


def new_client(client, server):
    clients.setdefault(client['id'], client)
    server.send_message(client, 'id: {} connected'.format(client['id']))
    print('{} clients in all'.format(len(clients)))


def drop_client(client, server):
    clients.pop(client['id'])
    print('{} clients in all'.format(len(clients)))


def on_message(client, server, message):
    if message == 'ticker' and client['id'] in clients:
        ticker_clients.setdefault(client['id'], client)
    if message == 'cancel_ticker' and client['id'] in clients:
        ticker_clients.pop(client['id'])


server = WebsocketServer(port=5000, host='0.0.0.0')

server.set_fn_new_client(new_client)
server.set_fn_client_left(drop_client)
server.set_fn_message_received(on_message)
Thread(target=ping, args=(server,)).start()
Thread(target=ticker, args=(server,)).start()

server.run_forever()

if __name__ == '__main__':
    pass
