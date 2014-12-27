from django.shortcuts import render

import decimal

# TODO: name could use improving here.
class DisplayInformation():
    def __init__(self, name, structure, keys, processor, format_key):
        self.name = name
        self.structure = structure
        self.keys = keys
        self.processor = processor
        self.format_key = format_key
        # TODO: put further checks here? That or document what structure you're
        # expecting to get.
        try:
            assert sum(len(section_subsections) for section_subsections in
                       self.structure['subsections']) == len(self.keys)
        except AssertionError as e:
            raise AssertionError(
                self.structure['subsections'], self.keys
            )

    def load_data(self, data):
        self.data = {
            key: (data[key][self.format_key] if self.format_key is not None
                  else data[key]) for key in self.keys
        }

    # TODO: document this or whatever. Figure out the right way.
    def process_data(self):
        # TODO: at the beginning have it just take these in.
        self.data = {
            key: self.processor(item) for key, item in
            self.data.items()
        }

    def populate_structure(self):
        self.structured_data = []
        key_index = 0
        for i, section in enumerate(self.structure['sections']):
            self.structured_data.append({'title': section, 'sections': []})
            # Assuming this is only called once, so that the dictionary we just
            # appended is located at index `i`.
            for subsection in self.structure['subsections'][i]:
                self.structured_data[i]['sections'].append(
                    {
                        'title': subsection,
                        'dictionaries': [
                            dict_ for dict_ in self.data[self.keys[key_index]]
                        ]
                    }
                )
                key_index += 1

    def purge_empty(self):
        # Filter subsections.
        for big_dict in self.structured_data:
            # Using mutability/fact that `self.structured_data` stores
            # references to objects.
            big_dict['sections'] = [item for item in big_dict['sections'] if
                                    item['dictionaries']]
        # Filter sections.
        self.structured_data = [big_dict for big_dict in self.structured_data
                                if big_dict['sections']]
        return None

    def create_template_data(self, data):
        self.load_data(data)
        self.process_data()
        self.populate_structure()
        self.purge_empty()
        return self.structured_data

def format_balance(load=None, balance=None):

    def sign_int(balance):
        balance = int(balance.to_integral_value())
        if balance >= 0:
            return '+{bal}'.format(bal=balance)
        else:
            return '−{bal}'.format(bal=abs(balance))

    endpoints = (-float('inf'), -0.35, -0.15, 0.15, 0.35, float('inf'))
    CSS_classes = ('very_low_balance', 'low_balance', 'OK_balance',
                   'high_balance', 'very_high_balance')
    assert len(endpoints) == len(CSS_classes)+1

    try:
        ratio = balance/load
    except decimal.DivisionByZero:
        ratio = endpoints[-1]+1 if balance >= 0 else endpoints[0]-1
    except decimal.InvalidOperation:
        #Assuming both `balance` and `load` are `0` here.
        #TODO: any other scenarios to consider?
        ratio = 0
    for i, CSS_class in enumerate(CSS_classes):
        if endpoints[i] <= ratio < endpoints[i+1]:
            # We will use the value of `CSS_class`. If we never make it to this
            # block, `CSS_class` will end up `CSS_classes[-1]`.
            break
    return {
        'value': balance,
        'formatted_value': sign_int(balance),
        'html_title': 'Exact value: {val}'.format(val=balance),
        'CSS_class': ' '.join(('balance', CSS_class)),
    }

#TODO: this should be handled as a static page. Not sure how to get that
#working with templates.
def about(request):
    return render(request, 'utilities/about.html')
