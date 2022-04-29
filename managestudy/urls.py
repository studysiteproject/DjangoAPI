from django.urls import path

from managestudy.views import (
    CreateOrViewComments,
    CreateReplyComment,
    UpdateOrDeleteComment,
    UpdateVisibleComment,
)

urlpatterns = [
    path("<int:study_id>/comments", CreateOrViewComments.as_view()),
    path("<int:study_id>/comments/<int:comment_id>/reply", CreateReplyComment.as_view()),
    path("<int:study_id>/comments/<int:comment_id>", UpdateOrDeleteComment.as_view()),
    path(
        "<int:study_id>/comments/<int:comment_id>/visible",
        UpdateVisibleComment.as_view(),
    ),
]
