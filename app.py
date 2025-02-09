import os
import uuid
import zipfile
from flask import Flask, request, send_file, render_template
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image

app = Flask(__name__)

# Caminho base (onde está este arquivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta onde salvamos uploads e arquivos temporários
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    # Página principal
    return render_template("index.html")

# 1) PDF -> JPG (somente a primeira página)
@app.route("/pdf_to_jpg_single", methods=["POST"])
def pdf_to_jpg_single():
    pdf_file = request.files.get("file_single")
    if not pdf_file:
        return "Nenhum PDF enviado.", 400

    # Nome único
    pdf_filename = f"{uuid.uuid4()}_{pdf_file.filename}"
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
    pdf_file.save(pdf_path)

    try:
        images = convert_from_path(pdf_path)  # Converte todas as páginas em imagens
        output_jpg = pdf_path.replace(".pdf", ".jpg")
        # Salva só a 1ª página
        images[0].save(output_jpg, "JPEG")
        return send_file(output_jpg, as_attachment=True)
    except Exception as e:
        return f"Erro ao converter PDF para JPG: {e}", 500

# 2) PDF -> JPG (todas as páginas em .zip)
@app.route("/pdf_to_jpg_multi", methods=["POST"])
def pdf_to_jpg_multi():
    pdf_file = request.files.get("file_multi")
    if not pdf_file:
        return "Nenhum PDF enviado.", 400

    pdf_filename = f"{uuid.uuid4()}_{pdf_file.filename}"
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
    pdf_file.save(pdf_path)

    try:
        images = convert_from_path(pdf_path)
        zip_filename = pdf_path.replace(".pdf", ".zip")

        with zipfile.ZipFile(zip_filename, "w") as zipf:
            # Salva cada página em JPEG e inclui no .zip
            for i, img in enumerate(images):
                page_jpg = pdf_path.replace(".pdf", f"_page_{i+1}.jpg")
                img.save(page_jpg, "JPEG")
                zipf.write(page_jpg, arcname=os.path.basename(page_jpg))

        return send_file(zip_filename, as_attachment=True)
    except Exception as e:
        return f"Erro ao converter PDF para JPG: {e}", 500

# 3) PDF -> Texto
@app.route("/pdf_to_text", methods=["POST"])
def pdf_to_text():
    pdf_file = request.files.get("file_text")
    if not pdf_file:
        return "Nenhum PDF enviado.", 400

    pdf_filename = f"{uuid.uuid4()}_{pdf_file.filename}"
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
    pdf_file.save(pdf_path)

    try:
        reader = PdfReader(pdf_path)
        all_pages_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            all_pages_text.append(text)

        joined_text = "\n".join(all_pages_text)
        txt_filename = pdf_path.replace(".pdf", ".txt")

        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(joined_text)

        return send_file(txt_filename, as_attachment=True)
    except Exception as e:
        return f"Erro ao extrair texto do PDF: {e}", 500

# 4) Imagens -> PDF
@app.route("/images_to_pdf", methods=["POST"])
def images_to_pdf():
    images_files = request.files.getlist("images_files")
    if not images_files:
        return "Nenhuma imagem enviada.", 400

    try:
        pil_images = []
        for img_file in images_files:
            unique_name = f"{uuid.uuid4()}_{img_file.filename}"
            img_path = os.path.join(UPLOAD_FOLDER, unique_name)
            img_file.save(img_path)

            pil_img = Image.open(img_path).convert("RGB")
            pil_images.append(pil_img)

        first_image = pil_images[0]
        other_images = pil_images[1:]
        output_pdf = os.path.join(UPLOAD_FOLDER, f"imagens_{uuid.uuid4()}.pdf")

        if other_images:
            first_image.save(output_pdf, save_all=True, append_images=other_images)
        else:
            first_image.save(output_pdf)

        return send_file(output_pdf, as_attachment=True)
    except Exception as e:
        return f"Erro ao gerar PDF a partir das imagens: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
