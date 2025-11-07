from django.shortcuts import render, redirect, get_object_or_404 # <-- CORREÇÃO APLICADA AQUI
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import (
    DocumentType,
    EmployeeDocument,
) 
from .forms import DocumentUploadForm


# Esta é a sua view 'home' que já existia
def home_view(request):
    return HttpResponse("Olá, mundo! O portal de funcionários funcionou.")


# -----------------------------------------------------------------
# VIEW DO DASHBOARD (CORRIGIDA)
# -----------------------------------------------------------------
@login_required 
def dashboard_view(request):

    # 1. Pega o usuário que está logado
    current_user = request.user

    # 2. Busca todos os tipos de documento que o RH cadastrou
    all_doc_types = DocumentType.objects.all()

    # 3. Busca os documentos que ESTE usuário já enviou
    user_docs = EmployeeDocument.objects.filter(owner=current_user)

    # 4. (Mágica) Cria um dicionário para saber o status de cada documento
    user_docs_status = {doc.doc_type.name: doc.status for doc in user_docs}

    # 5. Prepara a lista final para o HTML
    document_list_for_html = []

    for doc_type in all_doc_types:
        document_list_for_html.append(
            {
                "name": doc_type.name,
                "description": doc_type.description,
                "status": user_docs_status.get(doc_type.name, "PENDENTE"),
                "doc_type_id": doc_type.id 
            }
        )

    # O 'context' agora envia a lista completa para o template
    context = {
        "nome_do_usuario": current_user.username,
        "document_list": document_list_for_html,
    }

    # Renderiza o arquivo 'dashboard.html'
    return render(request, "dashboard.html", context)


@login_required
def document_upload_view(request, doc_type_id):
    # 1. Pega o "Tipo de Documento" (ex: RG) que o usuário quer enviar
    # (Agora o 'get_object_or_404' funciona)
    doc_type = get_object_or_404(DocumentType, id=doc_type_id)

    # 2. Verifica se o usuário JÁ enviou este documento
    document = EmployeeDocument.objects.filter(
        owner=request.user, doc_type=doc_type
    ).first()

    # 3. Processa o formulário quando o usuário clica em "Enviar" (POST)
    if request.method == "POST":
        # Cria o formulário preenchido com os dados (e arquivos) enviados
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)

        if form.is_valid():
            doc_to_save = form.save(commit=False)

            # 4. Define os campos que faltam
            doc_to_save.owner = request.user
            doc_to_save.doc_type = doc_type
            doc_to_save.status = "UPLOADED" 

            doc_to_save.save()

            # 5. Redireciona o usuário de volta para o dashboard
            # (Agora o 'redirect' funciona)
            return redirect("dashboard")

    # 6. Se for a primeira visita (GET), mostra um formulário limpo
    else:
        form = DocumentUploadForm(instance=document)

    # 7. Prepara o contexto para o HTML
    context = {"form": form, "doc_type_name": doc_type.name}

    return render(request, "upload_document.html", context)