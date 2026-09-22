import os
from PIL import Image, ImageOps, ImageFilter, ImageChops

def test_guarantee():
    backend_dir = r"c:\Users\Cristian Arcayne\OneDrive\Documents\Sistemas de Informacion 2\Examen_Si2\fashionstore-backend"
    ref_photo_path = r"C:\Users\Cristian Arcayne\.gemini\antigravity\brain\1dff14a3-ab66-4824-8e2f-eaa0f94da574\ejemplo_foto_ideal_vestidor_1790056875414.jpg"
    
    if not os.path.exists(ref_photo_path):
        print("Reference photo not found")
        return
        
    user_img = Image.open(ref_photo_path).convert("RGBA")
    u_w, u_h = user_img.size
    print(f"Reference photo size: {u_w}x{u_h}")
    
    # Prenda de prueba (Polera Oversize Negra)
    garment_path = os.path.join(backend_dir, "static", "uploads", "polera_oversize_negra.jpg")
    garment_img = Image.open(garment_path).convert("RGBA")
    
    threshold = 215
    r, g, b, a = garment_img.split()
    mask_r = r.point(lambda p: 0 if p > threshold else 255)
    mask_g = g.point(lambda p: 0 if p > threshold else 255)
    mask_b = b.point(lambda p: 0 if p > threshold else 255)
    mask_combined = ImageChops.lighter(ImageChops.lighter(mask_r, mask_g), mask_b)
    mask_final = ImageChops.darker(a, mask_combined)
    
    mask_final = mask_final.filter(ImageFilter.MinFilter(size=3))
    garment_img.putalpha(mask_final)
    
    bbox = garment_img.getbbox()
    if bbox:
        garment_img = garment_img.crop(bbox)
        
    gw, gh = garment_img.size
    alpha_prenda = garment_img.split()[3]
    
    def obtener_y_primer_pixel(x_pos):
        for y in range(gh):
            if alpha_prenda.getpixel((x_pos, y)) > 50:
                return y
        return 0

    y_left_shoulder = obtener_y_primer_pixel(int(gw * 0.22))
    y_right_shoulder = obtener_y_primer_pixel(int(gw * 0.78))
    shoulder_y_offset = (y_left_shoulder + y_right_shoulder) // 2
    
    # Escala para cubrir la persona (84% del ancho de la persona)
    torso_w = int(u_w * 0.84)
    aspect_garment = gh / max(gw, 1)
    torso_h = int(torso_w * aspect_garment)
    
    max_h = int(u_h * 0.58)
    if torso_h > max_h:
        torso_h = max_h
        torso_w = int(torso_h / aspect_garment)
        
    garment_resized = garment_img.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
    
    w_res, h_res = garment_resized.size
    taper_x = int(w_res * 0.02)
    quad = (-taper_x, 0, 0, h_res, w_res, h_res, w_res + taper_x, 0)
    garment_warped = garment_resized.transform((w_res, h_res), Image.QUAD, quad, resample=Image.Resampling.BILINEAR)
    
    alpha_ch = garment_warped.split()[3]
    alpha_blurred = alpha_ch.filter(ImageFilter.GaussianBlur(radius=1.2))
    garment_warped.putalpha(alpha_blurred)
    
    pos_x = (u_w - torso_w) // 2
    target_shoulder_y = int(u_h * 0.255)
    scaled_shoulder_offset = int(shoulder_y_offset * (torso_h / gh))
    pos_y = target_shoulder_y - scaled_shoulder_offset
    
    combined = user_img.copy()
    combined.paste(garment_warped, (pos_x, pos_y), garment_warped)
    
    out_path = r"C:\Users\Cristian Arcayne\.gemini\antigravity\brain\1dff14a3-ab66-4824-8e2f-eaa0f94da574\resultado_ropa_cambiada.jpg"
    combined.convert("RGB").save(out_path, format="JPEG", quality=95)
    print("Saved guarantee try-on result to:", out_path)

if __name__ == "__main__":
    test_guarantee()

