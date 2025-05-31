import re
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.chrome.service import Service # Diambil dari kode Anda

# --- Step 2 dari kode Anda: Konfigurasi WebDriver ---
# Pastikan path ke chromedriver.exe sudah benar
executable_path = r"chromedriver\120\chromedriver.exe" # Sesuaikan dengan path Anda
service = Service(executable_path)
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument('--ignore-certificate-errors')
options.add_argument('--start-maximized') # Memulai browser dalam mode maximize
# options.add_argument('--headless') # Jika ingin menjalankan tanpa membuka UI browser (opsional)
# Opsi untuk menonaktifkan notifikasi browser bawaan (mungkin tidak selalu efektif untuk notifikasi dalam halaman)
options.add_argument("--disable-notifications")


driver = webdriver.Chrome(service=service, options=options)
driver.get("https://mamikos.com/")
print("Berhasil membuka Mamikos.com")

# Fungsi untuk menangani notifikasi awal ("Mau dapat notifikasi promo...")
def handle_initial_notification(driver_instance, timeout=10):
    """
    Mencoba untuk menutup notifikasi awal "Mau dapat notifikasi promo..."
    dengan mengklik tombol "Nanti Saja".
    """
    try:
        print("Mencoba menangani notifikasi awal (promo)...")
        possible_later_button_xpaths = [
            "//button[normalize-space()='Nanti Saja']"
        ]
        nanti_saja_button = None
        for xpath_option in possible_later_button_xpaths:
            try:
                nanti_saja_button = WebDriverWait(driver_instance, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_option))
                )
                print(f"Tombol 'Nanti Saja' ditemukan dengan XPath: {xpath_option}")
                break
            except TimeoutException:
                print(f"Tombol 'Nanti Saja' tidak ditemukan dengan XPath: {xpath_option}")
        
        if nanti_saja_button:
            nanti_saja_button.click()
            print("Notifikasi awal (promo) ditutup dengan mengklik 'Nanti Saja'.")
            time.sleep(1)
        else:
            print("Notifikasi awal (promo) tidak ditemukan atau tombol 'Nanti Saja' tidak dapat diklik.")
    except TimeoutException:
        print("Notifikasi awal (promo) tidak muncul dalam waktu yang ditentukan atau tidak dapat ditangani.")
    except Exception as e:
        print(f"Error saat mencoba menangani notifikasi awal: {e}")

# Fungsi untuk menangani notifikasi "Promo Ngebut"
def handle_promo_ngebut_notification(driver_instance, timeout=10):
    """
    Mencoba untuk menutup notifikasi "Mamikos Promo Ngebut"
    dengan mengklik tombol "Saya mengerti", hanya menggunakan XPath yang diberikan pengguna.
    """
    try:
        print("Mencoba menangani notifikasi 'Promo Ngebut'...")
        # Hanya menggunakan XPath yang Anda berikan
        user_provided_xpath = '//*[@id="filterKostTypeWrapper"]/div/div[1]/div[1]/div/div/div[3]/button'
        
        saya_mengerti_button = None
        try:
            saya_mengerti_button = WebDriverWait(driver_instance, timeout).until(
                EC.element_to_be_clickable((By.XPATH, user_provided_xpath))
            )
            print(f"Tombol 'Saya mengerti' (Promo Ngebut) ditemukan dengan XPath: {user_provided_xpath}")
        except TimeoutException:
            print(f"Tombol 'Saya mengerti' (Promo Ngebut) TIDAK ditemukan dengan XPath: {user_provided_xpath}")

        if saya_mengerti_button:
            try:
                driver_instance.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", saya_mengerti_button)
                time.sleep(0.5)
                saya_mengerti_button.click()
            except ElementNotInteractableException:
                print("Klik biasa gagal untuk 'Saya mengerti', mencoba klik dengan JavaScript.")
                driver_instance.execute_script("arguments[0].click();", saya_mengerti_button)
            print("Notifikasi 'Promo Ngebut' ditutup.")
            time.sleep(1)
        else:
            print("Notifikasi 'Promo Ngebut' tidak ditemukan atau tombol 'Saya mengerti' tidak dapat diklik menggunakan XPath yang diberikan.")
    except TimeoutException: # Ini akan menangkap timeout dari WebDriverWait jika elemen tidak pernah muncul
        print("Notifikasi 'Promo Ngebut' tidak muncul dalam waktu yang ditentukan atau tidak dapat ditangani (WebDriverWait timeout).")
    except Exception as e:
        print(f"Error saat mencoba menangani notifikasi 'Promo Ngebut': {e}")



