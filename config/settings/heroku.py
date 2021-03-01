import django_heroku

from .base import *


ALLOWED_HOSTS = [
    'https://beverage-shop.herokuapp.com'
]

BASE_URL = 'https://beverage-shop.herokuapp.com'

DEBUG = False

django_heroku.settings(locals(), staticfiles=False)
