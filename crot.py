import requests
from PIL import Image
from io import BytesIO
import os
import json
from colorama import Fore, Style, init

# Inisialisasi colorama
init(autoreset=True)

# Lokasi file JSON untuk menyimpan data barcode
DATA_FILES = [
    '/storage/emulated/0/galinx/file1.json',
    '/storage/emulated/0/galinx/file2.json'
]
PLU_DIR = '/storage/emulated/0/galinx/'  # Direktori di mana file PLU disimpan

def load_json_file(file_path):
    """ Memuat data dari file JSON """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print(f"{Fore.RED}{Style.BRIGHT}File '{file_path}' tidak valid. Pastikan file menggunakan format JSON.")
                return []
    else:
        print(f"{Fore.RED}{Style.BRIGHT}File '{file_path}' tidak ditemukan.")
        return []

def find_barcode_data(plu_code):
    """ Mencari data barcode di beberapa file JSON """
    for file_path in DATA_FILES:
        data = load_json_file(file_path)
        for item in data:
            if item.get("PLU") == plu_code:
                return item.get("Barcode")
    return None

def get_next_filename(base_name, extension, folder):
    """ Menghasilkan nama file berikutnya dengan urutan nomor di dalam folder """
    i = 1
    while True:
        filename = os.path.join(folder, f"{base_name}_{i}.{extension}")
        if not os.path.isfile(filename):
            return filename
        i += 1

def create_directory(directory):
    """ Membuat direktori jika belum ada """
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_barcode_as_image(code, barcode_data, file_format, folder):
    """ Menyimpan barcode sebagai gambar dengan format yang ditentukan dalam folder """
    barcode_url = f"https://barcode.tec-it.com/barcode.ashx?data={barcode_data}&code=Code128&translate-esc=on"

    try:
        # Mengunduh gambar barcode
        response = requests.get(barcode_url)
        response.raise_for_status()  # Menghasilkan exception untuk kode status HTTP 4xx/5xx
        # Membuka gambar dari bytes
        img = Image.open(BytesIO(response.content))

        # Konversi gambar ke mode RGB jika diperlukan
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Mengubah ukuran gambar (75% dari ukuran asli)
        width, height = img.size
        new_size = (int(width * 0.75), int(height * 0.75))
        img = img.resize(new_size, Image.LANCZOS)  # Menggunakan Image.LANCZOS untuk resizing

        # Membuat background putih dan menempatkan barcode di tengah
        background = Image.new('RGB', (new_size[0] + 40, new_size[1] + 40), (255, 255, 255))
        position = ((background.width - img.width) // 2, (background.height - img.height) // 2)
        background.paste(img, position)

        # Menentukan nama file berikutnya dan format file
        if file_format == 'JPG':
            file_format = 'JPEG'
        filename = get_next_filename("barcode", file_format.lower(), folder)

        # Menyimpan gambar sebagai file dengan format yang ditentukan
        background.save(filename, file_format)
        print(f"{Fore.GREEN}Barcode untuk kode '{code}' telah disimpan sebagai '{filename}'.")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}{Style.BRIGHT}Terjadi kesalahan saat mengunduh barcode untuk kode '{code}': {e}")
    except IOError as e:
        print(f"{Fore.RED}{Style.BRIGHT}Terjadi kesalahan saat menyimpan gambar untuk kode '{code}': {e}")

def process_barcodes(plu_files, file_format):
    """ Memproses kode barcode yang diberikan dan menyimpannya sebagai gambar """
    not_found_list = []

    for plu_file in plu_files:
        plu_list = load_json_file(plu_file)

        if not plu_list:
            print(f"{Fore.RED}{Style.BRIGHT}Tidak ada data PLU yang tersedia untuk diproses di file '{plu_file}'.")
            continue

        # Membuat folder baru berdasarkan nama file PLU
        folder_name = os.path.splitext(os.path.basename(plu_file))[0]
        folder_path = os.path.join(PLU_DIR, folder_name)
        create_directory(folder_path)

        # Membuat folder untuk PLU yang tidak ditemukan
        not_found_folder = os.path.join(folder_path, "not_found")
        create_directory(not_found_folder)

        for plu_item in plu_list:
            code = plu_item.get("PLU")
            if not code:
                continue

            # Mengambil data barcode sesuai kode dari peta data
            barcode_data = find_barcode_data(code)

            if barcode_data:
                save_barcode_as_image(code, barcode_data, file_format, folder_path)
            else:
                print(f"{Fore.YELLOW}{Style.BRIGHT}Tidak ditemukan data untuk kode barcode '{code}' di semua file JSON.")
                not_found_list.append(code)

    # Simpan PLU yang tidak ditemukan ke dalam file
    if not_found_list:
        not_found_file = os.path.join(not_found_folder, 'not_found_plu.json')
        with open(not_found_file, 'w') as file:
            json.dump(not_found_list, file, indent=4)
        print(f"{Fore.YELLOW}{Style.BRIGHT}Daftar PLU yang tidak ditemukan telah disimpan di '{not_found_file}'.")

