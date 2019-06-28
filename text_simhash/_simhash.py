import re

import jieba
import jieba.analyse
import redis
import zhon.hanzi
from simhash import Simhash

jieba.setLogLevel("WARNING")

train_article = """
安徽六安义乌小商品市场旁，家园物业停车场内车辆及货物发生火灾，现场火势很大，浓烟滚滚，
消防人员迅速赶到现场进行扑救，目前火势已得到有效控制，火灾原因正在调查中。"""
test_article = """
首先，我们需要将Queue.Queue和其他两者区分开来，因为它的出现主要用于线程之间的通信，而其他二者主要用作存储数据的工具。
当我们需要实现Condition锁时，就要用Queue.Queue，单纯存储数据则用后两者。"""


class TextHashChecker(object):

    def __init__(self, threshold=3, bit_block_size=16, redis_url='redis://localhost:6379'):
        self.threshold = threshold
        self.bit_block_size = bit_block_size
        self.redis = redis.StrictRedis.from_url(redis_url)
        self.key_prefix = "text_simhash:"

    @staticmethod
    def calculate_hash(text: str) -> int:
        text = re.sub(r"[%s\n]+" % zhon.hanzi.punctuation, "", text)
        split_text = jieba.cut(text)
        return Simhash(split_text).value

    @staticmethod
    def hamming_distance(x: int, y: int):
        return len(list(filter(lambda _n: _n == "1", f"{x ^ y:064b}")))

    def save_split_hash(self, raw_hash: int):
        bit64 = f"{raw_hash:064b}"
        split_bit = [bit64[i:i + self.bit_block_size] for i in range(0, 64, self.bit_block_size)]
        for b in split_bit:
            self.redis.sadd(f"{self.key_prefix}{b}", raw_hash)

    def cal_rds_hash(self, raw_hash: int):
        bit64 = f"{raw_hash:064b}"
        split_bit = [bit64[i:i + self.bit_block_size] for i in range(0, 64, self.bit_block_size)]
        _hamming_distance = {self.threshold + 1}
        hash_all = set()
        for b in split_bit:
            rds_hash = self.redis.smembers(f"{self.key_prefix}{b}")
            if not rds_hash:
                continue
            for _hash in rds_hash:
                hash_all.add(_hash)
        for _hash in hash_all:
            _hamming_distance.add(self.hamming_distance(raw_hash, int(_hash)))
        return min(_hamming_distance)

    def is_text_duplicated(self, text: str):
        is_duplicated = False
        if self.cal_rds_hash(self.calculate_hash(text)) <= self.threshold:
            is_duplicated = True
        self.save_split_hash(self.calculate_hash(text))
        return is_duplicated


if __name__ == '__main__':
    c = TextHashChecker()
    print(c.is_text_duplicated(train_article))
