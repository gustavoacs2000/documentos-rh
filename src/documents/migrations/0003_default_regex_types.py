# Generated manually to create default document types and regexes

from django.db import migrations

def create_default_document_types(apps, schema_editor):
    DocumentType = apps.get_model('documents', 'DocumentType')
    ValidationRule = apps.get_model('documents', 'ValidationRule')

    # 1. RG (Registro Geral)
    rg_type, _ = DocumentType.objects.get_or_create(
        name="RG",
        defaults={"description": "Carteira de Identidade (Registro Geral)"}
    )
    
    # Regras para o RG
    ValidationRule.objects.get_or_create(
        document_type=rg_type,
        rule_type="CONTAINS_TEXT",
        rule_value="CARTEIRA DE IDENTIDADE",
        defaults={"description": "Deve indicar que é uma carteira de identidade"}
    )
    ValidationRule.objects.get_or_create(
        document_type=rg_type,
        rule_type="REGEX_MATCH",
        # Regex básico para RG: 1 ou 2 digitos, ponto, 3 digitos, ponto, 3 digitos, hífen, digito ou letra
        rule_value=r"\d{1,2}\.?\d{3}\.?\d{3}-?[0-9X-x]",
        defaults={"description": "Padrão do número do RG"}
    )

    # 2. CPF (Cadastro de Pessoas Físicas)
    cpf_type, _ = DocumentType.objects.get_or_create(
        name="CPF",
        defaults={"description": "Cadastro de Pessoas Físicas"}
    )
    
    # Regras para o CPF
    ValidationRule.objects.get_or_create(
        document_type=cpf_type,
        rule_type="REGEX_MATCH",
        # Regex básico para CPF: XXX.XXX.XXX-XX
        rule_value=r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
        defaults={"description": "Padrão do número do CPF"}
    )

    # 3. CNH (Carteira Nacional de Habilitação)
    cnh_type, _ = DocumentType.objects.get_or_create(
        name="CNH",
        defaults={"description": "Carteira Nacional de Habilitação"}
    )
    
    # Regras para CNH
    ValidationRule.objects.get_or_create(
        document_type=cnh_type,
        rule_type="CONTAINS_TEXT",
        rule_value="CARTEIRA NACIONAL DE",
        defaults={"description": "Deve indicar Carteira Nacional de Habilitação"}
    )
    ValidationRule.objects.get_or_create(
        document_type=cnh_type,
        rule_type="REGEX_MATCH",
        # Regex para CNH: O número de registro costuma ter 11 dígitos
        rule_value=r"\b\d{11}\b",
        defaults={"description": "Padrão de 11 dígitos da CNH"}
    )

class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_alter_employeedocument_status_validationrule'),
    ]

    operations = [
        migrations.RunPython(create_default_document_types),
    ]
