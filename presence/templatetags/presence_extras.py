from django import template
from functools import partial

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='call_attr')
def call_attr(obj, attr_name):
    attr = getattr(obj, attr_name, None)
    if callable(attr):  # ça couvre les partial aussi
        return attr()
    return attr
