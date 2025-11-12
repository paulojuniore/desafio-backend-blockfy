from communication.views import PixMessageView
from django.urls import path

urlpatterns = [
    path('util/msgs/<str:ispb>/<str:number>', PixMessageView.as_view()),
]