def process_single_barcode(plu_codes, file_format):
    """ Memproses beberapa kode barcode yang diberikan secara manual """
    plu_list = plu_codes.split(',')
    folder_path = os.path.join(PLU_DIR, "manual")
    create_directory(folder_path)

    # Membuat folder untuk PLU yang tidak ditemukan
    not_found_folder = os.path.join(folder_path, "not_found")
    create_directory(not_found_folder)

    not_found_list = []

    for code in plu_list:
        code = code.strip()
        # Mengambil data barcode sesuai kode dari peta data
        barcode_data = find_barcode_data(code)

        if barcode_data:
            save_barcode_as_image(code, barcode_data, file_format, folder_path)
        else:
            print(f"{Fore.YELLOW}{Style.BRIGHT}Tidak ditemukan data untuk kode barcode '{code}' di semua file JSON.")
            not_found_list.append(code)

    # Simpan PLU yang tidak ditemukan ke dalam file
    if not_found_list:
        not_found_file = os.path.join(not_found_folder, 'not_found_plu.json')
        with open(not_found_file, 'w') as file:
            json.dump(not_found_list, file, indent=4)
        print(f"{Fore.YELLOW}{Style.BRIGHT}Daftar PLU yang tidak ditemukan telah disimpan di '{not_found_file}'.")

def process_monitoring_pricetag(file_format):
    """ Memproses file monitoring.json dan menyimpan barcode sebagai gambar """
    monitoring_file = '/storage/emulated/0/galinx/monitoring.json'
    plu_list = load_json_file(monitoring_file)

    if not plu_list:
        print(f"{Fore.RED}{Style.BRIGHT}Tidak ada data PLU yang tersedia di file '{monitoring_file}'.")
        return

    # Membuat folder baru untuk hasil monitoring
    folder_path = os.path.join(PLU_DIR, "monitoring")
    create_directory(folder_path)

    # Membuat folder untuk PLU yang tidak ditemukan
    not_found_folder = os.path.join(folder_path, "not_found")
    create_directory(not_found_folder)

    not_found_list = []

    for plu_item in plu_list:
        code = plu_item.get("PLU")
        if not code:
            continue

        # Mengambil data barcode sesuai kode dari peta data
        barcode_data = find_barcode_data(code)

        if barcode_data:
            save_barcode_as_image(code, barcode_data, file_format, folder_path)
        else:
            print(f"{Fore.YELLOW}{Style.BRIGHT}Tidak ditemukan data untuk kode barcode '{code}' di semua file JSON.")
            not_found_list.append(code)

    # Simpan PLU yang tidak ditemukan ke dalam file
    if not_found_list:
        not_found_file = os.path.join(not_found_folder, 'not_found_plu.json')
        with open(not_found_file, 'w') as file:
            json.dump(not_found_list, file, indent=4)
        print(f"{Fore.YELLOW}{Style.BRIGHT}Daftar PLU yang tidak ditemukan telah disimpan di '{not_found_file}'.")

def print_banner():
    """ Mencetak banner informasi dengan teks bold """
    print(f"{Fore.RED}{Style.BRIGHT}" + "_"*38)
    print(f"{Fore.RED}{Style.BRIGHT}" + "-"*38)
    print(f"{Fore.BLUE}{Style.BRIGHT}>>---   Nama pemilik : {Fore.YELLOW}{Style.BRIGHT}rondol{Fore.BLUE}{Style.BRIGHT}    ---<<")
    print(f"{Fore.BLUE}{Style.BRIGHT}>>---   Telegram : {Fore.YELLOW}{Style.BRIGHT}t.me/Ghlinx{Fore.BLUE}{Style.BRIGHT}   ---<<")
    print(f"{Fore.GREEN}{Style.BRIGHT}>--Cetak Barcode, Monitoring & ITT --<{Fore.GREEN}{Style.BRIGHT}")
    print(f"{Fore.RED}{Style.BRIGHT}" + "-"*38)

