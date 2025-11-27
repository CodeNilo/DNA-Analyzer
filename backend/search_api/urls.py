from django.urls import path

from .views import SearchJobDetailView, SearchView

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('search/jobs/<int:pk>/', SearchJobDetailView.as_view(), name='search-job-detail'),
]
