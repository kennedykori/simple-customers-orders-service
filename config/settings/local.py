from .base import *


ALLOWED_HOSTS = ['*']

####################################################################################################
# Database
####################################################################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': os.environ['DATABASE_PORT']
    }
}


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
