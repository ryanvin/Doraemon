"""
python3.6+
pip3 install tronapi
pip3 install https://github.com/ryanvin/toolbox/archive/master.zip
"""
import csv
import sys
import time
from datetime import datetime
from toolbox.logger import BasicLogger
from tronapi import HttpProvider
from tronapi import Tron
import os

log = BasicLogger('trx_sender', os.path.dirname(os.path.abspath(__file__)) + '/log', 'INFO')


def load_addr_single(filename):
    addr_all = dict()
    with open(filename, 'r') as f:
        w = csv.DictReader(f)
        for row in w:
            addr_all.setdefault(row['addr'], 0)
            addr_all[row['addr']] += float(row['amount'])
        return addr_all


class TronClient(object):

    def __init__(self, private_key=None, default_address=None):
        full_node = HttpProvider('https://api.trongrid.io')
        solidity_node = HttpProvider('https://api.trongrid.io')
        event_server = HttpProvider('https://api.trongrid.io')
        self.tron = Tron(full_node=full_node,
                         solidity_node=solidity_node,
                         event_server=event_server)
        self.tron.private_key = private_key
        self.tron.default_address = default_address

    def create_account(self):
        account = self.tron.create_account
        is_valid = bool(self.tron.isAddress(account.address.hex))
        log.info(f"Private Key: {account.private_key}\n"
                 f"Public Key: {account.public_key}\n"
                 f"Addr Base58: {account.address.base58}\n"
                 f"Addr Hex: {account.address.hex}\n"
                 f"Addr Status: {'valid' if is_valid else 'invalid'}")
        return account if is_valid else None

    def get_account(self, address):
        account_info_from = self.tron.trx.get_account(address)
        log.info(account_info_from)

    def send_transaction(self, to, amount):
        send = self.tron.trx.send_transaction(to, float(amount))
        return send

    def validate_addr(self, address):
        try:
            is_valid = bool(self.tron.isAddress(self.tron.address.to_hex(address)))
        except Exception as err:
            is_valid = False
            log.info(err)
        return is_valid

    def get_confirmed_tx(self, tx_hash):
        try:
            tx = self.tron.trx.get_transaction(tx_hash, is_confirm=True)
            return tx
        except Exception as err:
            log.info(err)
            return None


def batch_send():
    action = str(sys.argv[1]) if len(sys.argv) > 1 else None
    filename = sys.argv[2] if len(sys.argv) > 2 else 'trx_sent.csv'
    _pk = ''
    _addr = ''
    tc = TronClient(_pk, _addr)
    if action == 'send':
        wallet_balance = tc.tron.trx.get_balance(_addr, is_float=True)
        log.info(f'钱包余额: {wallet_balance}')
        total = 0
        addr_list = []
        for addr, amount in load_addr_single(filename).items():
            if not tc.validate_addr(addr):
                log.info(f'无效地址: {addr}')
                continue
            else:
                addr_list.append((addr, float(amount)))
                total += (float(amount) + 0.1)
        if total > wallet_balance:
            log.info('余额不足, 需要 {}'.format(total))
            return False
        if total <= wallet_balance and addr_list:
            ans = input(f'检查完毕，地址数 {len(addr_list)}，总额 {total}, 是否开始打币[yes/no]: ')
            if ans == 'no':
                return False
            sent_amount = 0
            dt = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f'transaction_history/trx_sent_{dt}.csv', 'a') as f:
                writer = csv.DictWriter(f, ['time', 'address', 'amount', 'tx_hash'])
                writer.writeheader()
                for addr, amount in addr_list:
                    result = 'fail'
                    try:
                        send = tc.send_transaction(addr, amount)
                        if send.get('result', False):
                            tx_hash = send.get('transaction', {}).get('txID', '')
                            writer.writerow({
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'address': addr,
                                'amount': amount,
                                'tx_hash': tx_hash
                            })
                            result = 'success'
                            sent_amount += amount
                            time.sleep(0.2)
                        else:
                            raise ValueError(send)
                    except Exception as e:
                        log.error(e)
                    log.info(f"{addr} {amount} {result}")
            log.info(f'批量发币完成，总发币 {sent_amount}')
    if action == 'check':
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            total = 0
            unconfirmed = 0
            for row in reader:
                total += 1
                tx_hash = row['tx_hash']
                tx = tc.get_confirmed_tx(tx_hash)
                if not tx:
                    log.warning(tx_hash, 'unconfirmed!')
                    unconfirmed += 1
            log.info(f'总交易笔数 {total}, 未满足确认数交易笔数 {unconfirmed}')


if __name__ == '__main__':
    batch_send()
