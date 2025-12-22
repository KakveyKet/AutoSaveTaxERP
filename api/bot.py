import time
import os
import threading
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.conf import settings
from django.core.files import File
# Added ActionChains import as it is needed for the tab/esc sequence
from selenium.webdriver.common.action_chains import ActionChains
from asgiref.sync import async_to_sync
from server.sio import sio

class AutoDownloadBot:
    def __init__(self, order_import_instance, config=None):
        self.order = order_import_instance
        self.items = self.order.parsed_data or []
        
        self.config = config or {}
        # Default config or fallback to hardcoded credentials
        self.target_url = self.config.get('target_url', "https://ax.d365ffo.onprem.libgroup.com/namespaces/AXSF/?cmp=TAC&mi=DefaultDashboard")
        self.username = self.config.get('username', "tcexp01@dc.libgroup.com")
        self.password = self.config.get('password', "Tc&Exp0#1385!")
        
        self.start_index = int(self.config.get('start_index', 0))
        self.limit = self.config.get('limit') 

        # Set to True if you don't want to see the browser window
        self.headless = False 

        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("detach", True)
        
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-ssl-errors')
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if self.headless:
            self.chrome_options.add_argument("--headless")

        # Setup Download Directory (Django Media Temp)
        # We save here first to ensure we capture the file from Chrome
        self.download_dir = os.path.join(settings.MEDIA_ROOT, 'temp', str(self.order.id))
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        self.chrome_options.add_experimental_option("prefs", prefs)

    def _emit(self, event_type, payload):
        try:
            message = {'type': event_type, 'order_id': self.order.id, **payload}
            async_to_sync(sio.emit)('bot_update', message)
        except Exception as e:
            print(f"Socket Emit Error: {e}")

    def run(self):
        """Starts the bot process in a separate thread so it doesn't block Django."""
        t = threading.Thread(target=self._process_in_background)
        t.daemon = False 
        t.start()

    def _update_item_status(self, index, status):
        """Updates the status of a specific invoice item in the database JSON."""
        if self.items and index < len(self.items):
            self.items[index]['status'] = status
            self.order.parsed_data = self.items
            self.order.save()
            self._emit('progress', {'index': index, 'status': status, 'invoice': self.items[index].get('invoice_number')})

    def _check_stop_signal(self):
        self.order.refresh_from_db()
        if self.order.bot_status == 'stopping':
            self.order.bot_status = 'cancelled'
            self.order.bot_message = "Stopped by user."
            self.order.save()
            self._emit('status_change', {'status': 'cancelled', 'message': 'Stopped by user.'})
            return True
        return False

    def _rename_latest_download(self, new_name):
        """Waits for a file to appear in the download folder and renames it to match the invoice number."""
        try:
            # Wait loop for file to appear (Fast polling)
            retries = 20 # Wait up to 10 seconds (20 * 0.5s)
            while retries > 0:
                if self._check_stop_signal(): return
                files = [os.path.join(self.download_dir, f) for f in os.listdir(self.download_dir) if os.path.isfile(os.path.join(self.download_dir, f))]
                # Ignore temp files, the archive itself, and partial downloads
                valid_files = [f for f in files if "archive.zip" not in f and not f.endswith('.crdownload') and not f.endswith('.tmp')]
                
                if valid_files:
                    # Get the most recently created file
                    latest_file = max(valid_files, key=os.path.getctime)
                    
                    # If it's already named correctly, skip
                    if os.path.basename(latest_file).startswith(new_name):
                        return 

                    extension = os.path.splitext(latest_file)[1]
                    new_path = os.path.join(self.download_dir, f"{new_name}{extension}")
                    
                    # Handle duplicates if the file already exists
                    if os.path.exists(new_path):
                        timestamp = int(time.time())
                        new_path = os.path.join(self.download_dir, f"{new_name}_{timestamp}{extension}")
                        
                    os.rename(latest_file, new_path)
                    print(f"Captured and renamed to: {os.path.basename(new_path)}")
                    return
                
                time.sleep(0.5)
                retries -= 1
        except Exception as e: 
            print(f"Error renaming file: {e}")

    def _zip_files(self):
        """Compresses all downloaded files into a single ZIP archive."""
        zip_filename = os.path.join(self.download_dir, 'archive.zip')
        files = os.listdir(self.download_dir)
        
        # Ensure we don't zip empty folders or just re-zip an existing zip
        has_files = any(f != 'archive.zip' and not f.endswith('.crdownload') for f in files)
        if not has_files: return None

        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, dirs, files in os.walk(self.download_dir):
                for file in files:
                    if file != 'archive.zip':
                        zipf.write(os.path.join(root, file), file)
        return zip_filename

    def _process_in_background(self):
        """Main logic loop: Opens browser, logs in, iterates invoices, downloads, and saves."""
        driver = None
        try:
            self.order.refresh_from_db()
            self.order.bot_status = 'running'
            self.order.bot_message = "Initializing Browser..."
            self.order.save()
            self._emit('status_change', {'status': 'running', 'message': 'Initializing Browser...'})

            print("Starting Browser...")
            driver_path = ChromeDriverManager().install()
            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            print(f"Navigating to {self.target_url}")
            driver.get(self.target_url)
            wait = WebDriverWait(driver, 60) 
            short_wait = WebDriverWait(driver, 5)

            # --- Fast Wait Helper ---
            def wait_for_loading():
                try:
                    driver.implicitly_wait(0.1) 
                    overlays = driver.find_elements(By.CSS_SELECTOR, ".modalBackground, .sys-loading-overlay")
                    if overlays and any(o.is_displayed() for o in overlays):
                        driver.implicitly_wait(5)
                        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modalBackground")))
                        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".sys-loading-overlay")))
                    driver.implicitly_wait(5) 
                except: pass

            # --- Robust Input Helper ---
            def fill_input_robust(element, text):
                try: element.click()
                except: driver.execute_script("arguments[0].click();", element)
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
                element.send_keys(text)

            # --- 1. LOGIN ---
            if self._check_stop_signal(): 
                if driver: driver.quit()
                return

            try:
                print("Logging in...")
                email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email' or @name='loginfmt']")))
                fill_input_robust(email_field, self.username)
                email_field.send_keys(Keys.ENTER)
                
                password_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password' or @name='passwd']")))
                password_field.send_keys(self.password)
                time.sleep(0.5) 
                driver.switch_to.active_element.send_keys(Keys.ENTER)
                
                try:
                    short_wait.until(EC.presence_of_element_located((By.ID, "idSIButton9")))
                    driver.switch_to.active_element.send_keys(Keys.ENTER)
                except: pass
                
                WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                self._emit('log', {'message': 'Login Successful'})
                print("Login Successful!")
            except Exception as e:
                print(f"Login Failed: {e}")
                raise e

            # --- AUTO CLOSE POPUP (ADDED HERE) ---
            try:
                print("Checking for startup popups...")
                time.sleep(5) 

                # 1. Reset Focus
                try:
                    driver.find_element(By.TAG_NAME, "body").click()
                except: pass

                # 2. Try ESCAPE
                try:
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    print("Sent ESC key.")
                    time.sleep(1)
                except: pass

                # 3. Try Clicking Close Buttons (X or text)
                close_selectors = [
                    "//button[@title='Close']", 
                    "//button[@aria-label='Close']",
                    "//button[span[text()='Close']]",
                    "//div[@role='button'][@title='Close']",
                    "//*[@data-icon-name='Cancel']",
                    "//*[@data-icon-name='ChromeClose']" 
                ]
                for xpath in close_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        for btn in elements:
                            if btn.is_displayed():
                                print(f"Found and clicking: {xpath}")
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(1)
                    except: continue

            except Exception as e:
                print(f"Popup check finished: {e}")
            # -------------------------------------

            if self._check_stop_signal(): 
                if driver: driver.quit()
                return

            # --- 2. NAVIGATION ---
            wait_for_loading()
            time.sleep(2) 
            try:
                self._emit('log', {'message': 'Navigating...'})
                fav_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@title, 'Favorites') or contains(@aria-label, 'Favorites')]")))
                fav_btn.click()
                export_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Export Invoice (Bulk)')]")))
                export_link.click()
            except Exception as e: 
                print("Navigation failed, trying direct URL or skipping...")
            
            wait_for_loading()
            print("Navigated. Starting Loop...")

            # --- 3. INVOICE LOOP ---
            processed_count = 0
            
            def find_invoice_input():
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[role='textbox']")
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled(): return inp
                raise Exception("No input found")

            # Apply limits if configured
            total_items = len(self.items)
            end_index = min(self.start_index + (int(self.limit) if self.limit else total_items), total_items)
            
            for i in range(self.start_index, end_index):
                if self._check_stop_signal(): 
                    if driver: driver.quit()
                    return 

                item = self.items[i]
                invoice = item.get('invoice_number')
                
                # Check if item is already done to avoid reprocessing
                if item.get('status') == 'completed': continue

                for attempt in range(3): # Retry logic
                    if self._check_stop_signal(): 
                        if driver: driver.quit()
                        return
                    try:
                        self._update_item_status(i, 'processing')
                        print(f"[{i+1}] Processing: {invoice}")
                        wait_for_loading()

                        # --- INTERACTION LOGIC (Simplified) ---
                        # 1. Open Report
                        print("Clicking Report Dropdown...")
                        try:
                            target_report_text = "Report"
                            report_link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{target_report_text}')]")))
                            report_link.click()
                            time.sleep(0.5)
                            po_form_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Purchase Order Form')]")))
                            po_form_link.click()
                        except Exception as nav_err:
                            print(f"Menu error: {nav_err}")
                            time.sleep(1)
                            report_link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{target_report_text}')]")))
                            report_link.click()
                            time.sleep(0.5)
                            po_form_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Purchase Order Form')]")))
                            po_form_link.click()

                        wait_for_loading()
                        time.sleep(2) 

                        # 2. Fill Invoice
                        input_field = wait.until(lambda d: find_invoice_input())
                        fill_input_robust(input_field, invoice)
                        
                        # 3. Click Change/Apply
                        try:
                            change_btn = driver.find_element(By.XPATH, "//*[text()='Change' or text()='Apply' or text()='OK']")
                            change_btn.click()
                        except:
                            input_field.send_keys(Keys.ENTER)

                        wait_for_loading()
                        time.sleep(1)

                        # 4. Handle Dialog & Download
                        try:
                            name_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//label[contains(text(), 'Name')]/following::input[1]")))
                            fill_input_robust(name_input, f"{invoice}.xlsx")
                            
                            try:
                                dialog_ok_btn = driver.find_element(By.XPATH, "//button[contains(@name, 'OK') or text()='OK']")
                                dialog_ok_btn.click()
                            except:
                                name_input.send_keys(Keys.ENTER)

                            wait_for_loading()
                            time.sleep(1)
                        except Exception as dialog_err:
                            print(f"Dialog step error: {dialog_err}")

                        # 5. Final Download Trigger
                        try:
                            main_ok_btn = short_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='OK']] | //button[text()='OK']")))
                            driver.execute_script("arguments[0].click();", main_ok_btn)
                            
                            # Capture and Rename File
                            self._rename_latest_download(invoice)
                        except Exception as err:
                            print(f"Download trigger failed: {err}")
                            try: driver.switch_to.active_element.send_keys(Keys.ENTER)
                            except: pass

                        wait_for_loading()
                        time.sleep(2) 

                        # 6. Close Success Popup
                        try:
                            driver.switch_to.active_element.send_keys(Keys.ENTER)
                        except: pass
                        
                        wait_for_loading()
                        time.sleep(2) 

                        self._update_item_status(i, 'completed')
                        processed_count += 1
                        break 
                    except Exception as e:
                        print(f"Failed Invoice {invoice}: {e}")
                        if attempt == 2: self._update_item_status(i, 'failed')
                        else: time.sleep(1)

            # --- 4. FINISH & SAVE ---
            print("Zipping files...")
            zip_path = self._zip_files()
            
            target_zip_name = f"Invoices_{self.order.id}.zip"
            try:
                if self.order.file and hasattr(self.order.file, 'name'):
                    original = os.path.basename(self.order.file.name)
                    target_zip_name = f"{os.path.splitext(original)[0]}.zip"
            except: pass

            if zip_path and os.path.exists(zip_path):
                # 1. SAVE TO DIGITALOCEAN DISK
                with open(zip_path, 'rb') as f:
                    self.order.generated_zip.save(target_zip_name, File(f))
                
                cloud_url = self.order.generated_zip.url

                # 2. ATTEMPT LOCAL COPY (Localhost Only)
                local_success = False
                if not self.headless: 
                    try:
                        local_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                        if os.path.exists(local_downloads):
                            target_path = os.path.join(local_downloads, target_zip_name)
                            shutil.copy2(zip_path, target_path)
                            local_success = True
                    except: pass

                # 3. CLEANUP TEMP
                try:
                    shutil.rmtree(self.download_dir)
                except: pass

                status_msg = "Completed."
                if local_success: status_msg += " Copied to Downloads."
                else: status_msg += " Saved to Server/Cloud."

                self.order.bot_status = 'completed'
                self.order.bot_message = status_msg
                
                self._emit('status_change', {
                    'status': 'completed', 
                    'message': status_msg, 
                    'file_url': cloud_url 
                })
            else:
                self.order.bot_status = 'completed'
                self.order.bot_message = "Finished, no files found."
                self._emit('status_change', {'status': 'completed', 'message': "Finished, no files."})
            
            self.order.save()
            
            # Optional: Close browser when done
            if driver: driver.quit()

        except Exception as e:
            print(f"CRITICAL BOT ERROR: {e}")
            self.order.bot_status = 'failed'
            self.order.bot_message = f"Error: {str(e)}"
            self.order.save()
            self._emit('status_change', {'status': 'failed', 'message': f"Error: {str(e)}"})
            if driver: driver.quit()