from celery import shared_task
from .models import EmployeeDocument
from PIL import Image
from pdf2image import convert_from_bytes # <-- NOVO IMPORT
import pytesseract
import io
import logging

# Configura um logger para vermos os resultados no terminal do Celery
logger = logging.getLogger(__name__)

@shared_task
def process_document_ocr(document_id):
    """
    Tarefa assíncrona do Celery para processar o OCR de um documento.
    Agora suporta tanto IMAGENS (jpg, png) quanto PDFs.
    """
    try:
        # 1. Busca o documento no banco de dados
        doc = EmployeeDocument.objects.get(id=document_id)
        logger.info(f"Iniciando OCR para o Documento ID: {document_id}")

        # 2. Lê o arquivo do Cloudflare R2 para a memória
        file_content = doc.file.read()
        
        final_text = ""

        # --- TENTATIVA 1: Processar como IMAGEM ---
        try:
            logger.info(f"Tentando processar Doc ID: {document_id} como IMAGEM.")
            img = Image.open(io.BytesIO(file_content))
            final_text = pytesseract.image_to_string(img, lang='por')
            logger.info(f"Processado com sucesso como IMAGEM.")

        except Exception as image_error:
            logger.warning(f"Falha ao processar Doc ID: {document_id} como imagem ({image_error}). Tentando como PDF...")
            
            # --- TENTATIVA 2: Processar como PDF ---
            try:
                # Converte o PDF (em bytes) para uma lista de imagens PIL
                images = convert_from_bytes(file_content)
                
                full_text_list = []
                # Passa o Tesseract em cada página
                for i, page_image in enumerate(images):
                    logger.info(f"Processando página {i+1} do PDF (Doc ID: {document_id})")
                    page_text = pytesseract.image_to_string(page_image, lang='por')
                    full_text_list.append(page_text)
                    
                # Junta o texto de todas as páginas
                final_text = "\n\n--- PÁGINA SEGUINTE ---\n\n".join(full_text_list)
                logger.info(f"Processado com sucesso como PDF.")

            except Exception as pdf_error:
                # --- FALHA TOTAL ---
                logger.error(f"Falha total no OCR para Doc ID: {document_id}. Não é imagem nem PDF. Erro: {pdf_error}")
                doc.notes_hr = f"Falha no OCR: Arquivo não é uma imagem ou PDF válido. Erro: {pdf_error}"
                doc.status = 'REJECTED'
                doc.save(update_fields=['notes_hr', 'status'])
                return f"Falha total: {document_id}"

        # --- SUCESSO (Seja Imagem ou PDF) ---
        doc.extracted_text = final_text
        
        # ATUALIZAÇÃO DA LÓGICA:
        # Muda o status para 'AGUARDANDO_REVISAO' para que o RH saiba
        # que o OCR foi concluído e o documento está pronto para ser verificado.
        # (Se o status já for 'REJECTED' ou 'APPROVED', não mude)
        if doc.status == 'UPLOADED':
             doc.status = 'REVIEW' # <-- Vamos precisar adicionar isso

        doc.save(update_fields=['extracted_text', 'status'])
        logger.info(f"OCR concluído com sucesso para Doc ID: {document_id}")
        return f"Sucesso: {document_id}"

    except EmployeeDocument.DoesNotExist:
        logger.error(f"Erro no OCR: Documento ID {document_id} não encontrado.")
        return f"Erro: Documento não encontrado"
    except Exception as e:
        logger.error(f"Erro inesperado no OCR para Doc ID {document_id}: {e}")
        return f"Erro inesperado: {e}"