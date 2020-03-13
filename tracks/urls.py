from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='tracks-index'),
    path('about/', views.about, name='tracks-about'),
    path('select-factors/', views.select_factors, name='tracks-select_factors'),
    path('select-cell-type/', views.select_cell_type, name='tracks-select_cell_type'),
    path('select-tracks/', views.select_tracks, name='tracks-select_tracks'),
    path('<encoded_key_value>/', views.detail, name='tracks-detail'),
    path('<encoded_key_value>/hub.txt', views.hub, name='tracks-hub'),
    path('<encoded_key_value>/genomes.txt', views.genomes, name='tracks-genomes'),
    path('<encoded_key_value>/<genome>/trackDb.txt', views.track_db, name='tracks-trackdb'),
]