# Fungsi scroll_down (tetap berguna)
def scroll_down(driver_instance):
    driver_instance.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# Fungsi untuk scrape data dari elemen kos yang terlihat
def scrape_visible_kos_data(driver_instance):
    scraped_data_on_page = []
    kos_cards = driver_instance.find_elements(By.XPATH, '//div[contains(@class, "rc-overview")]//div[contains(@class, "rc-overview-card")]')
    # print(f"Menemukan {len(kos_cards)} kartu kos di halaman saat ini.") # Kurangi verbosity

    if not kos_cards:
        kos_cards = driver_instance.find_elements(By.CSS_SELECTOR, 'div.rc-overview > div.rc-overview-card')
        # print(f"Mencoba selector alternatif, menemukan {len(kos_cards)} kartu kos.")

    for card in kos_cards:
        try:
            nama_kos = "Tidak Ditemukan"
            fasilitas_kos = "Tidak Ditemukan"
            harga_kos = "Tidak Ditemukan"
            try:
                nama_element = card.find_element(By.XPATH, './/span[contains(@class, "rc-info__name")]')
                nama_kos = nama_element.text.strip()
            except NoSuchElementException: pass
            try:
                fasilitas_elements = card.find_elements(By.XPATH, './/div[contains(@class, "rc-facilities__item")]/span')
                fasilitas_list = [fe.text.strip() for fe in fasilitas_elements if fe.text.strip()]
                fasilitas_kos = ", ".join(fasilitas_list) if fasilitas_list else "Tidak Ada Info Fasilitas"
                fasilitas_kos = re.sub(r'[^a-zA-Z0-9\s,]', '', fasilitas_kos)
            except NoSuchElementException: pass
            try:
                harga_element = card.find_element(By.XPATH, './/div[contains(@class, "rc-price")]/p[contains(@class, "rc-price__text")]')
                harga_kos = harga_element.text.strip()
            except NoSuchElementException: pass
            
            if nama_kos != "Tidak Ditemukan" or harga_kos != "Tidak Ditemukan":
                scraped_data_on_page.append({
                    'Nama_Kos': nama_kos,
                    'Fasilitas': fasilitas_kos,
                    'Harga': harga_kos
                })
        except Exception as e_scrape_item:
            print(f"Error saat men-scrape satu item kos: {e_scrape_item}")
            continue
    return scraped_data_on_page

