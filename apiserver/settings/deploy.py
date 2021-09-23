from .base import *

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# s3에서 DB에 대한 정보가 저장된 파일을 불러와 설정한다.
s3_resource = boto3.resource('s3')
my_bucket = s3_resource.Bucket(name='deploy-django-api')
SECRET_FILE_DATA = json.loads(json.dumps(yaml.load(my_bucket.Object('secret/deploy_db_info.yml').get()['Body'].read())))
DATABASES = SECRET_FILE_DATA