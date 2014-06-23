############################
# TO DELETE WHEN COMFORTABLE
############################

def update(dict_, key, data, mode):

    '''
    Construct and update a dictionary of dictionaries piece-by-piece.

    Arguments:
        dict_ -- Data structure being modified.
        key   -- Identifies the entry to create or change.
        data  -- Used to changing the entry.
        mode  -- Dictates how `data` will be used to change the entry.
    '''

    def appender(dict_, key, data):
        dict_[key]['items'].append(data)
        dict_[key]['html_titles'].append(', '.join(str(chore) for chore in
                                                   data))
        return dict_

    def combiner(dict_, key, data):
        # TODO: this seems to be the wrong way to go about it.
        dict_[key]['items'] += list(data)
        return dict_

    options_by_mode = {
        'append': {
            'blank_entry': {'title': None, 'items': [], 'html_titles': []},
            'updater': appender
        },
        'combine': {
            'blank_entry': {'title': None, 'items': []},
            'updater': combiner
        }
    }
    try:
        options = options_by_mode[mode]
    except KeyError as e:
        raise KeyError('Unrecognized mode {mod}.'.format(mod=mode))

    if not key in dict_.keys():
        dict_[key] = options['blank_entry']
        dict_[key]['title'] = key
        return update(dict_, key, data, mode)
    else:
        return options['updater'](dict_, key, data)


