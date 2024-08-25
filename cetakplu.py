import barcode
from barcode.writer import ImageWriter

def generate_code_128(plu_list):
    for plu in plu_list:
        plu = plu.strip()
        if not plu:
            continue
        # Buat barcode Code 128
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(plu, writer=ImageWriter())
        
        # Simpan barcode sebagai gambar PNG
        filename = f'{plu}_code128'
        barcode_instance.save(filename)
        print(f'Barcode disimpan sebagai {filename}.png')

# Input beberapa PLU atau angka, dipisahkan dengan koma
plu_input = input('Masukkan PLU atau angka, dipisahkan dengan koma: ')
plu_list = plu_input.split(',')

generate_code_128(plu_list)
