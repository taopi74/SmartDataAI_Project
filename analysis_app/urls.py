from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('scrape/', views.scrape_data_view, name='scrape_data'),
]