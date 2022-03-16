import jwt
import datetime
import json
import boto3


from django.core.mail import EmailMessage

# 설정에 작성된 값 가져오기
from django.conf import settings

PUBLIC_KEY = getattr(settings, "PUBLIC_KEY", None)
COOKIE_DOMAIN = getattr(settings, "COOKIE_DOMAIN", None)
COOKIE_SECURE = getattr(settings, "COOKIE_SECURE", None)
USE_SERVER = getattr(settings, "USE_SERVER", None)
FRONTEND_SERVER = getattr(settings, "FRONTEND_SERVER", None)
EMAIL_TOKEN_EXP = 30  # 30 min

# jwt 인코딩에 사용될 사설키 정보를 얻어옴
s3_resource = boto3.resource("s3")
my_bucket = s3_resource.Bucket(name="deploy-django-api")
SECRET_FILE_DATA = json.loads(
    my_bucket.Object("secret/secrets.json").get()["Body"].read()
)

# Email 클래스 사용
email = EmailMessage()


def send_auth_mail(send_to_email):

    payload = {"auth_mail": send_to_email}
    mail_auth_token = create_mail_token(payload)

    auth_url = "{}/auth/email/{}".format(FRONTEND_SERVER, mail_auth_token)

    title = "CatchStudys 회원 인증 메일입니다."
    body = "이메일 인증 URL 입니다.\n{}\n{}분 안에 링크를 클릭하여 인증하세요.".format(
        auth_url, EMAIL_TOKEN_EXP
    )

    email.subject = title
    email.body = body
    email.to = [send_to_email]
    email.send()

    return True


def send_password_reset_mail(input_id, send_to_email):

    payload = {"user_id": input_id, "user_email": send_to_email}
    mail_auth_token = create_mail_token(payload)

    # query = {'user_mail_auth_token': mail_auth_token}

    # auth_url = "{}/auth/email/verify?".format(USE_SERVER) + parse.urlencode(query, doseq=True)
    auth_url = "{}/auth/password/reset/{}".format(FRONTEND_SERVER, mail_auth_token)

    title = "CatchStudys 패스워드 초기화 메일입니다."
    body = "패스워드 초기화 페이지 URL 입니다.\n{}\n{}분 안에 링크를 클릭하여 패스워드를 변경하세요.".format(
        auth_url, EMAIL_TOKEN_EXP
    )

    email.subject = title
    email.body = body
    email.to = [send_to_email]
    email.send()

    return True


# mail 인증 token 생성
def create_mail_token(payload):

    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=EMAIL_TOKEN_EXP
    )

    try:
        token = jwt.encode(payload, SECRET_FILE_DATA["PRIVATE_KEY"], algorithm="RS256")
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False

    return token


# mail 인증 token 인증
def verify_mail_token(token):
    try:
        jwt.decode(token, PUBLIC_KEY, algorithms="RS256")
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False
    else:
        return True
