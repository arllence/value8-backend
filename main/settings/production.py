from .base import *
if os.getenv('SERVER_DEBUG_MODE') == 'True':
    DEBUG = True
else:
    DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DBNAME'),
        'USER': os.environ.get('DBUSERNAME'),
        'PASSWORD': os.environ.get('DBPASSWORD'),
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'options': '-c search_path={}'.format(os.environ.get('DBSCHEMA'))
        },
        'HOST': str(os.environ.get('DBHOST')),
        'PORT': int(os.environ.get('DBPORT')),

    }
}


TOKEN_EXPIRY = int(os.getenv('TOKEN_EXPIRY_TIME'))

