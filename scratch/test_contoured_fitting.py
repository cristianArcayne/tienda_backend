import os
from PIL import Image, ImageOps, ImageFilter, ImageChops

def test_contoured_fitting():
    backend_dir = r"c:\Users\Cristian Arcayne\OneDrive\Documents\Sistemas de Informacion 2\Examen_Si2\fashionstore-backend"
    ref_photo_path = r"C:\Users\Cristian Arcayne\.gemini\antigravity\brain\1dff14a3-ab66-4824-8e2f-eaa0f94da574\ejemplo_foto_ideal_vestidor_1790056875414.jpg"
    
    if not os.path.exists(ref_photo_path):
        print("Reference photo not found")
        return
        
    user_img = Image.open(ref_photo_path).convert("RGBA")
    u_w, u_h = user_img.size
    
    garment_path = os.path.join(backend_dir, "static", "uploads", "polera_oversize_negra.jpg")
    garment_img = Image.open(garment_path).convert("RGBA")
    
    # 1. Limpieza de silueta
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
    
    # Escala base
    torso_w = int(u_w * 0.82)
    aspect_garment = gh / max(gw, 1)
    torso_h = int(torso_w * aspect_garment)
    
    max_h = int(u_h * 0.56)
    if torso_h > max_h:
        torso_h = max_h
        torso_w = int(torso_h / aspect_garment)
        
    garment_resized = garment_img.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
    w_res, h_res = garment_resized.size
    
    # 2. Deformación Curvada de Cintura y Silueta Anatómica (Waist & Torso Contour Warp)
    # Creamos un canvas con deformación de curva de cintura
    # Dividimos la prenda en 2 secciones verticales (Torso superior e inferior)
    top_h = int(h_res * 0.45)
    bottom_h = h_res - top_h
    
    top_half = garment_resized.crop((0, 0, w_res, top_h))
    bottom_half = garment_resized.crop((0, top_h, w_res, h_res))
    
    # Sección superior: Hombros ligeramente estrechados arriba (slope taper)
    taper_top = int(w_res * 0.025)
    quad_top = (-taper_top, 0, 0, top_h, w_res, top_h, w_res + taper_top, 0)
    top_warped = top_half.transform((w_res, top_h), Image.QUAD, quad_top, resample=Image.Resampling.BILINEAR)
    
    # Sección inferior: Ajuste de cintura (entalle suave en el medio)
    waist_taper = int(w_res * 0.04) # 4% de curva hacia la cintura
    quad_bottom = (0, 0, waist_taper, bottom_h, w_res - waist_taper, bottom_h, w_res, 0)
    bottom_warped = bottom_half.transform((w_res, bottom_h), Image.QUAD, quad_bottom, resample=Image.Resampling.BILINEAR)
    
    # Unir ambas secciones contorneadas
    contoured_garment = Image.new("RGBA", (w_res, h_res), (0, 0, 0, 0))
    contoured_garment.paste(top_warped, (0, 0))
    contoured_garment.paste(bottom_warped, (0, top_h))
    
    # Desvanecimiento orgánico de bordes
    alpha_ch = contoured_garment.split()[3]
    alpha_blurred = alpha_ch.filter(ImageFilter.GaussianBlur(radius=1.3))
    contoured_garment.putalpha(alpha_blurred)
    
    pos_x = (u_w - torso_w) // 2
    target_shoulder_y = int(u_h * 0.255)
    scaled_shoulder_offset = int(shoulder_y_offset * (torso_h / gh))
    pos_y = target_shoulder_y - scaled_shoulder_offset
    
    combined = user_img.copy()
    combined.paste(contoured_garment, (pos_x, pos_y), contoured_garment)
    
    out_path = r"C:\Users\Cristian Arcayne\.gemini\antigravity\brain\1dff14a3-ab66-4824-8e2f-eaa0f94da574\resultado_chaqueta_perfecta.jpg"
    combined.convert("RGB").save(out_path, format="JPEG", quality=95)
    print("Saved contoured fitting result to:", out_path)

if __name__ == "__main__":
    test_contoured_fitting()

