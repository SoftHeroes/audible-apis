from django.urls import path

# from devices import views
from .views import CatalogCategories,CatalogProducts,StatsAggregates,StatsProducts,AccountInfo,ProductDetail,GetAllProducts,AddProduct

urlpatterns = [
    path('catalog/categories', CatalogCategories.as_view()),
    path('catalog/products', CatalogProducts.as_view()),
    path('product/<str:asin>', ProductDetail.as_view()),
    path('product/<str:asin>/add', AddProduct.as_view()),
    path('stats/aggregates', StatsAggregates.as_view()),
    path('stats/products', StatsProducts.as_view()),
    path('account/info', AccountInfo.as_view()),
    path('get-all-products', GetAllProducts.as_view()),
]