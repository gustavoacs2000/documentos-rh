from django.contrib import admin
from django.urls import path, include
# --- IMPORTE AS VIEWS DE DOCUMENTAÇÃO ---
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # 1. Rota do Admin (Já existia)
    path('admin/', admin.site.urls),

    # 2. Rotas de Autenticação do Django (Login / Logout)
    path('accounts/', include('django.contrib.auth.urls')),

    # 3. Rotas do nosso App (Dashboard, Upload, etc.)
    path('', include('documents.urls')),

    # -----------------------------------------------------------------
    # 4. NOVAS ROTAS DE DOCUMENTAÇÃO DA API
    # -----------------------------------------------------------------
    
    # Rota que gera o "esquema" da API (o JSON bruto)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Rota para a interface do Swagger UI (a que você provavelmente quer)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Rota para a interface do Redoc (uma alternativa)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]