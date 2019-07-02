"""
python3.6+
pip3 install requests
pip3 install https://github.com/ryanvin/toolbox/archive/master.zip
"""
import csv
import os
import sys
import time
from datetime import datetime

import requests
from toolbox.logger import BasicLogger

log = BasicLogger('btc_sender', os.path.dirname(os.path.abspath(__file__)) + '/log', 'INFO')
test_conf = dict(
    rpc_addr='http://172.17.3.194:8333',
    property_id=1,  # OMNI
    addr='',
    test_tx='',
)

main_conf = dict(
    rpc_addr='http://172.17.3.245:8333',
    property_id=31,  # USDT
    addr='',
    test_tx='',
)

conf = main_conf


def load_addr_single(filename):
    addr_all = dict()
    with open(filename, 'r') as f:
        w = csv.DictReader(f)
        for row in w:
            addr_all.setdefault(row['addr'], 0)
            addr_all[row['addr']] += float(row['amount'])
        return addr_all


def rpc_call(method, *params):
    _params = {
        "jsonrpc": "2.0",
        "method": method,
        "params": list(params),
        "id": method
    }
    r = requests.post(conf['rpc_addr'], json=_params,
                      headers={'Content-type': 'application/json'},
                      auth=('admin', '123456'))
    try:
        return r.json()
    except Exception as err:
        log.error(err)
        return None


def get_info():
    return rpc_call('getinfo')


def send_to_one(addr, amount):
    _method = 'omni_send'
    r = rpc_call(_method, conf['addr'], addr, conf['property_id'], str(amount))
    print(r)
    return r['result']
    # ok = input(f"send from {conf['addr']} to {addr}, amount: {amount} USDT [y/n]")
    # if ok == 'y':
    #     r = rpc_call(_method, conf['addr'], addr, conf['property_id'], str(amount))
    #     print(r)
    #     return r['result']
    # else:
    #     return None


def batch_send(filename):
    total_amount = 0
    valid_addr = []
    for addr, amount in load_addr_single(filename).items():
        if not verify_addr(addr):
            log.info(f'无效地址: {addr}')
            continue
        valid_addr.append((addr, float(amount)))
        total_amount += float(amount)
    balance_now = get_balance(conf['addr'], conf['property_id'])
    if total_amount > balance_now:
        log.info(f'余额不足, 需要 {total_amount}, 当前余额 {balance_now}')
        return False
    if len(valid_addr) == 0:
        exit('无有效地址')
    ans = input(f'检查完毕，地址数 {len(valid_addr)}，总额 {total_amount}, 是否开始打币[yes/no]: ')
    if ans == 'no':
        return False
    sent_amount = 0
    dt = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'transaction_history/btc_sent_{dt}.csv', 'a') as f:
        writer = csv.DictWriter(f, ['time', 'address', 'amount', 'tx_hash'])
        writer.writeheader()
        for addr, amount in valid_addr:
            result = 'fail'
            try:
                tx = send_to_one(addr, amount)
                if not tx:
                    raise ValueError('send to one not finished')
                writer.writerow({
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'address': addr,
                    'amount': amount,
                    'tx_hash': tx
                })
                result = 'success'
                sent_amount += amount
                time.sleep(1)
            except Exception as e:
                log.error(e)
            log.info(f"{addr} {amount} {result}")
        log.info(f'批量发币完成，总发币 {sent_amount}')


def check(filename):
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        total = 0
        unconfirmed = 0
        for row in reader:
            total += 1
            tx = row['tx_hash']
            _r = get_tx_verify(tx)
            if _r['confirmations'] > 0 and _r['valid']:
                log.info(f"confirmed: {row['address']}, confirmations: {_r['confirmations']}, tx: {row['tx_hash']}")
            else:
                log.warning(tx, 'unconfirmed!')
                unconfirmed += 1
                continue
        log.info(f'总交易笔数 {total}, 未满足确认数交易笔数 {unconfirmed}')


def get_tx_verify(_tx):
    """
    {
      "txid" : "hash",                 // (string) 这个交易的16进制编码交易hash
      "sendingaddress" : "address",    // (string) 发送方的比特币地址
      "referenceaddress" : "address",  // (string) 接收方的比特币地址（如果有）
      "ismine" : true|false,           // (boolean) 表示交易涉及的地址是否在钱包中
      "confirmations" : nnnnnnnnnn,    // (number) 交易被确认的数量
      "fee" : "n.nnnnnnnn",            // (string) 比特币的交易费
      "blocktime" : nnnnnnnnnn,        // (number) 包含交易的区块的出块时间
      "valid" : true|false,            // (boolean) 表示交易是否有效
      "positioninblock" : n,           // (number) 交易在区块中的位置
      "version" : n,                   // (number) 交易的版本
      "type_int" : n,                  // (number) 交易类型号
      "type" : "type",                 // (string) 交易类型字符串
      [...]                            // (mixed) 其他交易类型规格属性
    }
    """
    _method = 'omni_gettransaction'
    r = rpc_call(_method, _tx)
    return r['result']


def get_addresses(name='dfg'):
    r = rpc_call('getaddressesbyaccount', name)
    return r['result']


def get_balance(addr, p_id):
    r = rpc_call('omni_getbalance', addr, p_id)
    if r is None:
        return 0
    return float(r['result']['balance'])


def verify_addr(addr):
    if rpc_call('omni_getbalance', addr, 1).get('error') is not None:
        return False
    return True


def main():
    action = str(sys.argv[1]) if len(sys.argv) > 1 else None
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    if action == 'send':
        batch_send(filename)
    if action == 'check':
        check(filename)


if __name__ == '__main__':
    main()
