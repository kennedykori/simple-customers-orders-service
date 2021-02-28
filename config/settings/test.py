from .base import *


####################################################################################################
# Database
####################################################################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['TEST_DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': os.environ['DATABASE_PORT']
    }
}


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


####################################################################################################
# Faker
####################################################################################################

# https://faker.readthedocs.io/en/master/
FAKER = {
    'DEFAULT_LOCALE': 'en_US',
}
