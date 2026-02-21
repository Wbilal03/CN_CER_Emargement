from PIL import Image
import numpy as np

def convert_canvas_to_image(canvas_result):
    """
    Convertit le résultat du canvas Streamlit en PIL.Image.
    """
    if canvas_result is None or canvas_result.image_data is None:
        return None

    rgba = np.array(canvas_result.image_data, copy=True)

    # Le canvas peut renvoyer des valeurs en [0, 1] ou en [0, 255].
    if rgba.max() <= 1.0:
        rgba = (rgba * 255).astype(np.uint8)
    else:
        rgba = np.clip(rgba, 0, 255).astype(np.uint8)

    # Composition sur fond blanc pour eviter un fond noir dans le PDF.
    if rgba.shape[2] == 4:
        alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
        rgb = rgba[:, :, :3].astype(np.float32)
        white_bg = np.full_like(rgb, 255.0)
        rgb = (rgb * alpha) + (white_bg * (1.0 - alpha))
        img_array = rgb.astype(np.uint8)
    else:
        img_array = rgba[:, :, :3]

    img = Image.fromarray(img_array, mode="RGB")
    return img
