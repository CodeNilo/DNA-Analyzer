from django.urls import path

from .views import DNASequenceListView, DNASequenceUploadView

urlpatterns = [
    path('sequences/upload/', DNASequenceUploadView.as_view(), name='sequence-upload'),
    path('sequences/', DNASequenceListView.as_view(), name='sequence-list'),
]
