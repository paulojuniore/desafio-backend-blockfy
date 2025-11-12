from communication.views import PixMessageView, PixStreamStartView, PixStreamNextView
from django.urls import path

urlpatterns = [
    path('util/msgs/<str:ispb>/<str:number>', PixMessageView.as_view()),
    path('pix/<str:ispb>/stream/start', PixStreamStartView.as_view()),
    path('pix/<str:ispb>/stream/<str:interationId>', PixStreamNextView.as_view(), name='pix-stream-next')
]
