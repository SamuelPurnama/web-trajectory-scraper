import base64
from io import BytesIO

from PIL import Image


def pil_image_to_base64(pil_image: Image.Image, format="PNG"):
    """
    Encode a PIL Image to base64 string

    Args:
        pil_image: PIL Image object
        format: Image format (PNG, JPEG, etc.)

    Returns:
        base64 encoded string
    """
    buffered = BytesIO()
    pil_image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    return img_base64


def pil_image_to_html(pil_image: Image.Image):
    base64_image = pil_image_to_base64(pil_image)
    html = f'<img src="data:image/png;base64,{base64_image}" alt="Image">'
    return html
