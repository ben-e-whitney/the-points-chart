from django.shortcuts import render

import decimal

class TableElement:
    def __init__(self, title=None, CSS_classes=None, content=None):
        self.title = title
        self.CSS_classes = CSS_classes
        self.content = content

class TableParent(TableElement):
    def __init__(self, **kwargs):
        self.children = kwargs.pop('children')
        super().__init__(**kwargs)

def format_balance(load=None, balance=None):

    def sign_int(balance):
        balance = int(balance.to_integral_value())
        if balance >= 0:
            return '+{bal}'.format(bal=balance)
        else:
            return '−{bal}'.format(bal=abs(balance))

    endpoints = (-float('inf'), -0.35, -0.15, 0.15, 0.35, float('inf'))
    possible_CSS_classes = ('very_low_balance', 'low_balance', 'OK_balance',
                   'high_balance', 'very_high_balance')
    assert len(endpoints) == len(possible_CSS_classes)+1

    try:
        ratio = balance/load
    except decimal.DivisionByZero:
        ratio = endpoints[-1]+1 if balance >= 0 else endpoints[0]-1
    except decimal.InvalidOperation:
        #Assuming both `balance` and `load` are `0` here.
        #TODO: any other scenarios to consider?
        ratio = 0
    for i, CSS_class in enumerate(possible_CSS_classes):
        if endpoints[i] <= ratio < endpoints[i+1]:
            # We will use the value of `CSS_class`. If we never make it to this
            # block, `CSS_class` will end up `CSS_classes[-1]`.
            break
    return {
        'value': float(balance),
        'formatted_value': sign_int(balance),
        'html_title': 'Exact value: {val}'.format(val=balance),
        'CSS_class': ' '.join(('balance', CSS_class)),
    }
