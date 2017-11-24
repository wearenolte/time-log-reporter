from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    res = dictionary.get(key)
    if res == None:
        return ''
    return res


@register.filter
def round_if_not_empty(value):
    if value != '':
        r = round(value, 1)
        if r.is_integer():
            return int(r)
        return r
    return ''

    
@register.filter
def day_of_week(day):
    days = {0: 'S', 1: 'M', 2: 'T', 3: 'W', 4: 'T', 5: 'F', 6: 'S'}
    return days.get(day)

    


@register.filter
def sort_items(items):
    return sorted(items)
