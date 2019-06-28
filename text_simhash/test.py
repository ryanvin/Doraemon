from unittest import TestCase
from _simhash import TextHashChecker
import unittest


class FunctionTest(TestCase):

    def test_simhash(self):
        c = TextHashChecker()
        c.key_prefix = "test:text_hash:"
        for _k in c.redis.keys(f"{c.key_prefix}*"):
            c.redis.delete(_k)
        text_train = "新华社北京6月27日电（记者侯晓晨）外交部发言人耿爽27日在回应美国总统特朗普日前威胁要对中国加征额外关税的提问时说，这吓唬不了中国人民。中国人不信邪、不怕压，从来不吃这一套。"

        text_test_diff = "耿爽说，中方始终主张通过对话协商解决中美经贸摩擦，但同时也会坚定捍卫自己的正当合法权益。“美方威胁要对中方加征额外的关税，这吓唬不了中国人民。中国人不信邪、不怕压，从来不吃这一套。”"

        self.assertFalse(c.is_text_duplicated(text_train))
        self.assertTrue(c.is_text_duplicated(text_train))
        self.assertFalse(c.is_text_duplicated(text_test_diff))


if __name__ == '__main__':
    unittest.main()