# --- Bagian Utama Skrip ---
scraped_data_list = [] 
try:
    start_time = time.time()
    # handle_initial_notification(driver)

    print("Mencari dan mengklik elemen 'cari'...")
    possible_search_box_xpaths = [
        '//*[@id="home"]/div[4]/div/div/div/div[1]',
        '//input[contains(@class, "search-input") or contains(@class, "SearchInput")]',
        '//*[@data-testid="input-search-input-comp"]',
        '//*[@id="home-search-input"]',
        '//*[@id="home"]/div[4]/div/div/div/div[1]', # XPath lama Anda, mungkin perlu disesuaikan dengan struktur div terbaru
        '//*[@id="home"]/div[5]/div/div/div/div[1]'  # XPath lain dari histori
    ]
    cari = None
    for xpath_option in possible_search_box_xpaths:
        try:
            cari = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_option)))
            print(f"Elemen 'cari' ditemukan dengan XPath: {xpath_option}")
            break
        except TimeoutException: print(f"Elemen 'cari' tidak ditemukan dengan XPath: {xpath_option}")
    if not cari: raise Exception("Tidak dapat menemukan elemen 'cari' (kotak pencarian utama). Periksa XPath.")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", cari)
    time.sleep(0.5); cari.click(); print("Elemen 'cari' diklik/diaktifkan.")

    print("Mencari dan mengklik elemen 'area' (misal: Yogyakarta)...")
    area_xpath = '//*[@id="home"]/div[13]/div/div[2]/div[2]/ul/li[2]' 
    try:
        area = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, area_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", area)
        time.sleep(0.5); area.click(); print("Elemen 'area' diklik.")
    except TimeoutException:
        print(f"GAGAL mengklik 'area' dengan XPath: {area_xpath}.")
        raise Exception("Gagal menemukan atau mengklik elemen 'area'.")

    print("Mencari dan mengklik elemen 'kota' (dropdown)...")
    kota_xpath = '//*[@id="home"]/div[13]/div/div[2]/div[4]/div/div[9]/details' # XPath ini sangat mungkin berubah
    try:
        kota = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, kota_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", kota)
        time.sleep(0.5); kota.click(); print("Elemen 'kota' (dropdown) diklik.")
    except TimeoutException:
        print(f"GAGAL mengklik 'kota' (dropdown) dengan XPath: {kota_xpath}.")
        raise Exception("Gagal menemukan atau mengklik elemen 'kota' (dropdown).")

    print("Mencari dan mengklik elemen 'kota_2' (pilihan kota)...")
    target_kota_2_xpath = '//*[@id="home"]/div[12]/div/div[2]/div[4]/div/div[9]/details/div/a[2]'
    try:
        kota_2 = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, target_kota_2_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", kota_2)
        time.sleep(0.5); kota_2.click(); print("Elemen 'kota_2' (pilihan kota) diklik.")
    except TimeoutException:
        print(f"GAGAL mengklik 'kota_2' (pilihan kota) dengan XPath: {target_kota_2_xpath}.")
        raise Exception("Gagal menemukan atau mengklik elemen 'kota_2' (pilihan kota).")

    print("Menunggu halaman hasil pencarian kota termuat...")
    time.sleep(3) 

    # Panggil fungsi untuk menangani notifikasi "Promo Ngebut" setelah memilih kota
    handle_promo_ngebut_notification(driver)
    time.sleep(2) # Beri jeda setelah menangani notifikasi

    # --- Loop Pagination ---
    page_count = 0
    max_pages_to_scrape = 5 # Batasi jumlah halaman untuk testing (atau sesuaikan)
    print("Memulai loop pagination untuk memuat semua data...")
    while page_count < max_pages_to_scrape:
        page_count += 1
        print(f"--- Mencoba memuat halaman/data tambahan ke-{page_count} ---")
        scroll_down(driver); time.sleep(1) # Scroll untuk memicu pemuatan
        
        # Coba tangani notifikasi promo ngebut lagi jika muncul di antara pagination
        if page_count > 1: # Jangan panggil di halaman pertama lagi jika sudah ditangani
            handle_promo_ngebut_notification(driver, timeout=3) 
            time.sleep(0.5) # Jeda setelah handle notif
        
        try:
            next_button_selectors = [
                (By.CLASS_NAME, 'list__content-load-link'), # Sesuai log Anda
                (By.XPATH, '//button[contains(translate(text(), "MUAT LEBIH BANYAK", "muat lebih banyak"), "muat lebih banyak")]'),
                (By.XPATH, '//a[contains(translate(text(), "MUAT LEBIH BANYAK", "muat lebih banyak"), "muat lebih banyak")]'),
            ]
            next_button_found_and_clicked = False
            for strategy, selector_value in next_button_selectors:
                try:
                    # print(f"Mencoba menemukan tombol 'next' dengan {strategy}: {selector_value}") # Kurangi verbosity
                    next_button = WebDriverWait(driver, 7).until( # Timeout lebih pendek untuk cek tombol next
                        EC.element_to_be_clickable((strategy, selector_value))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", next_button)
                    time.sleep(0.3)
                    next_button.click()
                    print(f"Tombol 'next' ({selector_value}) diklik.")
                    next_button_found_and_clicked = True
                    print("Menunggu konten halaman selanjutnya dimuat (3-5 detik)...")
                    time.sleep(4) # Waktu tunggu setelah klik next
                    break 
                except TimeoutException: 
                    # print(f"Tombol 'next' dengan {strategy}: {selector_value} tidak ditemukan atau tidak clickable.")
                    pass # Coba selector berikutnya
                except ElementNotInteractableException: 
                    # print(f"Tombol 'next' dengan {strategy}: {selector_value} tidak interactable.")
                    pass # Coba selector berikutnya
            
            if not next_button_found_and_clicked: 
                print("Tidak ada tombol 'next' yang ditemukan atau bisa diklik lagi. Mengakhiri pagination.")
                break 
        
        except ElementNotInteractableException: 
            print("ElementNotInteractableException saat mencoba klik next_button utama.")
            try:
                print("Mencoba menangani popup (jika ada)...")
                handle_promo_ngebut_notification(driver, timeout=3) 
                if not next_button_found_and_clicked: 
                     handle_initial_notification(driver, timeout=3)
                continue 
            except TimeoutException: 
                print("Tidak dapat menemukan tombol pada popup setelah ElementNotInteractableException. Mengakhiri pagination."); break
        except TimeoutException: 
            print("TimeoutException: Tombol next tidak ditemukan setelah semua usaha. Mengakhiri pagination."); break
        except Exception as e_pagination: 
            print(f"Error tak terduga di loop pagination: {e_pagination}"); break
            
    print(f"Selesai loop pagination setelah {page_count} iterasi.")
    print("Menunggu beberapa saat agar semua elemen termuat sepenuhnya...")
    time.sleep(5) # Beri waktu ekstra setelah semua pagination selesai

    # --- Pengambilan Data Sesuai Instruksi Anda (Setelah Semua Pagination) ---
    print("\nMengambil data kos setelah semua halaman dimuat...")
    try:
        elemen_nama = driver.find_elements(By.CLASS_NAME, 'rc-info')
        elemen_fasilitas = driver.find_elements(By.CLASS_NAME, 'rc-facilities')
        # Untuk harga, berdasarkan gambar Anda, class 'rc-price__text' ada di dalam elemen dengan class 'rc-price'
        # Jadi, kita bisa mencari 'rc-price' dulu, lalu 'rc-price__text' di dalamnya, atau langsung 'rc-price__text'
        elemen_harga = driver.find_elements(By.CLASS_NAME, 'rc-price__text')

        print(f"Ditemukan {len(elemen_nama)} elemen nama.")
        print(f"Ditemukan {len(elemen_fasilitas)} elemen fasilitas.")
        print(f"Ditemukan {len(elemen_harga)} elemen harga.")

        if not (elemen_nama and elemen_fasilitas and elemen_harga):
            print("Salah satu atau lebih list elemen (nama, fasilitas, harga) kosong. Tidak dapat memproses data.")
        elif not (len(elemen_nama) == len(elemen_fasilitas) == len(elemen_harga)):
            print("PERINGATAN: Jumlah elemen nama, fasilitas, dan harga tidak sama!")
            print(f"Nama: {len(elemen_nama)}, Fasilitas: {len(elemen_fasilitas)}, Harga: {len(elemen_harga)}")
            print("Data mungkin tidak selaras. Akan tetap diproses dengan jumlah elemen terkecil.")
            min_len = min(len(elemen_nama), len(elemen_fasilitas), len(elemen_harga))
            elemen_nama = elemen_nama[:min_len]
            elemen_fasilitas = elemen_fasilitas[:min_len]
            elemen_harga = elemen_harga[:min_len]

        for nama, fasilitas, harga in zip(elemen_nama, elemen_fasilitas, elemen_harga):
            try:
                # Untuk nama, rc-info bisa jadi container. Kita coba cari rc-info__name di dalamnya.
                # Jika tidak, ambil teks dari rc-info.
                try:
                    nama_kos_text = nama.find_element(By.CLASS_NAME, 'rc-info__name').text.strip()
                except NoSuchElementException:
                    nama_kos_text = nama.text.strip() # Ambil semua teks di rc-info jika rc-info__name tidak ada

                fasilitas_text_cleaned = re.sub(r'[^a-zA-Z0-9\s,]', '', fasilitas.text.strip())
                harga_text = harga.text.strip()

                scraped_data_list.append({
                    'Nama_Kos': nama_kos_text,
                    'Fasilitas': fasilitas_text_cleaned,
                    'Harga': harga_text
                })
            except Exception as e_zip:
                print(f"Error saat memproses satu item dalam zip: {e_zip}")
                continue
        
        print(f"Berhasil memproses {len(scraped_data_list)} item kos.")

    except Exception as e_scrape_all:
        print(f"Error saat mengambil semua data setelah pagination: {e_scrape_all}")


except Exception as e_main:
    print(f"Terjadi kesalahan utama dalam skrip: {e_main}")
    import traceback; traceback.print_exc()
finally:
    end_time = time.time()
    if 'start_time' in locals(): print(f"Total waktu eksekusi: {end_time - start_time:.2f} detik")
    
    if scraped_data_list:
        print(f"\nTotal data yang berhasil di-scrape: {len(scraped_data_list)} item.")
        df = pd.DataFrame(scraped_data_list)
        print("\nContoh Data (5 baris pertama):")
        print(df.head())
        try:
            csv_filename = 'hasil_scrapping_mamikos.csv'
            df.to_csv(csv_filename, index=False)
            print(f"\nData berhasil disimpan ke {csv_filename}")
        except Exception as e_csv:
            print(f"\nGagal menyimpan data ke CSV: {e_csv}")
    else:
        print("\nTidak ada data yang berhasil di-scrape untuk disimpan.")

    input("Tekan Enter untuk menutup browser...")
    driver.quit()
    print("Selesai. Browser telah ditutup.")

