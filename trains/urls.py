from django.urls import path
from . import views

app_name = 'trains'

urlpatterns = [
    path('', views.home, name="home"),
    path('search/', views.search_trains, name="search"),
    path('deep-search/', views.deep_search, name="deep_search"),
    path('train/<int:train_id>/', views.train_detail, name="train_detail"),
    
    # Admin Management URLs

    path('manage/trains/', views.admin_train_list, name='admin_train_list'),
    path('manage/trains/add/', views.admin_train_add, name='admin_train_add'),
    path('manage/trains/<int:train_id>/edit/', views.admin_train_edit, name='admin_train_edit'),
    path('manage/trains/<int:train_id>/delete/', views.admin_train_delete, name='admin_train_delete'),
    
    path('manage/routes/', views.admin_route_list, name='admin_route_list'),
    path('manage/routes/add/', views.admin_route_add, name='admin_route_add'),
    path('manage/routes/<int:route_id>/delete/', views.admin_route_delete, name='admin_route_delete'),
    
    path('manage/schedules/', views.admin_schedule_list, name='admin_schedule_list'),
    path('manage/schedules/<int:schedule_id>/edit/', views.admin_schedule_edit, name='admin_schedule_edit'),

]