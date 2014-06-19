######################
# DELETE ME WHEN READY
######################

def transpose(dictionaries, keys=None):
    '''
    Returns a dictionary with keys `keys` and values lists whose elements are
    the associated values of the dictionaries in `dictionaries`.
    '''
    if keys is None:
        keys = set.intersection(*(set(dictionary.keys()) for dictionary in
                                dictionaries))
    return {
        key: [dictionary[key] for dictionary in dictionaries] for key in keys
    }

def consolidate(dictionaries, keys=None):
    '''
    Returns a dictionary with keys `keys` and values itertools chain objects
    composed of the associated values of the dictionaries in `dictionaries`.
    '''
    if keys is None:
        keys = set.intersection(*(set(dictionary.keys()) for dictionary in
                                dictionaries))
    return {
        key: itertools.chain(*(dictionary[key] for dictionary in dictionaries))
        for key in keys
    }

# TODO: this seems like more trouble that it is worth.
def structure(data, form):
    if callable(form):
        return form(data)
    elif form is None:
        return data
    # TODO: how could we replace these two calls to `isinstance`? Does some
    # attribute or method distinguish dictionaries and lists, tuples, etc.?
    elif isinstance(form, type([])):
        assert len(form) == 1
        return [structure(item, form[0]) for item in data]
    elif isinstance(form, type({})):
        # Recall that the keys of a dictionary don't have any guaranteed order,
        # so they are stored them in a list.
        assert isinstance(form['_ordered_keys'], type([]))
        return {
            key: structure(value, form[key]) for key, value in
            zip(form['_ordered_keys'], data)
        }
    else:
        raise TypeError('Unrecognized form type {typ}.'.format(typ=type(form)))

# TODO: this could be better, definitely, but I'm not sure how to do it.
FORM = {
    '_ordered_keys': ['title', 'sections'],
    'title': None,
    'sections': [
        {
            '_ordered_keys': ['title', 'sections'],
            'title': None,
            'sections': [
                {
                    '_ordered_keys': ['title', 'items', 'total',
                                      'concatenated_items'],
                    'title': None,
                    'items': None,
                    'total': None,
                    'concatenated_items': None,
                }
            ]
        }
    ]
}
LIST_DATA = [
    'Selected Information',
    [
        ['Chores',
         [['Upcoming', my_chores_upcoming, sum_chores],
          ['Needing Sign Off', my_chores_needing_sign_off, sum_chores]],
        ],
        ['Stewardships and Similar',
         [['Stewardships', my_classical_stewardships, sum_chores],
          ['Special Points', my_special_points, sum_chores],
          ['Loans', my_loans, sum_chores]]
        ],
        ['Benefit Changes',
         [['Absences', my_absences, lambda x: None],
          ['Share Changes', my_share_changes, lambda x: None]]
        ],
    ]
]
TABLE_DATA = [
    'Summary Information',
    [
        ['Summary',
         [['Load', my_accounts['load'], lambda x: None],
          ['Credits', my_accounts['credits'], lambda x: None],
          ['Balance', my_accounts['balance'], lambda x: None]]
        ],
        ['Chores',
         [['Signed Up', my_chores, sum_chores],
          ['Signed Off', my_chores_signed_off, sum_chores],
          ['Needing Sign Off', my_chores_needing_sign_off, sum_chores],
          ['Voided', my_chores_voided, sum_chores]]
        ],
        ['Stewardships and Similar',
         [['Stewardships', my_classical_stewardships, sum_chores],
          ['Special Points', my_special_points, sum_chores],
          ['Loans', my_loans, sum_chores]]
        ]
    ]
]










































