import os
from celery import Celery

# Define a variável de ambiente 'DJANGO_SETTINGS_MODULE' para o Celery
# Isso aponta para o seu arquivo settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')

# Cria a instância principal do aplicativo Celery
# O nome 'portal' deve ser o mesmo do seu projeto Django
app = Celery('portal')

# Informa ao Celery para carregar sua configuração do arquivo settings.py do Django.
# O 'namespace='CELERY'' significa que todas as configurações do Celery no settings.py
# devem começar com "CELERY_" (ex: CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Informa ao Celery para descobrir automaticamente os arquivos 'tasks.py'
# em todos os seus 'INSTALLED_APPS' (como o seu app 'documents')
app.autodiscover_tasks()