import os
from PIL import Image, ImageChops, ImageFilter

def test_user_photo_fit():
    backend_dir = r"c:\Users\Cristian Arcayne\OneDrive\Documents\Sistemas de Informacion 2\Examen_Si2\fashionstore-backend"
    
    # 1. Cargar la foto real subida por el usuario
    user_photo_path = r"C:\Users\Cristian Arcayne\.gemini\antigravity\brain\1dff14a3-ab66-4824-8e2f-eaa0f94da574\.user_uploaded\media_1790052968289.png"
    if not os.path.exists(user_photo_path):
        print("User photo not found")
        return
        
    user_img = Image.open(user_photo_path).convert("RGBA")
    u_w, u_h = user_img.size
    print(f"User image size: {u_w}x{u_h}")
    
    # 2. Cargar la prenda
    garment_path = os.path.join(backend_dir, "static", "uploads", "polera_oversize_negra.jpg")
    garment_img = Image.open(garment_path).convert("RGBA")
    
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
    alpha_prenda = garment_img.split()[3]
    
    def obtener_y_primer_pixel(x_pos):
        for y in range(gh):
            if alpha_prenda.getpixel((x_pos, y)) > 50:
                return y
        return 0

    y_left_shoulder = obtener_y_primer_pixel(int(gw * 0.22))
    y_right_shoulder = obtener_y_primer_pixel(int(gw * 0.78))
    shoulder_y_offset = (y_left_shoulder + y_right_shoulder) // 2
    
    # Probemos ajustar pos_y para fotos donde los hombros están alrededor del 48-52% de la imagen (como en la foto del usuario)
    # En la foto del usuario, el rostro toma los primeros 45% y los hombros están a y=500 de 1024 (aprox 0.48 - 0.50)
    torso_w = int(u_w * 0.76)
    aspect_garment = gh / max(gw, 1)
    torso_h = int(torso_w * aspect_garment)
    
    garment_resized = garment_img.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
    
    w, h = garment_resized.size
    taper_x = int(w * 0.02)
    quad = (-taper_x, 0, 0, h, w, h, w + taper_x, 0)
    garment_warped = garment_resized.transform((w, h), Image.QUAD, quad, resample=Image.Resampling.BILINEAR)
    
    alpha_ch = garment_warped.split()[3]
    alpha_blurred = alpha_ch.filter(ImageFilter.GaussianBlur(radius=1.2))
    garment_warped.putalpha(alpha_blurred)
    
    pos_x = (u_w - torso_w) // 2
    # El usuario tiene la cabeza en primer plano, hombros inician en y ~ 0.48 * u_h
    target_shoulder_y = int(u_h * 0.48)
    scaled_shoulder_offset = int(shoulder_y_offset * (torso_h / gh))
    pos_y = target_shoulder_y - scaled_shoulder_offset
    
    combined = user_img.copy()
    combined.paste(garment_warped, (pos_x, pos_y), garment_warped)
    
    out_path = os.path.join(backend_dir, "scratch", "test_user_photo_fit.jpg")
    combined.convert("RGB").save(out_path, format="JPEG", quality=95)
    print("Saved user photo fit to:", out_path)

if __name__ == "__main__":
    test_user_photo_fit()

