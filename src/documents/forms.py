from django import forms
from .models import EmployeeDocument

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        # Diz ao formulário para usar o modelo EmployeeDocument
        model = EmployeeDocument

        # Diz ao formulário para mostrar APENAS o campo 'file'
        # (O 'owner' e 'doc_type' serão definidos automaticamente na view)
        fields = ['file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona uma ajuda de texto ou classe CSS, se quisermos
        self.fields['file'].label = "Selecione o arquivo (PDF ou Imagem)"
        self.fields['file'].widget.attrs.update({'class': 'form-control-file'})