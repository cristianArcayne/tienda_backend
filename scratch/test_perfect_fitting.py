import os
import io
import base64
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

def test_perfect_fitting():
    backend_dir = r"c:\Users\Cristian Arcayne\OneDrive\Documents\Sistemas de Informacion 2\Examen_Si2\fashionstore-backend"
    
    # 1. Foto de usuario sintética
    user_img = Image.new("RGBA", (768, 1024), (245, 245, 245, 255))
    u_w, u_h = user_img.size
    
    # Prenda de prueba
    garment_path = os.path.join(backend_dir, "static", "uploads", "polera_oversize_negra.jpg")
    garment_img = Image.open(garment_path).convert("RGBA")
    
    # Limpieza de silueta
    threshold = 230
    r, g, b, a = garment_img.split()
    mask_r = r.point(lambda p: 0 if p > threshold else 255)
    mask_g = g.point(lambda p: 0 if p > threshold else 255)
    mask_b = b.point(lambda p: 0 if p > threshold else 255)
    mask_combined = ImageChops.lighter(ImageChops.lighter(mask_r, mask_g), mask_b)
    mask_final = ImageChops.darker(a, mask_combined)
    garment_img.putalpha(mask_final)
    
    bbox = garment_img.getbbox()
    if bbox:
        garment_img = garment_img.crop(bbox)
        
    gw, gh = garment_img.size
    alpha = garment_img.split()[3]
    
    def first_y(x_pos):
        for y in range(gh):
            if alpha.getpixel((x_pos, y)) > 50:
                return y
        return 0

    y_left = first_y(int(gw * 0.22))
    y_right = first_y(int(gw * 0.78))
    shoulder_y_offset = (y_left + y_right) // 2
    
    # Ajuste de ancho de torso
    ratio = u_w / u_h
    es_retrato = ratio > 0.60
    
    torso_w = int(u_w * (0.64 if es_retrato else 0.66))
    aspect = gh / max(gw, 1)
    torso_h = int(torso_w * aspect)
    
    max_h = int(u_h * 0.48)
    if torso_h > max_h:
        torso_h = max_h
        torso_w = int(torso_h / aspect)
        
    garment_resized = garment_img.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
    
    # Deformación anatómica trapezoidal (Shoulder Taper)
    w, h = garment_resized.size
    taper_x = int(w * 0.035)
    quad = (-taper_x, 0, 0, h, w, h, w + taper_x, 0)
    garment_warped = garment_resized.transform((w, h), Image.QUAD, quad, resample=Image.Resampling.BILINEAR)
    
    # Desvanecimiento sutil de bordes (Feathering)
    alpha_ch = garment_warped.split()[3]
    alpha_blurred = alpha_ch.filter(ImageFilter.GaussianBlur(radius=1.2))
    garment_warped.putalpha(alpha_blurred)
    
    # Posicionamiento exacto por la línea de hombros
    pos_x = (u_w - torso_w) // 2
    target_shoulder_y = int(u_h * (0.30 if es_retrato else 0.22))
    scaled_shoulder_offset = int(shoulder_y_offset * (torso_h / gh))
    pos_y = target_shoulder_y - scaled_shoulder_offset
    
    combined = user_img.copy()
    combined.paste(garment_warped, (pos_x, pos_y), garment_warped)
    
    out_path = os.path.join(backend_dir, "scratch", "test_perfect_fitting.jpg")
    combined.convert("RGB").save(out_path, format="JPEG", quality=95)
    print("Perfect fitting test saved to:", out_path)

if __name__ == "__main__":
    test_perfect_fitting()
