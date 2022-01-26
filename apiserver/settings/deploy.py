from .base import *

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# s3에서 DB에 대한 정보가 저장된 파일을 불러와 설정한다.
s3_resource = boto3.resource('s3')
my_bucket = s3_resource.Bucket(name='deploy-django-api')
SECRET_FILE_DATA = json.loads(json.dumps(yaml.load(my_bucket.Object('secret/deploy_db_info.yml').get()['Body'].read())))
DATABASES = SECRET_FILE_DATA

# s3에서 Email 인증 서버에 대한 정보가 저장된 파일을 불러와 설정한다.
SECRET_MAIL_INFO = json.loads(my_bucket.Object('secret/auth_mail_info.json').get()['Body'].read())
EMAIL_BACKEND = SECRET_MAIL_INFO['EMAIL_BACKEND']
EMAIL_HOST = SECRET_MAIL_INFO['EMAIL_HOST']
EMAIL_HOST_USER = SECRET_MAIL_INFO['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = SECRET_MAIL_INFO['EMAIL_HOST_PASSWORD']
EMAIL_PORT = SECRET_MAIL_INFO['EMAIL_PORT']
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DEBUG = False
ALLOWED_HOSTS = ['*']

COOKIE_DOMAIN = 'catchstudys.com'
COOKIE_SECURE = True

USE_SERVER = "https://api.catchstudys.com"
FRONTEND_SERVER = "https://www.catchstudys.com"

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = [
	# 허용할 Origin 추가
    "https://catchstudys.com",
    "https://www.catchstudys.com"
]
CORS_ALLOW_WHITELIST = [
    'catchstudys.com'
]