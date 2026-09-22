import os
import io
import base64
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

def test_enhanced_composite():
    backend_dir = r"c:\Users\Cristian Arcayne\OneDrive\Documents\Sistemas de Informacion 2\Examen_Si2\fashionstore-backend"
    
    # Load sample user photo (or create synthetic test user photo)
    user_img = Image.new("RGBA", (768, 1024), (240, 235, 225, 255))
    u_w, u_h = user_img.size
    
    # Load real garment image from static/uploads
    garment_path = os.path.join(backend_dir, "static", "uploads", "polera_oversize_negra.jpg")
    garment_img = Image.open(garment_path).convert("RGBA")
    
    # 1. Extracción limpia de silueta con desvanecimiento de bordes
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
    
    # 2. Medir profundidad del cuello (collar dip)
    center_alpha = garment_img.split()[3]
    collar_dip_y = 0
    center_x = gw // 2
    for y in range(gh):
        if center_alpha.getpixel((center_x, y)) > 50:
            collar_dip_y = y
            break
            
    print(f"Garment size: {gw}x{gh}, Collar dip Y: {collar_dip_y}")
    
    # 3. Ancho de torso adaptativo
    torso_w = int(u_w * 0.64)
    aspect = gh / max(gw, 1)
    torso_h = int(torso_w * aspect)
    
    garment_resized = garment_img.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
    
    # 4. Deformación anatómica de hombros (Shoulder Taper)
    w, h = garment_resized.size
    taper_x = int(w * 0.035)
    quad = (-taper_x, 0, 0, h, w, h, w + taper_x, 0)
    garment_warped = garment_resized.transform((w, h), Image.QUAD, quad, resample=Image.Resampling.BILINEAR)
    
    # Suavizado de bordes (Feathering)
    alpha_ch = garment_warped.split()[3]
    alpha_blurred = alpha_ch.filter(ImageFilter.GaussianBlur(radius=1.2))
    garment_warped.putalpha(alpha_blurred)
    
    pos_x = (u_w - torso_w) // 2
    scaled_collar_dip = int(collar_dip_y * (torso_h / gh))
    pos_y = int(u_h * 0.32) - scaled_collar_dip
    
    combined = user_img.copy()
    combined.paste(garment_warped, (pos_x, pos_y), garment_warped)
    
    out_path = os.path.join(backend_dir, "scratch", "test_composite_result.jpg")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    combined.convert("RGB").save(out_path, format="JPEG", quality=95)
    print("Saved test composite result to:", out_path)

if __name__ == "__main__":
    test_enhanced_composite()
