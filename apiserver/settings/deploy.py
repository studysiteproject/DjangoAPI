from .base import *

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.mysql',
        'ENGINE': 'mysql.connector.django',
        'NAME': 'sitedb_test',
        'USER': 'root',
        'PASSWORD': 'password1!',
        'HOST': '52.78.216.119',
        # 'HOST': 'projectdatabase.chu2aut3rs5k.ap-northeast-2.rds.amazonaws.com',
        'PORT': '3306',
    }    
}