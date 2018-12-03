from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# How many intents are at max put into the output intent
# ranking, everything else will be cut off
INTENT_RANKING_LENGTH = 10


# modify by fangning 20181028
class Reg_IntentClassifier():

    invest_scope = ['投资策略','投资类型','投资标的','投资范围']

    return_rate = ['收益','业绩']

    manager = ['管理人']

    risk = ['风险','保本']

    period = ['期限','封闭期','赎回','到期']

    amount = ['起投', '起头', '多少钱可以买']

    buy_time = ['募集时间','什么时间可以买']

    coupon = ['优惠','投资券','折扣']

    operation = ['密码','操作', '充值', '取现', '流程','冻结','余额']

    rec = ['推荐']

    @classmethod
    def reg_process(cls, message):
        # type: (Message, **Any) -> None

        intent = {"name": cls.reg_parse(message.text), "confidence": 1.0}
        return intent

    @classmethod
    def reg_parse(cls, text):
        # type: (Text) -> Text

        # _text = text.lower()
        _text = text.replace(' ','')

        def is_present(x):
            return x in _text

        if any(map(is_present, cls.invest_scope)):
            return "invest_scope"
        elif any(map(is_present, cls.return_rate)):
            return "invest_return"
        elif any(map(is_present, cls.manager)):
            return "invest_manager"
        elif any(map(is_present, cls.risk)):
            return "invest_risk"
        elif any(map(is_present, cls.period)):
            return "invest_period"
        elif any(map(is_present, cls.amount)):
            return "invest_amount"
        elif any(map(is_present, cls.buy_time)):
            return "invest_time"
        elif any(map(is_present, cls.coupon)):
            return "invest_coupon"
        elif any(map(is_present, cls.operation)):
            return "operation"
        elif any(map(is_present, cls.rec)):
            return "rec_products"
        else:
            return None

        # if any(map(is_present, cls.operation)):
        #     return "operation"
        # else:
        #     return None