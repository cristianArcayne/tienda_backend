import os
from PIL import Image, ImageChops

def test_collar_dip():
    backend_dir = r"c:\Users\Cristian Arcayne\OneDrive\Documents\Sistemas de Informacion 2\Examen_Si2\fashionstore-backend"
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
    alpha = garment_img.split()[3]
    
    def first_y(x_pos):
        for y in range(gh):
            if alpha.getpixel((x_pos, y)) > 50:
                return y
        return 0

    y_left = first_y(int(gw * 0.22))
    y_right = first_y(int(gw * 0.78))
    y_center = first_y(int(gw * 0.50))
    
    shoulder_avg = (y_left + y_right) // 2
    collar_dip = y_center - shoulder_avg
    print(f"Left shoulder Y: {y_left}, Right shoulder Y: {y_right}, Center neck Y: {y_center}")
    print(f"Average shoulder Y: {shoulder_avg}, Collar dip depth: {collar_dip}px")

if __name__ == "__main__":
    test_collar_dip()

