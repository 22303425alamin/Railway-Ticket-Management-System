from django.urls import path
from . import views

app_name = 'trains'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_trains, name='search'),
    path('deep-search/', views.deep_search, name='deep_search'),
    path('train/<int:train_id>/', views.train_detail, name='train_detail'),
]