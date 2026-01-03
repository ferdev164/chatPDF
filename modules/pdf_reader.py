import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import os
import platform

# Configuración para Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    """
    Extrae texto de un PDF.
    - Si tiene texto nativo, lo extrae directamente (rápido)
    - Si es escaneo/imagen, usa OCR (más lento)
    """
    text = ""
    
    try:
        # PASO 1: Intentar extraer texto nativo
        print(f"📖 Intentando extraer texto nativo de {pdf_path}...")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Verificar si se extrajo texto suficiente
            if len(text.strip()) > 100:  # Si hay más de 100 caracteres
                print(f"✅ Texto nativo extraído: {len(text)} caracteres")
                return text
            else:
                print("⚠️ Poco o ningún texto nativo, intentando OCR...")
        
        # PASO 2: Si no hay texto o es muy poco, usar OCR
        print(f"🔍 Aplicando OCR a {pdf_path}...")
        text = extract_text_with_ocr(pdf_path)
        print(f"✅ OCR completado: {len(text)} caracteres")
        
        return text
    
    except Exception as e:
        print(f"❌ Error al procesar PDF: {str(e)}")
        # Como último recurso, intentar OCR
        try:
            return extract_text_with_ocr(pdf_path)
        except Exception as ocr_error:
            return f"Error: No se pudo extraer texto del PDF. {str(e)}"

def extract_text_with_ocr(pdf_path):
    """
    Usa OCR (Tesseract) para extraer texto de PDFs escaneados
    """
    text = ""
    
    try:
        # Convertir PDF a imágenes
        print("🖼️ Convirtiendo PDF a imágenes...")
        
        # Detectar poppler path en Windows
        if platform.system() == 'Windows':
            poppler_path = r'C:\poppler\Library\bin'
            images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        else:
            images = convert_from_path(pdf_path, dpi=300)
        
        print(f"📄 Procesando {len(images)} página(s) con OCR...")
        
        # Aplicar OCR a cada imagen
        for i, image in enumerate(images):
            print(f"   Página {i+1}/{len(images)}...")
            
            # OCR con Tesseract (español + inglés)
            page_text = pytesseract.image_to_string(
                image,
                lang='spa+eng',  # Español e inglés
                config='--psm 1'  # Automatic page segmentation with OSD
            )
            
            text += f"\n--- Página {i+1} ---\n{page_text}\n"
        
        return text
    
    except Exception as e:
        raise Exception(f"Error en OCR: {str(e)}")

def is_scanned_pdf(pdf_path):
    """
    Detecta si un PDF es escaneo o tiene texto nativo
    Retorna True si es escaneo (necesita OCR)
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Revisar las primeras 3 páginas
            pages_to_check = min(3, len(pdf_reader.pages))
            total_text = ""
            
            for i in range(pages_to_check):
                total_text += pdf_reader.pages[i].extract_text()
            
            # Si hay muy poco texto, probablemente es escaneo
            return len(total_text.strip()) < 50
    
    except Exception:
        return True  # Si hay error, asumir que necesita OCR