from django.urls import path

from authuser.views import (
    EmailDuplicatecheck,
    IdDuplicatecheck,
    NameDuplicatecheck,
    PasswordReset,
    SendAuthEmail,
    SendPasswordResetEmail,
    TokenAuth,
    UserLogin,
    UserLogout,
    VerifyAuthEmail,
    VerifyPassword,
)

urlpatterns = [
    path("login", UserLogin.as_view()),
    path("logout", UserLogout.as_view()),
    path("id_duplicate_check", IdDuplicatecheck.as_view()),
    path("email_duplicate_check", EmailDuplicatecheck.as_view()),
    path("name_duplicate_check", NameDuplicatecheck.as_view()),
    path("verify_user", TokenAuth.as_view()),
    path("password/verify", VerifyPassword.as_view()),
    path("password/reset", PasswordReset.as_view()),
    path("password/reset/send", SendPasswordResetEmail.as_view()),
    path("email/send", SendAuthEmail.as_view()),
    path("email/verify", VerifyAuthEmail.as_view()),
]
