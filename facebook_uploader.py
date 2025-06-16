#!/usr/bin/env python3
"""
Facebook Uploader - Status (Text/Media) dan Reels
Mendukung cookies JSON untuk auto-login dan selector yang spesifik
"""

import os
import sys
import json
import time
import platform
from pathlib import Path
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from colorama import init, Fore, Style, Back
import argparse

# Initialize colorama untuk Windows compatibility
init(autoreset=True)

class FacebookUploader:
    def __init__(self, headless: bool = False, debug: bool = False):
        """
        Initialize Facebook Uploader
        
        Args:
            headless: Jalankan browser dalam mode headless
            debug: Enable debug logging
        """
        self.headless = headless
        self.debug = debug
        self.driver = None
        self.wait = None
        
        # Setup paths - menggunakan folder cookies dengan file JSON
        self.base_dir = Path(__file__).parent
        self.cookies_dir = self.base_dir / "cookies"
        self.cookies_dir.mkdir(exist_ok=True)
        self.cookies_path = self.cookies_dir / "facebook_cookies.json"
        self.screenshots_dir = self.base_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Facebook URLs
        self.facebook_url = "https://www.facebook.com"
        self.reels_create_url = "https://www.facebook.com/reels/create/?surface=PROFILE_PLUS"
        self.login_url = "https://www.facebook.com/login"
        
        # Selectors untuk Facebook Status
        self.status_selectors = {
            'status_input': [
                # Selector baru yang diberikan user (PRIMARY)
                "#mount_0_0_aw > div > div:nth-child(1) > div > div:nth-child(5) > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div.x1uvtmcs.x4k7w5x.x1h91t0o.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1n2onr6.x1qrby5j.x1jfb8zj > div > div > div > form > div > div.x9f619.x1ja2u2z.x1k90msu.x6o7n8i.x1qfuztq.x1o0tod.x10l6tqk.x13vifvy.x1hc1fzr.x71s49j > div > div > div > div.xb57i2i.x1q594ok.x5lxg6s.x6ikm8r.x1ja2u2z.x1pq812k.x1rohswg.xfk6m8.x1yqm8si.xjx87ck.xx8ngbg.xwo3gff.x1n2onr6.x1oyok0e.x1odjw0f.x1e4zzel.x78zum5.xdt5ytf.x1iyjqo2 > div.x78zum5.xdt5ytf.x1iyjqo2.x1n2onr6 > div.x1ed109x.x1iyjqo2.x5yr21d.x1n2onr6.xh8yej3 > div.x9f619.x1iyjqo2.xg7h5cd.xf7dkkf.x1n2onr6.xh8yej3.x1ja2u2z.xjfo4ez > div > div > div.xzsf02u.x1a2a7pz.x1n2onr6.x14wi4xw.x9f619.x1lliihq.x5yr21d.xh8yej3.notranslate > p",
                # Fallback selectors
                "div[contenteditable='true'][data-text*='mind']",
                "div[contenteditable='true'][role='textbox']",
                "div[aria-label*='What'][contenteditable='true']",
                "div[data-text*='What'][contenteditable='true']",
                "[data-testid='status-attachment-mentions-input']",
                "div[contenteditable='true']",
                ".notranslate[contenteditable='true']"
            ],
            'media_upload_input': [
                "input[type='file'][accept*='image']",
                "input[type='file'][accept*='video']",
                "input[type='file']",
                "[data-testid='media-upload-input']"
            ],
            'media_upload_status': [
                # Selector baru untuk cek status upload media
                "#mount_0_0_xy > div > div:nth-child(1) > div > div:nth-child(5) > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div.x1uvtmcs.x4k7w5x.x1h91t0o.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1n2onr6.x1qrby5j.x1jfb8zj > div > div > div > form > div > div.x9f619.x1ja2u2z.x1k90msu.x6o7n8i.x1qfuztq.x1o0tod.x10l6tqk.x13vifvy.x1hc1fzr.x71s49j > div > div > div > div.xb57i2i.x1q594ok.x5lxg6s.x6ikm8r.x1ja2u2z.x1pq812k.x1rohswg.xfk6m8.x1yqm8si.xjx87ck.xx8ngbg.xwo3gff.x1n2onr6.x1oyok0e.x1odjw0f.x1e4zzel.x78zum5.xdt5ytf.x1iyjqo2 > div.x78zum5.xdt5ytf.x1iyjqo2.x1n2onr6 > div.xexx8yu.xf159sx.x18d9i69.xmzvs34 > div > div.x1obq294.x5a5i1n.xde0f50.x15x8krk.x6ikm8r.x10wlt62.x1n2onr6.xh8yej3",
                # Fallback selectors untuk media upload status
                ".media-upload-preview",
                ".media-preview-container",
                "[data-testid='media-preview']",
                ".attachment-preview",
                "div[role='img']",
                ".media-attachment"
            ],
            'post_button': [
                "div[aria-label='Post'][role='button']",
                "div[aria-label='Posting'][role='button']",
                "[data-testid='react-composer-post-button']",
                "button[type='submit']",
                "div[role='button']:has-text('Post')"
            ]
        }
        
        # Selectors untuk Facebook Reels
        self.reels_selectors = {
            'upload_input': [
                "input[type='file'][accept*='video']",
                "input[type='file']",
                "[data-testid='reels-upload-input']"
            ],
            'next_button': [
                # English
                "div[aria-label='Next'][role='button']",
                "div[role='button']:has-text('Next')",
                # Indonesian
                "div[aria-label='Berikutnya'][role='button']",
                "div[role='button']:has-text('Berikutnya')",
                # Generic
                "[data-testid='reels-next-button']",
                "button:contains('Next')",
                "button:contains('Berikutnya')"
            ],
            'description_input': [
                "div[contenteditable='true'][aria-label*='description']",
                "div[contenteditable='true'][data-text*='description']",
                "textarea[placeholder*='description']",
                "div[contenteditable='true']"
            ],
            'publish_button': [
                # English
                "div[aria-label='Publish'][role='button']",
                "div[role='button']:has-text('Publish')",
                # Indonesian  
                "div[aria-label='Terbitkan'][role='button']",
                "div[role='button']:has-text('Terbitkan')",
                # Generic
                "[data-testid='reels-publish-button']",
                "button:contains('Publish')",
                "button:contains('Terbitkan')"
            ]
        }

    def _log(self, message: str, level: str = "INFO"):
        """Enhanced logging dengan warna - versi sederhana"""
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "DEBUG": Fore.MAGENTA
        }
        
        if level == "DEBUG" and not self.debug:
            return
            
        color = colors.get(level, Fore.WHITE)
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }
        
        icon = icons.get(level, "📝")
        print(f"{color}{icon} {message}{Style.RESET_ALL}")

    def _get_chromedriver_path(self):
        """Get ChromeDriver path dengan fallback untuk Windows"""
        try:
            # Coba download ChromeDriver terbaru
            self._log("Mendownload ChromeDriver terbaru...")
            driver_path = ChromeDriverManager().install()
            
            # Validasi file exists dan executable
            if os.path.exists(driver_path):
                # Untuk Windows, pastikan file adalah .exe
                if platform.system() == "Windows" and not driver_path.endswith('.exe'):
                    # Cari file .exe di direktori yang sama
                    driver_dir = os.path.dirname(driver_path)
                    for file in os.listdir(driver_dir):
                        if file.endswith('.exe') and 'chromedriver' in file.lower():
                            driver_path = os.path.join(driver_dir, file)
                            break
                
                self._log(f"ChromeDriver ditemukan: {driver_path}", "SUCCESS")
                return driver_path
            else:
                raise FileNotFoundError("ChromeDriver tidak ditemukan setelah download")
                
        except Exception as e:
            self._log(f"Error downloading ChromeDriver: {e}", "WARNING")
            
            # Fallback: cari ChromeDriver di PATH
            self._log("Mencari ChromeDriver di sistem PATH...")
            
            chrome_names = ['chromedriver', 'chromedriver.exe']
            for name in chrome_names:
                # Cek di PATH
                import shutil
                path = shutil.which(name)
                if path:
                    self._log(f"ChromeDriver ditemukan di PATH: {path}", "SUCCESS")
                    return path
            
            # Fallback terakhir: cek lokasi umum Windows
            if platform.system() == "Windows":
                common_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
                    r"C:\chromedriver\chromedriver.exe",
                    r"C:\tools\chromedriver.exe"
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        self._log(f"ChromeDriver ditemukan: {path}", "SUCCESS")
                        return path
            
            raise FileNotFoundError("ChromeDriver tidak ditemukan. Silakan install Chrome dan ChromeDriver.")

    def _setup_driver(self):
        """Setup Chrome WebDriver dengan konfigurasi optimal dan suppress logs"""
        self._log("Menyiapkan browser untuk Facebook...")
        
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1280,800")
        
        # Additional Chrome options
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disable-plugins-discovery')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-geolocation')
        chrome_options.add_argument('--disable-media-stream')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Suppress Chrome logs dan error messages
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-gpu-logging")
        chrome_options.add_argument("--disable-extensions-file-access-check")
        chrome_options.add_argument("--disable-extensions-http-throttling")
        chrome_options.add_argument("--disable-extensions-except")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--safebrowsing-disable-auto-update")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--disable-domain-reliability")
        
        # Suppress network errors
        chrome_options.add_argument("--disable-webrtc")
        chrome_options.add_argument("--disable-webrtc-multiple-routes")
        chrome_options.add_argument("--disable-webrtc-hw-decoding")
        chrome_options.add_argument("--disable-webrtc-hw-encoding")
        chrome_options.add_argument("--disable-webrtc-encryption")
        chrome_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
        
        # Anti-detection options
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        
        if self.headless:
            self._log("Mode headless diaktifkan")
        
        try:
            # Get ChromeDriver path dengan error handling
            driver_path = self._get_chromedriver_path()
            
            # Setup ChromeDriver dengan log suppression
            service = Service(
                driver_path,
                log_path=os.devnull,
                service_args=['--silent']
            )
            
            # Suppress Selenium logs
            os.environ['WDM_LOG_LEVEL'] = '0'
            os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Anti-detection script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Setup wait
            self.wait = WebDriverWait(self.driver, 30)
            
            self._log("Browser siap digunakan", "SUCCESS")
            
        except Exception as e:
            self._log(f"Gagal menyiapkan browser: {str(e)}", "ERROR")
            
            # Tambahan info untuk troubleshooting
            if "WinError 193" in str(e):
                self._log("Error Windows detected. Troubleshooting tips:", "INFO")
                self._log("1. Pastikan Google Chrome terinstall", "INFO")
                self._log("2. Update Chrome ke versi terbaru", "INFO")
                self._log("3. Restart komputer jika perlu", "INFO")
                self._log("4. Coba jalankan sebagai Administrator", "INFO")
            
            raise

    def _find_element_by_selectors(self, selectors: list, timeout: int = 10, visible: bool = True) -> Optional[Any]:
        """Mencari elemen menggunakan multiple selectors"""
        for i, selector in enumerate(selectors):
            try:
                if visible:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                if i == 0:
                    self._log("Elemen ditemukan", "SUCCESS")
                else:
                    self._log(f"Elemen ditemukan (alternatif {i+1})", "SUCCESS")
                return element
                
            except TimeoutException:
                continue
                
        return None

    def check_media_upload_status(self, timeout: int = 30) -> bool:
        """
        Cek apakah media sudah berhasil diupload menggunakan selector baru
        
        Args:
            timeout: Timeout dalam detik untuk menunggu upload selesai
            
        Returns:
            True jika media berhasil diupload, False jika tidak
        """
        self._log("Mengecek status upload media...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Cek menggunakan selector baru yang diberikan user
            media_status_element = self._find_element_by_selectors(
                self.status_selectors['media_upload_status'], 
                timeout=2, 
                visible=False
            )
            
            if media_status_element:
                # Cek apakah elemen terlihat dan memiliki konten
                if media_status_element.is_displayed():
                    self._log("Media berhasil diupload dan terdeteksi!", "SUCCESS")
                    return True
            
            # Tunggu sebentar sebelum cek lagi
            time.sleep(1)
        
        self._log("Timeout menunggu konfirmasi upload media", "WARNING")
        return False

    def load_cookies(self) -> bool:
        """Load cookies dari file JSON"""
        if not self.cookies_path.exists():
            self._log("File cookies tidak ditemukan", "WARNING")
            return False
            
        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # Pastikan cookies_data adalah list
            if isinstance(cookies_data, dict):
                cookies = cookies_data.get('cookies', [])
            else:
                cookies = cookies_data
            
            if not cookies:
                self._log("File cookies kosong", "WARNING")
                return False
            
            # Navigate ke Facebook dulu sebelum set cookies
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            
            # Add cookies
            cookies_added = 0
            for cookie in cookies:
                try:
                    # Pastikan cookie memiliki format yang benar
                    if 'name' in cookie and 'value' in cookie:
                        # Hapus keys yang tidak diperlukan untuk Selenium
                        clean_cookie = {
                            'name': cookie['name'],
                            'value': cookie['value'],
                            'domain': cookie.get('domain', '.facebook.com'),
                            'path': cookie.get('path', '/'),
                        }
                        
                        # Tambahkan expiry jika ada
                        if 'expiry' in cookie:
                            clean_cookie['expiry'] = int(cookie['expiry'])
                        elif 'expires' in cookie:
                            clean_cookie['expiry'] = int(cookie['expires'])
                        
                        # Tambahkan secure dan httpOnly jika ada
                        if 'secure' in cookie:
                            clean_cookie['secure'] = cookie['secure']
                        if 'httpOnly' in cookie:
                            clean_cookie['httpOnly'] = cookie['httpOnly']
                        
                        self.driver.add_cookie(clean_cookie)
                        cookies_added += 1
                        
                except Exception as e:
                    if self.debug:
                        self._log(f"Gagal menambahkan cookie {cookie.get('name', 'unknown')}: {e}", "DEBUG")
            
            self._log(f"Cookies dimuat: {cookies_added}/{len(cookies)}", "SUCCESS")
            return cookies_added > 0
            
        except Exception as e:
            self._log(f"Gagal memuat cookies: {str(e)}", "ERROR")
            return False

    def save_cookies(self):
        """Simpan cookies ke file JSON"""
        try:
            cookies = self.driver.get_cookies()
            
            # Format cookies untuk JSON
            cookies_data = {
                "timestamp": int(time.time()),
                "cookies": cookies
            }
            
            with open(self.cookies_path, 'w', encoding='utf-8') as f:
                json.dump(cookies_data, f, indent=2, ensure_ascii=False)
            
            self._log(f"Cookies disimpan: {len(cookies)} item", "SUCCESS")
            
        except Exception as e:
            self._log(f"Gagal menyimpan cookies: {str(e)}", "ERROR")

    def clear_cookies(self):
        """Hapus file cookies"""
        try:
            if self.cookies_path.exists():
                self.cookies_path.unlink()
                self._log("Cookies berhasil dihapus", "SUCCESS")
            else:
                self._log("Tidak ada cookies untuk dihapus", "WARNING")
        except Exception as e:
            self._log(f"Gagal menghapus cookies: {str(e)}", "ERROR")

    def check_login_required(self) -> bool:
        """Cek apakah perlu login"""
        current_url = self.driver.current_url
        return "login" in current_url or "checkpoint" in current_url

    def wait_for_login(self, timeout: int = 180):
        """Tunggu user login manual"""
        self._log("Silakan login secara manual di browser...", "WARNING")
        self._log(f"Menunggu login selesai (timeout {timeout} detik)...", "INFO")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            # Cek apakah sudah tidak di halaman login
            if not ("login" in current_url or "checkpoint" in current_url):
                self._log("Login berhasil!", "SUCCESS")
                self.save_cookies()  # Simpan cookies setelah login
                return True
            
            time.sleep(2)
        
        raise TimeoutException("Timeout menunggu login")

    def upload_status(self, status_text: str = "", media_path: str = "") -> Dict[str, Any]:
        """
        Upload status ke Facebook dengan dukungan text dan media
        
        Args:
            status_text: Text untuk status
            media_path: Path ke file media (video/gambar)
            
        Returns:
            Dict dengan status upload
        """
        try:
            # Validasi input
            if not status_text.strip() and not media_path:
                raise ValueError("Minimal status text atau media diperlukan")
            
            if media_path and not os.path.exists(media_path):
                raise FileNotFoundError(f"File media tidak ditemukan: {media_path}")
            
            # Setup driver
            self._setup_driver()
            
            # Load cookies
            cookies_loaded = self.load_cookies()
            
            # Navigate ke Facebook
            self._log("Navigasi ke Facebook...")
            self.driver.get(self.facebook_url)
            time.sleep(3)
            
            # Cek apakah perlu login
            if self.check_login_required():
                if cookies_loaded:
                    self._log("Cookies dimuat tapi masih perlu login, refresh halaman...", "WARNING")
                    self.driver.refresh()
                    time.sleep(3)
                
                if self.check_login_required():
                    self.wait_for_login()
                    # Navigate ulang ke Facebook setelah login
                    self.driver.get(self.facebook_url)
                    time.sleep(3)
            
            # Cari input status menggunakan selector baru
            if status_text.strip():
                self._log(f"Memposting status: {status_text[:50]}{'...' if len(status_text) > 50 else ''}")
                
                status_input = self._find_element_by_selectors(self.status_selectors['status_input'])
                
                if not status_input:
                    raise NoSuchElementException("Tidak dapat menemukan input status")
                
                # Klik dan masukkan text
                status_input.click()
                time.sleep(1)
                
                # Clear existing content jika ada
                status_input.send_keys(Keys.CONTROL + "a")
                status_input.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)
                
                # Type status text
                status_input.send_keys(status_text)
                self._log("Status text berhasil dimasukkan", "SUCCESS")
                time.sleep(2)
            
            # Upload media jika ada
            if media_path:
                self._log(f"Mengupload media: {os.path.basename(media_path)}")
                
                # Cari input file untuk media
                media_input = self._find_element_by_selectors(self.status_selectors['media_upload_input'], visible=False)
                
                if media_input:
                    abs_path = os.path.abspath(media_path)
                    media_input.send_keys(abs_path)
                    self._log("Media berhasil dikirim ke input", "SUCCESS")
                    
                    # Tunggu dan cek status upload menggunakan selector baru
                    upload_success = self.check_media_upload_status(timeout=30)
                    
                    if upload_success:
                        self._log("Media berhasil diupload dan dikonfirmasi!", "SUCCESS")
                    else:
                        self._log("Media mungkin berhasil diupload tapi tidak dapat dikonfirmasi", "WARNING")
                    
                    time.sleep(3)  # Tunggu tambahan untuk memastikan processing selesai
                else:
                    self._log("Input media tidak ditemukan, melanjutkan tanpa media", "WARNING")
            
            # Cari dan klik tombol Post
            self._log("Mencari tombol post...")
            
            post_button = self._find_element_by_selectors(self.status_selectors['post_button'])
            
            if not post_button:
                raise NoSuchElementException("Tidak dapat menemukan tombol Post")
            
            # Klik tombol post
            post_button.click()
            self._log("Tombol post berhasil diklik!", "SUCCESS")
            time.sleep(5)
            
            # Cek apakah berhasil (kembali ke feed)
            current_url = self.driver.current_url
            if "facebook.com" in current_url and "login" not in current_url:
                self._log("Post berhasil (kembali ke feed)", "SUCCESS")
                return {
                    "success": True,
                    "message": "Status berhasil dipost",
                    "status_text": status_text,
                    "media_path": media_path
                }
            else:
                return {
                    "success": False,
                    "message": "Post mungkin berhasil tapi tidak dapat dikonfirmasi",
                    "status_text": status_text,
                    "media_path": media_path
                }
                
        except Exception as e:
            error_msg = f"Upload status gagal: {str(e)}"
            self._log(error_msg, "ERROR")
            
            # Ambil screenshot untuk debugging
            self.take_screenshot(f"facebook_status_error_{int(time.time())}.png")
            
            return {
                "success": False,
                "message": error_msg,
                "status_text": status_text,
                "media_path": media_path
            }
        
        finally:
            if self.driver:
                self._log("Menutup browser...")
                try:
                    self.driver.quit()
                except:
                    pass

    def upload_reels(self, video_path: str, description: str = "") -> Dict[str, Any]:
        """
        Upload reels ke Facebook
        
        Args:
            video_path: Path ke file video
            description: Deskripsi untuk reels
            
        Returns:
            Dict dengan status upload
        """
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"File video tidak ditemukan: {video_path}")
            
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            self._log(f"Mengupload reels: {os.path.basename(video_path)} ({file_size:.2f}MB)")
            
            # Setup driver
            self._setup_driver()
            
            # Load cookies
            cookies_loaded = self.load_cookies()
            
            # Navigate ke Facebook Reels Create
            self._log("Navigasi ke Facebook Reels Create...")
            self.driver.get(self.reels_create_url)
            time.sleep(3)
            
            # Cek apakah perlu login
            if self.check_login_required():
                if cookies_loaded:
                    self._log("Cookies dimuat tapi masih perlu login, refresh halaman...", "WARNING")
                    self.driver.refresh()
                    time.sleep(3)
                
                if self.check_login_required():
                    self.wait_for_login()
                    # Navigate ulang ke reels create setelah login
                    self.driver.get(self.reels_create_url)
                    time.sleep(3)
            
            # Upload video
            self._log("Memulai upload video reels...")
            
            upload_input = self._find_element_by_selectors(self.reels_selectors['upload_input'], visible=False)
            
            if not upload_input:
                raise NoSuchElementException("Tidak dapat menemukan input upload")
            
            # Upload file
            abs_path = os.path.abspath(video_path)
            self._log("Input upload ditemukan. Mengirim file...")
            upload_input.send_keys(abs_path)
            self._log("File video berhasil dikirim ke input.", "SUCCESS")
            
            # Tunggu processing dan navigasi
            time.sleep(10)
            
            # Klik Next button (bisa ada beberapa step)
            next_buttons_clicked = 0
            max_next_clicks = 3
            
            for i in range(max_next_clicks):
                try:
                    self._log(f"Mencari tombol 'Next' (step {i+1})...")
                    
                    # Cari tombol Next dengan berbagai selector
                    next_button = None
                    
                    # Coba cari berdasarkan text content
                    buttons = self.driver.find_elements(By.TAG_NAME, "div")
                    for button in buttons:
                        if button.get_attribute("role") == "button":
                            text = button.text.lower()
                            if "next" in text or "berikutnya" in text:
                                next_button = button
                                break
                    
                    if not next_button:
                        # Fallback ke selector CSS
                        next_button = self._find_element_by_selectors(self.reels_selectors['next_button'], timeout=5)
                    
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        next_buttons_clicked += 1
                        self._log(f"Tombol 'Next' berhasil diklik (index {next_buttons_clicked})!", "SUCCESS")
                        time.sleep(3)
                    else:
                        self._log(f"Tombol 'Next' tidak ditemukan atau tidak enabled pada step {i+1}", "INFO")
                        break
                        
                except Exception as e:
                    self._log(f"Error pada step {i+1}: {str(e)}", "DEBUG")
                    break
            
            # Tambahkan deskripsi jika ada
            if description.strip():
                self._log("Menambahkan deskripsi...")
                
                desc_input = self._find_element_by_selectors(self.reels_selectors['description_input'], timeout=5)
                
                if desc_input:
                    desc_input.click()
                    time.sleep(0.5)
                    desc_input.send_keys(Keys.CONTROL + "a")
                    desc_input.send_keys(Keys.BACKSPACE)
                    desc_input.send_keys(description)
                    self._log("Deskripsi berhasil diisi", "SUCCESS")
                else:
                    self._log("Input deskripsi tidak ditemukan", "WARNING")
            
            # Klik Publish button
            self._log("Mencari tombol 'Publish'...")
            
            publish_button = None
            
            # Coba cari berdasarkan text content
            buttons = self.driver.find_elements(By.TAG_NAME, "div")
            for button in buttons:
                if button.get_attribute("role") == "button":
                    text = button.text.lower()
                    if "publish" in text or "terbitkan" in text:
                        publish_button = button
                        break
            
            if not publish_button:
                # Fallback ke selector CSS
                publish_button = self._find_element_by_selectors(self.reels_selectors['publish_button'], timeout=5)
            
            if not publish_button:
                raise NoSuchElementException("Tidak dapat menemukan tombol Publish")
            
            # Klik publish
            publish_button.click()
            publish_buttons_clicked = 1
            self._log(f"Tombol 'Publish' berhasil diklik (index {publish_buttons_clicked})!", "SUCCESS")
            time.sleep(5)
            
            self._log("Upload video reels berhasil!", "SUCCESS")
            
            return {
                "success": True,
                "message": "Reels berhasil diupload",
                "video_path": video_path,
                "description": description
            }
                
        except Exception as e:
            error_msg = f"Upload reels gagal: {str(e)}"
            self._log(error_msg, "ERROR")
            
            # Ambil screenshot untuk debugging
            self.take_screenshot(f"facebook_reels_error_{int(time.time())}.png")
            
            return {
                "success": False,
                "message": error_msg,
                "video_path": video_path,
                "description": description
            }
        
        finally:
            if self.driver:
                self._log("Menutup browser...")
                try:
                    self.driver.quit()
                except:
                    pass

    def take_screenshot(self, filename: str = None):
        """Ambil screenshot untuk debugging"""
        if not filename:
            filename = f"facebook_screenshot_{int(time.time())}.png"
        
        screenshot_path = self.screenshots_dir / filename
        
        try:
            if self.driver:
                self.driver.save_screenshot(str(screenshot_path))
                self._log(f"Screenshot disimpan: {screenshot_path.name}", "INFO")
                return str(screenshot_path)
            else:
                self._log("Driver tidak tersedia untuk screenshot", "WARNING")
                return None
        except Exception as e:
            self._log(f"Gagal menyimpan screenshot: {str(e)}", "WARNING")
            return None

    def check_cookies_status(self):
        """Cek status cookies"""
        if not self.cookies_path.exists():
            self._log("File cookies tidak ditemukan", "WARNING")
            return {"exists": False, "count": 0}
        
        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # Pastikan cookies_data adalah dict dengan struktur yang benar
            if isinstance(cookies_data, dict):
                cookies = cookies_data.get('cookies', [])
                timestamp = cookies_data.get('timestamp', 0)
            else:
                cookies = cookies_data if isinstance(cookies_data, list) else []
                timestamp = 0
            
            # Cek cookies yang expired
            current_time = time.time()
            valid_cookies = []
            expired_cookies = []
            
            for cookie in cookies:
                if 'expiry' in cookie:
                    if cookie['expiry'] > current_time:
                        valid_cookies.append(cookie)
                    else:
                        expired_cookies.append(cookie)
                elif 'expires' in cookie:
                    if cookie['expires'] > current_time:
                        valid_cookies.append(cookie)
                    else:
                        expired_cookies.append(cookie)
                else:
                    valid_cookies.append(cookie)  # Session cookies
            
            self._log(f"Total cookies: {len(cookies)}", "INFO")
            self._log(f"Valid cookies: {len(valid_cookies)}", "SUCCESS")
            
            if expired_cookies:
                self._log(f"Expired cookies: {len(expired_cookies)}", "WARNING")
            
            if timestamp:
                import datetime
                saved_time = datetime.datetime.fromtimestamp(timestamp)
                self._log(f"Cookies disimpan: {saved_time.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
            
            return {
                "exists": True,
                "total": len(cookies),
                "valid": len(valid_cookies),
                "expired": len(expired_cookies),
                "timestamp": timestamp
            }
            
        except Exception as e:
            self._log(f"Error membaca cookies: {str(e)}", "ERROR")
            return {"exists": True, "error": str(e)}


def main():
    """Main function untuk CLI"""
    parser = argparse.ArgumentParser(description="Facebook Uploader (Status & Reels)")
    parser.add_argument("--type", "-t", choices=['status', 'reels'], help="Jenis upload (status/reels)")
    parser.add_argument("--status", "-s", help="Status text untuk Facebook")
    parser.add_argument("--media", "-m", help="Path ke file media (video/gambar) untuk status")
    parser.add_argument("--video", "-v", help="Path ke file video untuk reels")
    parser.add_argument("--description", "-d", default="", help="Deskripsi untuk reels")
    parser.add_argument("--headless", action="store_true", help="Jalankan dalam mode headless")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--clear-cookies", action="store_true", help="Hapus cookies")
    parser.add_argument("--check-cookies", action="store_true", help="Cek status cookies")
    
    args = parser.parse_args()
    
    uploader = FacebookUploader(headless=args.headless, debug=args.debug)
    
    # Handle different actions
    if args.clear_cookies:
        uploader.clear_cookies()
        return
    
    if args.check_cookies:
        uploader.check_cookies_status()
        return
    
    if args.type:
        if args.type == 'status':
            if not args.status and not args.media:
                print(f"{Fore.RED}❌ Status text atau media diperlukan untuk Facebook status")
                sys.exit(1)
            
            if args.media and not os.path.exists(args.media):
                print(f"{Fore.RED}❌ File media tidak ditemukan: {args.media}")
                sys.exit(1)
            
            result = uploader.upload_status(args.status or "", args.media or "")
            
            if result["success"]:
                print(f"{Fore.GREEN}🎉 Facebook status berhasil!")
            else:
                print(f"{Fore.RED}❌ Facebook status gagal: {result['message']}")
                sys.exit(1)
        
        elif args.type == 'reels':
            if not args.video:
                print(f"{Fore.RED}❌ Video path diperlukan untuk Facebook Reels")
                sys.exit(1)
            if not os.path.exists(args.video):
                print(f"{Fore.RED}❌ File video tidak ditemukan: {args.video}")
                sys.exit(1)
            
            result = uploader.upload_reels(args.video, args.description)
            
            if result["success"]:
                print(f"{Fore.GREEN}🎉 Facebook Reels berhasil!")
            else:
                print(f"{Fore.RED}❌ Facebook Reels gagal: {result['message']}")
                sys.exit(1)
        
        return
    
    # Interactive mode
    print(f"{Fore.BLUE}📘 Facebook Uploader")
    print("=" * 40)
    print(f"{Fore.YELLOW}🔥 Status (Text/Media) + Reels")
    print()
    
    while True:
        print(f"\n{Fore.YELLOW}Pilih jenis upload:")
        print("1. 📝 Status Facebook (Text/Media)")
        print("2. 🎬 Reels Facebook (Video)")
        print("3. 🍪 Cek status cookies")
        print("4. 🗑️ Hapus cookies")
        print("5. ❌ Keluar")
        
        choice = input(f"\n{Fore.WHITE}Pilihan (1-5): ").strip()
        
        if choice == "1":
            print(f"\n{Fore.YELLOW}📝 Facebook Status Options:")
            print("1. Text Only")
            print("2. Text + Media")
            print("3. Media Only")
            
            status_choice = input(f"{Fore.WHITE}Pilihan (1-3): ").strip()
            
            status_text = ""
            media_path = ""
            
            if status_choice in ["1", "2"]:
                status_text = input(f"{Fore.CYAN}Status Facebook: ").strip()
                if not status_text and status_choice == "1":
                    print(f"{Fore.RED}❌ Status text tidak boleh kosong untuk text only!")
                    continue
            
            if status_choice in ["2", "3"]:
                media_path = input(f"{Fore.CYAN}Path ke file media (video/gambar): ").strip()
                if not os.path.exists(media_path):
                    print(f"{Fore.RED}❌ File media tidak ditemukan!")
                    continue
            
            if not status_text and not media_path:
                print(f"{Fore.RED}❌ Minimal status text atau media diperlukan!")
                continue
            
            result = uploader.upload_status(status_text, media_path)
            
            if result["success"]:
                print(f"{Fore.GREEN}🎉 Facebook status berhasil!")
            else:
                print(f"{Fore.RED}❌ Facebook status gagal: {result['message']}")
        
        elif choice == "2":
            video_path = input(f"{Fore.CYAN}Path ke file video: ").strip()
            if not os.path.exists(video_path):
                print(f"{Fore.RED}❌ File tidak ditemukan!")
                continue
            
            description = input(f"{Fore.CYAN}Deskripsi Facebook Reels (opsional): ").strip()
            
            result = uploader.upload_reels(video_path, description)
            
            if result["success"]:
                print(f"{Fore.GREEN}🎉 Facebook Reels berhasil!")
            else:
                print(f"{Fore.RED}❌ Facebook Reels gagal: {result['message']}")
        
        elif choice == "3":
            uploader.check_cookies_status()
        
        elif choice == "4":
            confirm = input(f"{Fore.YELLOW}Yakin ingin menghapus cookies? (y/N): ").strip().lower()
            if confirm == 'y':
                uploader.clear_cookies()
        
        elif choice == "5":
            print(f"{Fore.YELLOW}👋 Sampai jumpa!")
            break
        
        else:
            print(f"{Fore.RED}❌ Pilihan tidak valid!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Program dihentikan oleh user")
    except Exception as e:
        print(f"{Fore.RED}💥 Error fatal: {str(e)}")
        sys.exit(1)