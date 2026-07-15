from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('calculator/', views.calculator_view, name='calculator'),
    path('calculator/report/', views.calculator_report_view, name='calculator_report'),
    path('compare/', views.comparison_view, name='compare'),
]
