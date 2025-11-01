from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# -----------------------------------------------------------------
# MODELO 1: TIPO DE DOCUMENTO
# -----------------------------------------------------------------
# Tabela que o RH vai gerenciar para criar os tipos de
# documentos que os funcionários precisam enviar.
# -----------------------------------------------------------------
class DocumentType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome do Documento"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição"
    )

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"

    def __str__(self):
        # Isso é o que vai aparecer no painel admin (ex: "RG")
        return self.name

# -----------------------------------------------------------------
# MODELO 2: DOCUMENTO DO FUNCIONÁRIO
# -----------------------------------------------------------------
# Tabela principal que armazena o arquivo enviado pelo funcionário
# e seu status.
# -----------------------------------------------------------------
class EmployeeDocument(models.Model):

    # Opções para o campo 'status'
    STATUS_CHOICES = [
        ('UPLOADED', 'Enviado (Processando)'),
        ('REVIEW', 'Aguardando Revisão'), # <-- NOVO STATUS
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    ]

    # --- RELACIONAMENTOS ---
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Funcionário"
    )
    doc_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT, # Protege para não deletar um tipo se houver docs
        verbose_name="Tipo de Documento"
    )

    # --- CAMPOS DO ARQUIVO ---
    file = models.FileField(
        upload_to='employee_documents/', # Pasta dentro do bucket R2
        verbose_name="Arquivo"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPLOADED', # Status inicial ao criar
        verbose_name="Status"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, # Define a data/hora automaticamente na criação
        verbose_name="Data de Envio"
    )

    # --- CAMPOS DO RH E OCR ---
    extracted_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="Texto Extraído (OCR)"
    )
    notes_hr = models.TextField(
        blank=True,
        null=True,
        verbose_name="Feedback do RH (Motivo da Rejeição)"
    )

    class Meta:
        verbose_name = "Documento de Funcionário"
        verbose_name_plural = "Documentos de Funcionários"
        # Garante que um funcionário só possa ter UM documento de cada tipo
        unique_together = ('owner', 'doc_type')
        # Ordena os mais novos primeiro no admin
        ordering = ['-uploaded_at']

    def __str__(self):
        # Ex: "gustavo - RG (Aprovado)"
        return f"{self.owner.username} - {self.doc_type.name} ({self.status})"

# -----------------------------------------------------------------
# MODELO 3: REGRA DE VALIDAÇÃO
# -----------------------------------------------------------------
# Tabela para o RH cadastrar as regras que o OCR deve
# procurar no texto extraído para validar um documento.
# -----------------------------------------------------------------
class ValidationRule(models.Model):
    # Define os tipos de regras que podemos criar.
    # Isso cobre os exemplos que você deu.
    RULE_TYPES = [
        ('CONTAINS_TEXT', 'Deve Conter o Texto'),
        ('CONTAINS_KEY', 'Deve Conter a Chave (ex: "CPF:")'),
        ('REGEX_MATCH', 'Deve Corresponder ao Padrão (Regex)'),
    ]

    # --- RELACIONAMENTO ---
    # Liga esta regra a um Tipo de Documento específico
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name='validation_rules', # Como acessar as regras a partir de um DocumentType
        verbose_name="Tipo de Documento"
    )

    # --- CAMPOS DA REGRA ---
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPES,
        verbose_name="Tipo de Regra"
    )
    # O valor que a regra vai procurar (ex: "Carteira de Identidade" ou "Registro Geral - CPF")
    rule_value = models.CharField(
        max_length=255,
        verbose_name="Valor/Texto/Padrão a verificar"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Descrição (Opcional)"
    )

    class Meta:
        verbose_name = "Regra de Validação"
        verbose_name_plural = "Regras de Validação"

    def __str__(self):
        # Ex: "RG: Deve Conter o Texto 'Carteira de Identidade'"
        return f"{self.document_type.name}: {self.get_rule_type_display()} '{self.rule_value[:20]}...'"
# -----------------------------------------------------------------
# SINAL (SIGNAL) PARA DISPARAR O OCR
# -----------------------------------------------------------------
# Esta função "escuta" o evento de salvar um EmployeeDocument.
# Quando um novo documento é CRIADO, ela chama a tarefa do Celery.
# -----------------------------------------------------------------
@receiver(post_save, sender=EmployeeDocument)
def trigger_ocr_on_upload(sender, instance, created, **kwargs):
    """
    Dispara a tarefa de OCR (Celery) quando um novo
    EmployeeDocument é criado (created=True).
    """
    # (Vamos precisar criar este arquivo 'tasks.py' em breve)

    # Garante que só rode na criação (created=True)
    # e se um arquivo realmente existir
    if created and instance.file:
        # A CORREÇÃO: Mova o import para DENTRO do if.
        # Isso evita o ImportError durante a inicialização.
        from .tasks import process_document_ocr
        
        # Chama a tarefa do Celery de forma assíncona
        # Passa o ID do documento para a tarefa
        process_document_ocr.delay(instance.id)