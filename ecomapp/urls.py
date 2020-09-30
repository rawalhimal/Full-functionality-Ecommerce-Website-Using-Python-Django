from django.urls import path
from .views import *
app_name='ecomapp'
urlpatterns=[
    path('',HomeView.as_view(),name='home'),
     path('about/',AboutView.as_view(),name='about'),
     path('contact-us/',ContactView.as_view(),name='contact'),
     path('all-products/',AllProducts.as_view(),name='allproducts'),
     path('product/<slug:slug>/',ProductDetailView.as_view(),name='productdetail'),
     path('add-to-cart/<int:pro_id>/',AddToCartView.as_view(),name='addtocart'),
     path('my-cart/',AddMyCartView.as_view(),name='mycart'),
     path('manage-cart/<int:cp_id>/',ManageCartView.as_view(),name='managecart'),
     path('empty-cart/',EmptyCartView.as_view(),name='emptycart'),
     path('checkout/',CheckoutView.as_view(),name='checkout'),
     path('register/',CustomerRegistration.as_view(),name='customerregistration'),
     path('logout/',CustomerLogoutView.as_view(),name='customerlogout'),
     path('login/',CustomerLoginView.as_view(),name='customerloginform'),
     path('profile/',CustomerDetailView.as_view(),name='customerprofile'),
     path('profile/order-<int:pk>/',CustomerOrderDetailView.as_view(),name='customerorderdetail'),
     path('search/',SearchView.as_view(),name="search"),
     #admin part
     path('admin-login/',AdminLoginView.as_view(),name='adminlogin'),
     path('admin-home/',AdminHomeView.as_view(),name='adminhome'),
     path('admin/order-<int:pk>/',AdminOrderDetailView.as_view(),name='adminorderdetail'),
     path('admin-all-order/',AdminOrderListView.as_view(),name='adminorder'),
     path('admin-order-<int:pk>-change/',AdminOrderStatusView.as_view(),name='adminorderstatus'),


]