import io
import logging
import re
import os

from celery import shared_task
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
import google.generativeai as genai

from .models import EmployeeDocument

# Logger para acompanhar o processamento no worker Celery
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def run_validation(doc: EmployeeDocument, extracted_text: str):
    """
    Executa as regras de validacao configuradas para o tipo de documento.
    Retorna (status, notes_hr).
    """
    rules = doc.doc_type.validation_rules.all()
    if not rules:
        return "REVIEW", "Sem regras automaticas definidas; aguardando revisao."

    text_lower = (extracted_text or "").lower()
    failed = []

    for rule in rules:
        value = rule.rule_value or ""

        if rule.rule_type in ("CONTAINS_TEXT", "CONTAINS_KEY"):
            if value.lower() not in text_lower:
                failed.append(f"Nao encontrou: {value}")
            continue

        if rule.rule_type == "REGEX_MATCH":
            try:
                if not re.search(value, extracted_text or "", flags=re.IGNORECASE | re.MULTILINE):
                    failed.append(f"Regex nao bateu: {value}")
            except re.error as regex_err:
                failed.append(f"Regex invalida ({value}): {regex_err}")
            continue

    if failed:
        return "REJECTED", "Falhas na validacao: " + "; ".join(failed)

    return "REVIEW", "Validacao automatica aprovada. Aguardando revisao."


@shared_task
def process_document_ocr(document_id):
    """
    Processa o OCR de um documento (imagem ou PDF) e aplica as regras
    de validacao cadastradas para o tipo daquele documento.
    """
    try:
        doc = EmployeeDocument.objects.get(id=document_id)
        logger.info("Iniciando OCR para o Documento ID: %s", document_id)

        # Le o arquivo do storage para memoria
        file_content = doc.file.read()
        final_text = ""

        # ----------------------------------------------------
        # TENTATIVA 0: IA GOOGLE GEMINI (VISUAL VERIFICATION)
        # ----------------------------------------------------
        if GEMINI_API_KEY:
            try:
                logger.info("Tentando processar Doc ID %s usando Google Gemini (IA).", document_id)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Vamos descobrir se é mais provável ser um PDF ou Imagem
                mime_type = "application/pdf" if doc.file.name.lower().endswith(".pdf") else "image/jpeg"
                
                prompt = (
                    "Você é um excelente assistente de extração de dados. "
                    "Extraia com EXTREMA fidelidade TODO o texto contido neste documento. "
                    "Seja preciso e não invente (hallucinate) nenhuma informação. "
                    "Retorne apenas o texto puro e exato lido do documento."
                )
                
                response = model.generate_content([
                    {"mime_type": mime_type, "data": file_content},
                    prompt
                ])
                
                if response.text:
                    final_text = response.text
                    logger.info("OCR concluído com SUCESSO via Google Gemini para Doc ID %s", document_id)
                else:
                    raise ValueError("Gemini retornou um texto vazio.")
                    
            except Exception as gemini_err:
                logger.warning(
                    "Falha ao processar Doc ID %s via Google Gemini. Erro: %s. "
                    "Fazendo fallback para PyTesseract (OCR Local)...",
                    document_id, gemini_err
                )
        else:
            logger.info("GEMINI_API_KEY não configurada. Usando PyTesseract (OCR Local) para Doc ID %s...", document_id)

        # ----------------------------------------------------
        # FALLBACK: OCR LOCAL (PYTESSERACT)
        # ----------------------------------------------------
        if not final_text:
            # Tentativa 1: imagem
            try:
                logger.info("Tentando processar Doc ID %s como IMAGEM (PyTesseract).", document_id)
                img = Image.open(io.BytesIO(file_content))
                final_text = pytesseract.image_to_string(img, lang="por")
                logger.info("Processado com sucesso como IMAGEM (PyTesseract).")
            except Exception as image_error:
                logger.warning(
                    "Falha ao processar Doc ID %s como imagem (%s). Tentando PDF (PyTesseract)...",
                    document_id,
                    image_error,
                )
                # Tentativa 2: PDF
                try:
                    images = convert_from_bytes(file_content)
    
                    full_text_list = []
                    for i, page_image in enumerate(images):
                        logger.info("Processando pagina %s do PDF (Doc ID: %s)", i + 1, document_id)
                        page_text = pytesseract.image_to_string(page_image, lang="por")
                        full_text_list.append(page_text)
    
                    final_text = "\n\n--- PAGINA SEGUINTE ---\n\n".join(full_text_list)
                    logger.info("Processado com sucesso como PDF (PyTesseract).")
                except Exception as pdf_error:
                    logger.error(
                        "Falha total no OCR para Doc ID: %s. Nao e imagem nem PDF valido, falhou Gemini e PyTesseract. Erro: %s",
                        document_id,
                        pdf_error,
                    )
                    doc.notes_hr = (
                        "Falha na extração de texto: Arquivo não pôde ser lido (nem por IA, imagem ou PDF). "
                        f"Erro raiz OCR Local: {pdf_error}"
                    )
                    doc.status = "REJECTED"
                    doc.save(update_fields=["notes_hr", "status"])
                    return f"Falha total: {document_id}"

        # OCR concluiu; aplica validacao automatica
        doc.extracted_text = final_text
        new_status, notes = run_validation(doc, final_text)
        doc.status = new_status
        doc.notes_hr = notes

        doc.save(update_fields=["extracted_text", "status", "notes_hr"])
        logger.info(
            "OCR concluido com sucesso para Doc ID: %s (status: %s)", document_id, new_status
        )
        return f"Sucesso: {document_id}"

    except EmployeeDocument.DoesNotExist:
        logger.error("Erro no OCR: Documento ID %s nao encontrado.", document_id)
        return "Erro: Documento nao encontrado"
    except Exception as e:
        logger.error("Erro inesperado no OCR para Doc ID %s: %s", document_id, e)
        return f"Erro inesperado: {e}"
