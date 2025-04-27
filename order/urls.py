from django.urls import path
from . import views
from .views import create_order_ajax

app_name = 'order'

urlpatterns = [
	path('', views.order_list, name="order_list"),
	path('<int:id>', views.order_details, name="order_details"),
	path('shipping/', views.order_create, name="order_create"),
	path('pdf/<int:id>',views.pdf.as_view(), name="pdf"),
    path('payment', views.create_order_ajax, name='create_order_ajax'),
	path('success/', views.payment_success, name='payment_success'),
]
