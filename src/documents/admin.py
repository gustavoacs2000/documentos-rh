from django.contrib import admin
# 1. IMPORTAR O NOVO MODELO
from .models import DocumentType, EmployeeDocument, ValidationRule 

# -----------------------------------------------------------------
# 2. CRIAR O "INLINE" PARA AS REGRAS DE VALIDAÇÃO
# -----------------------------------------------------------------
# Isso permite que você edite regras DENTRO da página do Tipo de Documento
class ValidationRuleInline(admin.TabularInline):
    model = ValidationRule
    extra = 1 # Mostra 1 formulário em branco por padrão
    verbose_name = "Regra de Validação"
    verbose_name_plural = "Regras de Validação"

# -----------------------------------------------------------------
# ADMIN PARA: TIPO DE DOCUMENTO (MODIFICADO)
# -----------------------------------------------------------------
# Configuração para gerenciar os Tipos de Documento (RG, CPF, etc.)
# -----------------------------------------------------------------
@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    # O que mostrar na lista
    list_display = ('name', 'description')
    # Campos que o RH pode pesquisar
    search_fields = ('name',)

    # 3. ADICIONAR O INLINE À ADMIN DO TIPO DE DOCUMENTO
    inlines = [ValidationRuleInline]

# -----------------------------------------------------------------
# ADMIN PARA: DOCUMENTO DO FUNCIONÁRIO (SEU CÓDIGO ORIGINAL)
# -----------------------------------------------------------------
# Configuração principal para o RH gerenciar os documentos enviados
# -----------------------------------------------------------------
@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    # Colunas que o RH verá na lista de documentos
    list_display = (
        'owner',
        'doc_type',
        'status',
        'uploaded_at'
    )
    # Filtros rápidos na lateral (ESSENCIAL para o RH)
    list_filter = (
        'status',
        'doc_type'
    )
    # Campos que o RH pode pesquisar
    search_fields = (
        'owner__username',  # Permite buscar pelo nome do funcionário
        'extracted_text'    # Permite buscar pelo texto do OCR!
    )
    # Campos que o RH não pode editar diretamente (são automáticos)
    readonly_fields = (
        'uploaded_at',
        'extracted_text'
    )
    
    # Define a ordem dos campos no formulário de edição
    fieldsets = (
        (None, {
            'fields': ('owner', 'doc_type', 'file')
        }),
        ('Controle do RH', {
            'fields': ('status', 'notes_hr')
        }),
        ('Dados Automáticos (Somente Leitura)', {
            'classes': ('collapse',), # Começa "fechado"
            'fields': ('uploaded_at', 'extracted_text')
        }),
    )

    # Ações rápidas que o RH pode tomar (ex: "Aprovar 3 documentos de uma vez")
    actions = ['approve_documents', 'reject_documents']

    def approve_documents(self, request, queryset):
        queryset.update(status='APPROVED', notes_hr='Documento aprovado.')
    approve_documents.short_description = "Aprovar documentos selecionados"

    def reject_documents(self, request, queryset):
        # O ideal aqui é ter um campo 'notes_hr' obrigatório
        queryset.update(status='REJECTED')
    reject_documents.short_description = "Rejeitar documentos selecionados"