def main():
    menu_structure = {
        "PPT": ["ppt1.json", "ppt2.json"],
        "DND": ["dnd1.json", "dnd2.json", "dnd3.json", "dnd4.json"],
        "HNM": ["hnm1.json", "hnm2.json"],
        "DIA": ["dia1.json", "dia2.json", "dia3.json"],
        "MBF": ["mbf1.json", "mbf2.json", "mbf3.json", "mbf4.json", "mbf5.json", "mbf6.json"],
        "PCE": ["pce1.json", "pce2.json", "pce3.json", "pce4.json", "pce5.json", "pce6.json", "pce7.json", "pce8.json"],
        "STA": ["sta1.json"],
        "TOY": ["toy1.json"],
        "CNA": ["cna1.json"],
        "IFD": ["ifd1.json", "ifd2.json", "ifd3.json", "ifd4.json"],
        "BFD": ["bfd1.json", "bfd2.json", "bfd3.json", "bfd4.json", "bfd5.json", "bfd6.json"],
        "CON": ["con1.json", "con2.json"],
        "SLK": ["slk1.json"],
        "SHB": ["shb1.json"],
        "SNB": ["snb1.json", "snb2.json", "snb3.json", "snb4.json", "snb5.json", "snb6.json", "snb7.json", "snb8.json", "snb9.json", "snb10.json"],
        "BRE": ["bre1.json", "bre2.json"],
        "BEV": ["bev1.json", "bev2.json"],
        "CLB": ["clb1.json"],
        "YCG": ["ycg1.json"],
        "RBAT": ["rbat1.json"],
        "RG35": ["rg351.json"],
        "MBG": ["mbg1.json"],
        "BWSH": ["bwsh1.json"],
        "MONITORING PRICETAG": [],  # Tambahkan entri ini
        "CETAK BARCODE MANUAL": []
    }

    while True:
        print_banner()
        print(f"{Fore.RED}{Style.BRIGHT}" + "-"*38)

        print(f"{Fore.CYAN}[0] Exit")
        menu_index = 1

        # Menampilkan menu utama
        for category in menu_structure:
            print(f"{Fore.YELLOW}[{menu_index}] {Fore.CYAN}{category}")
            menu_index += 1

        choice = input(f"{Fore.CYAN}Masukkan pilihan Anda: ").strip().upper()
        if choice == '0':
            print(f"{Fore.BLUE}Keluar dari program.")
            break
        elif choice.isdigit() and 1 <= int(choice) < menu_index:
            category_index = int(choice) - 1
            category = list(menu_structure.keys())[category_index]

            if category == "MONITORING PRICETAG":
                file_format = input(f"{Fore.CYAN}Masukkan format file (JPG/PNG): ").upper()
                if file_format not in ["JPG", "PNG"]:
                    print(f"{Fore.RED}{Style.BRIGHT}Format file tidak valid. Gunakan 'JPG' atau 'PNG'.")
                else:
                    process_monitoring_pricetag(file_format)
                continue
            elif category == "CETAK BARCODE MANUAL":
                plu_codes = input(f"{Fore.CYAN}Masukkan PLU: ").strip()
                file_format = input(f"{Fore.CYAN}Masukkan format file (JPG/PNG): ").upper()
                if file_format not in ["JPG", "PNG"]:
                    print(f"{Fore.RED}{Style.BRIGHT}Format file tidak valid. Gunakan 'JPG' atau 'PNG'.")
                else:
                    process_single_barcode(plu_codes, file_format)
                continue

            subitems = menu_structure[category]
            print(f"{Fore.CYAN}[0] Kembali")

            # Menampilkan submenu
            for i, subitem in enumerate(subitems, start=1):
                print(f"{Fore.YELLOW}[{i}] {Fore.CYAN}{subitem}")

            sub_choice = input(f"{Fore.CYAN}Masukkan pilihan Anda: ").strip().upper()
            if sub_choice == '0':
                continue
            elif all(x.isdigit() and 1 <= int(x) <= len(subitems) for x in sub_choice.split(',')):
                selected_files = [subitems[int(x) - 1] for x in sub_choice.split(',')]
                file_format = input(f"{Fore.CYAN}Masukkan format file (JPG/PNG): ").upper()
                if file_format not in ["JPG", "PNG"]:
                    print(f"{Fore.RED}{Style.BRIGHT}Format file tidak valid. Gunakan 'JPG' atau 'PNG'.")
                else:
                    process_barcodes([os.path.join(PLU_DIR, file) for file in selected_files], file_format)
            else:
                print(f"{Fore.RED}{Style.BRIGHT}Pilihan tidak valid.")
        else:
            print(f"{Fore.RED}{Style.BRIGHT}Pilihan tidak valid.")
        print(f"{Fore.RED}{Style.BRIGHT}" + "_"*38)

if __name__ == "__main__":
    main()
