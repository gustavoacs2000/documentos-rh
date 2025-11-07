from django.urls import path
from . import views  # Importa o views.py

urlpatterns = [
    # Rota raiz (ex: http://localhost:8000/)
    path('', views.home_view, name='home'),

    # Rota do Dashboard (já existia)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # -----------------------------------------------------------------
    # ADICIONE ESTA NOVA ROTA
    # -----------------------------------------------------------------
    # Esta rota captura um número inteiro (int) da URL,
    # o salva como 'doc_type_id' e o passa para a 'document_upload_view'.
    # Ex: /upload/1/  -> chama a view com doc_type_id=1 (RG)
    # Ex: /upload/2/  -> chama a view com doc_type_id=2 (CPF)
    path(
        'upload/<int:doc_type_id>/', 
        views.document_upload_view, 
        name='document_upload'
    ),
]