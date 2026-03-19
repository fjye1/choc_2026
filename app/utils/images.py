import os
import uuid
from PIL import Image, UnidentifiedImageError
from flask import current_app

UPLOAD_ROOT = "/var/www/uploads"
CHOC_DIR = "choc"

def save_product_image(file_storage):
    """
    Saves uploaded product image, converts non-standard formats to PNG if needed.
    Returns tuple: (relative_image_path, pdf_friendly_path)
    """
    if not file_storage:
        return None, None

    ext = os.path.splitext(file_storage.filename)[1].lower()
    image_filename = f"{uuid.uuid4()}{ext}"
    save_dir = os.path.join(UPLOAD_ROOT, CHOC_DIR)
    os.makedirs(save_dir, exist_ok=True)
    image_path = os.path.join(save_dir, image_filename)
    file_storage.save(image_path)

    pdf_friendly_filename = image_filename

    if ext not in ['.jpg', '.jpeg', '.png']:
        try:
            png_fname = f"{uuid.uuid4()}.png"
            png_path = os.path.join(save_dir, png_fname)
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img.save(png_path, format="PNG")
            pdf_friendly_filename = png_fname
        except UnidentifiedImageError:
            current_app.logger.exception("Image conversion failed for %s", image_path)
        except Exception:
            current_app.logger.exception("Unexpected error converting image %s", image_path)

    rel_image = f"uploads/{CHOC_DIR}/{image_filename}"
    rel_pdf_image = f"uploads/{CHOC_DIR}/{pdf_friendly_filename}"
    return rel_image, rel_pdf_image