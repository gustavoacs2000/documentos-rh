# Importa o app Celery que acabamos de definir no celery.py
from .celery import app as celery_app

# Garante que o app Celery seja carregado quando o Django iniciar
__all__ = ('celery_app',)