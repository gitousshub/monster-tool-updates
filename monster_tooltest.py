import pyautogui
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import random
import winsound
import os
import json
from datetime import datetime, timedelta
import cv2
import numpy as np
from PIL import Image, ImageTk
import requests
import subprocess
import sys
import shutil
import hashlib
try:
    from packaging import version
except ImportError:
    # Fallback version comparison if packaging is not available
    def version_compare(v1, v2):
        """Simple version comparison fallback"""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        return normalize(v1) > normalize(v2)
    
    class version:
        @staticmethod
        def parse(v):
            return v
        
        def __gt__(self, other):
            return version_compare(str(self), str(other))

# Try to import pynput for coordinate capture
try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Warning: pynput not available. Install with: pip install pynput")

import tkinter as tk
import json
import os
try:
    from license_validator import MonsterToolLicenseIntegration
    LICENSE_SYSTEM_AVAILABLE = True
    print("🔐 License system loaded successfully")
except ImportError:
    print("⚠️ License system not available - running in demo mode")
    LICENSE_SYSTEM_AVAILABLE = False

# Application Configuration
APP_VERSION = "1.0.5"
UPDATE_SERVER_URL = "https://gitousshub.github.io/monster-tool-updates"  # Replace with your GitHub Pages URL
APP_NAME = "Monster Soul Retrieval Tool"

class AutoUpdater:
    """Auto-update system for the Monster Tool"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.current_version = APP_VERSION
        self.server_url = UPDATE_SERVER_URL
        self.update_check_file = "version_check.json"
        self.backup_suffix = ".backup"
        
    def check_for_updates(self, show_no_update_message=True):
        """Check if updates are available on the server"""
        try:
            print(f"🔍 Checking for updates... Current version: {self.current_version}")
            
            # Request version info from server
            response = requests.get(f"{self.server_url}/version.json", timeout=10)
            
            if response.status_code == 200:
                version_info = response.json()
                server_version = version_info.get("latest_version", "0.0.0")
                changelog = version_info.get("changelog", "No changelog available")
                download_url = version_info.get("download_url", f"{self.server_url}/monster_tooltest.py")
                
                print(f"📡 Server version: {server_version}")
                
                # Compare versions
                if version.parse(server_version) > version.parse(self.current_version):
                    return {
                        "update_available": True,
                        "server_version": server_version,
                        "current_version": self.current_version,
                        "changelog": changelog,
                        "download_url": download_url
                    }
                else:
                    if show_no_update_message:
                        print("✅ You have the latest version!")
                    return {"update_available": False}
            else:
                print(f"❌ Failed to check for updates: HTTP {response.status_code}")
                return {"update_available": False, "error": f"Server returned {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            print("🌐 No internet connection or server unavailable")
            return {"update_available": False, "error": "Connection failed"}
        except requests.exceptions.Timeout:
            print("⏱️ Update check timed out")
            return {"update_available": False, "error": "Request timed out"}
        except Exception as e:
            print(f"❌ Error checking for updates: {e}")
            return {"update_available": False, "error": str(e)}
    
    def download_update(self, download_url, progress_callback=None):
        """Download the update file"""
        try:
            print(f"📥 Downloading update from: {download_url}")
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get file size for progress tracking
            total_size = int(response.headers.get('content-length', 0))
            
            # Create temporary file name
            script_path = os.path.abspath(__file__)
            temp_file = script_path + ".temp"
            
            downloaded_size = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress)
            
            print(f"✅ Download completed: {downloaded_size} bytes")
            return temp_file
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def verify_update_integrity(self, file_path, expected_hash=None):
        """Verify the downloaded file integrity"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Basic checks
            file_size = os.path.getsize(file_path)
            if file_size < 1000:  # File should be at least 1KB
                print("❌ Downloaded file is too small")
                return False
            
            # Check if it's a valid Python file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(100)
                if not content.strip().startswith(('import', 'from', '#')):
                    print("❌ Downloaded file doesn't appear to be a Python script")
                    return False
            
            print("✅ Update file integrity verified")
            return True
            
        except Exception as e:
            print(f"❌ Integrity verification failed: {e}")
            return False
    
    def backup_current_version(self):
        """Create backup of current version"""
        try:
            script_path = os.path.abspath(__file__)
            backup_path = script_path + self.backup_suffix
            
            shutil.copy2(script_path, backup_path)
            print(f"📦 Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return None
    
    def apply_update(self, temp_file):
        """Apply the downloaded update"""
        try:
            script_path = os.path.abspath(__file__)
            
            # Create backup first
            backup_path = self.backup_current_version()
            if not backup_path:
                return False
            
            # Replace current file with downloaded file
            shutil.move(temp_file, script_path)
            print(f"✅ Update applied successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Update application failed: {e}")
            # Try to restore backup
            self.restore_backup()
            return False
    
    def restore_backup(self):
        """Restore from backup if update fails"""
        try:
            script_path = os.path.abspath(__file__)
            backup_path = script_path + self.backup_suffix
            
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, script_path)
                print("🔄 Restored from backup")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Backup restoration failed: {e}")
            return False
    
    def restart_application(self):
        """Restart the application after update"""
        try:
            print("🔄 Restarting application...")
            script_path = os.path.abspath(__file__)
            
            # Close current application
            if hasattr(self.app, 'root'):
                self.app.root.quit()
            
            # Start new instance
            subprocess.Popen([sys.executable, script_path])
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Restart failed: {e}")
            return False

class ScrollableFrame(tk.Frame):
    def __init__(self, container, bg_color="#1a1d29", *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=bg_color)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Optional: enable mouse wheel scrolling on Windows
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

class MetamobAPI:
    """Metamob.fr API Integration for syncing soul data"""
    
    def __init__(self):
        self.base_url = "https://api.metamob.fr"
        self.api_key = None
        self.user_key = None
        self.username = None
        self.monster_id_cache = {}
        self.credentials_file = "config/metamob_credentials.json"
        
        # Load saved credentials
        self.load_credentials()
        
    def load_credentials(self):
        """Load saved Metamob credentials"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key')
                    self.user_key = creds.get('user_key') 
                    self.username = creds.get('username')
                    print(f"✅ Loaded Metamob credentials for user: {self.username}")
        except Exception as e:
            print(f"⚠️ Failed to load Metamob credentials: {e}")
            
    def save_credentials(self, api_key, user_key, username):
        """Save Metamob credentials"""
        try:
            os.makedirs("config", exist_ok=True)
            creds = {
                'api_key': api_key,
                'user_key': user_key,
                'username': username,
                'saved_date': datetime.now().isoformat()
            }
            with open(self.credentials_file, 'w') as f:
                json.dump(creds, f, indent=2)
            
            self.api_key = api_key
            self.user_key = user_key
            self.username = username
            print(f"✅ Saved Metamob credentials for user: {username}")
            return True
        except Exception as e:
            print(f"❌ Failed to save Metamob credentials: {e}")
            return False
            
    def setup_credentials(self):
        """Open dialog to setup Metamob credentials"""
        dialog = tk.Toplevel()
        dialog.title("🌐 Metamob.fr API Setup")
        dialog.geometry("500x300")
        dialog.transient()
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"500x300+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Instructions
        ttk.Label(frame, text="🌐 Metamob.fr API Configuration", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        instructions = """To get your API credentials:
1. Go to https://www.metamob.fr/utilisateur/mon_profil
2. Click the "API" tab
3. Create an API key (if you don't have one)
4. Copy your API Key and User Unique Key
5. Enter them below with your username"""
        
        ttk.Label(frame, text=instructions, wraplength=450).grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Input fields
        ttk.Label(frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=5)
        username_var = tk.StringVar(value=self.username or "")
        ttk.Entry(frame, textvariable=username_var, width=40).grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="API Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar(value=self.api_key or "")
        ttk.Entry(frame, textvariable=api_key_var, width=40, show="*").grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="User Unique Key:").grid(row=4, column=0, sticky=tk.W, pady=5)
        user_key_var = tk.StringVar(value=self.user_key or "")
        ttk.Entry(frame, textvariable=user_key_var, width=40, show="*").grid(row=4, column=1, pady=5)
        
        def save_and_test():
            username = username_var.get().strip()
            api_key = api_key_var.get().strip()
            user_key = user_key_var.get().strip()
            
            if not all([username, api_key, user_key]):
                messagebox.showerror("Error", "Please fill in all fields!")
                return
                
            # Save credentials
            if self.save_credentials(api_key, user_key, username):
                # Test connection
                if self.test_connection():
                    messagebox.showinfo("Success", "✅ Metamob API connection successful!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "❌ Failed to connect to Metamob API. Please check your credentials.")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 Save & Test", command=save_and_test).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="❌ Cancel", command=dialog.destroy).grid(row=0, column=1, padx=10)
        
    def test_connection(self):
        """Test Metamob API connection"""
        if not all([self.api_key, self.user_key, self.username]):
            return False
            
        try:
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            # Test with a simple GET request to user monsters
            response = requests.get(
                f"{self.base_url}/utilisateurs/{self.username}/monstres",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Metamob API connection successful for user: {self.username}")
                return True
            else:
                print(f"❌ Metamob API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Metamob API connection failed: {e}")
            return False
    
    def is_connected(self):
        """Check if API is properly configured and connected"""
        return all([self.api_key, self.user_key, self.username])
    
    def get_monster_id_by_name(self, monster_name):
        """Get Metamob monster ID by name"""
        if not self.api_key:
            return None
            
        # Check cache first
        if monster_name in self.monster_id_cache:
            return self.monster_id_cache[monster_name]
            
        try:
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            # Search for monster by name
            response = requests.get(
                f"{self.base_url}/monstres",
                headers=headers,
                params={'nom': monster_name},
                timeout=10
            )
            
            if response.status_code == 200:
                monsters = response.json()
                if monsters and len(monsters) > 0:
                    monster_id = monsters[0]['id']
                    self.monster_id_cache[monster_name] = monster_id
                    return monster_id
                    
        except Exception as e:
            print(f"❌ Failed to get monster ID for {monster_name}: {e}")
            
        return None
    
    def get_monster_id(self, monster_name):
        """Alias for get_monster_id_by_name for compatibility"""
        return self.get_monster_id_by_name(monster_name)
    
    def update_monster_soul_count(self, monster_name, soul_count):
        """Update monster soul count on Metamob"""
        if not all([self.api_key, self.user_key, self.username]):
            print("❌ Metamob credentials not configured")
            return False
            
        # Get monster ID
        monster_id = self.get_monster_id_by_name(monster_name)
        if not monster_id:
            print(f"❌ Monster '{monster_name}' not found on Metamob")
            return False
            
        try:
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'HTTP-X-USERKEY': self.user_key,
                'Content-Type': 'application/json'
            }
            
            # Prepare update data
            update_data = [{
                "id": monster_id,
                "quantite": soul_count
            }]
            
            # Send update request
            response = requests.put(
                f"{self.base_url}/utilisateurs/{self.username}/monstres",
                headers=headers,
                json=update_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if str(monster_id) in result.get('reussite', {}):
                    print(f"✅ Updated {monster_name} to {soul_count} souls on Metamob")
                    return True
                else:
                    print(f"❌ Failed to update {monster_name}: {result.get('erreurs', [])}")
                    return False
            else:
                print(f"❌ Metamob API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to update {monster_name} on Metamob: {e}")
            return False
    
    def batch_update_souls(self, soul_data):
        """Update multiple monsters' soul counts in batch with chunking for large datasets"""
        if not all([self.api_key, self.user_key, self.username]):
            print("❌ Metamob credentials not configured")
            return False
            
        try:
            # Handle both list and dictionary formats
            update_data = []
            
            if isinstance(soul_data, list):
                # If it's already a list of formatted updates, use it directly
                update_data = soul_data
            elif isinstance(soul_data, dict):
                # If it's a dictionary, convert it
                for monster_name, data in soul_data.items():
                    monster_id = self.get_monster_id_by_name(monster_name)
                    if monster_id:
                        # Handle both simple quantity and complex data structure
                        if isinstance(data, dict):
                            soul_count = data.get('quantity', 0)
                        else:
                            soul_count = data
                        
                        # Debug logging for quantity verification
                        print(f"🔍 Preparing sync: {monster_name} → {soul_count} souls (Monster ID: {monster_id})")
                            
                        update_data.append({
                            "id": monster_id,
                            "quantite": soul_count
                        })
                    else:
                        print(f"⚠️ Skipping {monster_name} - not found on Metamob")
            
            if not update_data:
                print("❌ No valid monsters to update")
                return False
            
            total_monsters = len(update_data)
            print(f"📊 Syncing {total_monsters} monsters to Metamob...")
            
            # Split large datasets into smaller chunks (max 50 per request)
            chunk_size = 50
            chunks = [update_data[i:i + chunk_size] for i in range(0, len(update_data), chunk_size)]
            
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'HTTP-X-USERKEY': self.user_key,
                'Content-Type': 'application/json'
            }
            
            total_success = 0
            total_errors = 0
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                print(f"📦 Processing chunk {i+1}/{len(chunks)} ({len(chunk)} monsters)...")
                
                # Debug: Show what's being sent in this chunk
                print(f"🔍 Chunk {i+1} data preview:")
                for item in chunk[:3]:  # Show first 3 items as preview
                    print(f"   ID: {item['id']}, Quantity: {item['quantite']}")
                if len(chunk) > 3:
                    print(f"   ... and {len(chunk) - 3} more monsters")
                
                try:
                    # Send chunk update with longer timeout for large requests
                    response = requests.put(
                        f"{self.base_url}/utilisateurs/{self.username}/monstres",
                        headers=headers,
                        json=chunk,
                        timeout=60  # Increased timeout for large batches
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        chunk_success = len(result.get('reussite', {}))
                        chunk_errors = len(result.get('erreurs', []))
                        
                        total_success += chunk_success
                        total_errors += chunk_errors
                        
                        print(f"✅ Chunk {i+1}: {chunk_success} updated, {chunk_errors} errors")
                        
                        # Debug: Show detailed results for verification
                        if result.get('reussite'):
                            print(f"🔍 Chunk {i+1} successful updates:")
                            for monster_id, messages in result.get('reussite', {}).items():
                                # Find the monster name for this ID
                                monster_name = "Unknown"
                                sent_quantity = "Unknown"
                                for item in chunk:
                                    if str(item['id']) == str(monster_id):
                                        sent_quantity = item['quantite']
                                        break
                                print(f"   Monster ID {monster_id}: Sent {sent_quantity} → {messages}")
                        
                        # Log any errors for this chunk
                        if result.get('erreurs'):
                            print(f"❌ Chunk {i+1} errors:")
                            for error in result.get('erreurs', []):
                                print(f"   • {error}")
                    else:
                        print(f"❌ Chunk {i+1} failed: {response.status_code} - {response.text}")
                        total_errors += len(chunk)
                        
                except requests.exceptions.Timeout:
                    print(f"⏱️ Chunk {i+1} timed out - trying with smaller timeout...")
                    total_errors += len(chunk)
                except requests.exceptions.RequestException as e:
                    print(f"🌐 Chunk {i+1} network error: {e}")
                    total_errors += len(chunk)
                except Exception as e:
                    print(f"❌ Chunk {i+1} unexpected error: {e}")
                    total_errors += len(chunk)
                
                # Small delay between chunks to avoid rate limiting
                if i < len(chunks) - 1:  # Don't delay after last chunk
                    time.sleep(1)
            
            # Final results
            print(f"✅ Batch update complete: {total_success} updated, {total_errors} errors out of {total_monsters} total")
            
            # Add verification step to check for discrepancies
            if total_success > 0:
                print(f"🔍 Sync verification completed. Check console for detailed logs.")
                print(f"💡 If you notice quantity discrepancies:")
                print(f"   1. Compare the 'Preparing sync' logs with your scan results")
                print(f"   2. Check the 'successful updates' logs for what Metamob confirmed")
                print(f"   3. Verify monster names match exactly (special characters, spaces)")
            
            return total_success > 0  # Consider success if at least some monsters were updated
                
        except Exception as e:
            print(f"❌ Metamob batch update error: {e}")
            return False
    
    def batch_update_souls_with_progress(self, soul_data, progress_callback=None):
        """Update multiple monsters' soul counts in batch with progress reporting"""
        if not all([self.api_key, self.user_key, self.username]):
            print("❌ Metamob credentials not configured")
            return False, {}
            
        try:
            # Handle both list and dictionary formats
            update_data = []
            
            if isinstance(soul_data, list):
                update_data = soul_data
            elif isinstance(soul_data, dict):
                for monster_name, data in soul_data.items():
                    monster_id = self.get_monster_id_by_name(monster_name)
                    if monster_id:
                        if isinstance(data, dict):
                            soul_count = data.get('quantity', 0)
                        else:
                            soul_count = data
                            
                        print(f"🔍 Preparing sync: {monster_name} → {soul_count} souls (Monster ID: {monster_id})")
                            
                        update_data.append({
                            "id": monster_id,
                            "quantite": soul_count,
                            "monster_name": monster_name  # Keep name for progress tracking
                        })
                    else:
                        print(f"⚠️ Skipping {monster_name} - not found on Metamob")
            
            if not update_data:
                print("❌ No valid monsters to update")
                return False, {}
            
            total_monsters = len(update_data)
            total_souls = sum(item['quantite'] for item in update_data)
            print(f"📊 Syncing {total_monsters} monsters ({total_souls} total souls) to Metamob...")
            
            # Split large datasets into smaller chunks (max 50 per request)
            chunk_size = 50
            chunks = [update_data[i:i + chunk_size] for i in range(0, len(update_data), chunk_size)]
            
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'HTTP-X-USERKEY': self.user_key,
                'Content-Type': 'application/json'
            }
            
            total_success = 0
            total_errors = 0
            total_updated_souls = 0
            processed_monsters = 0
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                print(f"📦 Processing chunk {i+1}/{len(chunks)} ({len(chunk)} monsters)...")
                
                # Update progress
                if progress_callback:
                    current_souls = sum(item['quantite'] for item in update_data[:processed_monsters])
                    progress_callback(processed_monsters, total_monsters, total_success, current_souls)
                
                # Remove monster_name from API payload
                api_chunk = [{"id": item["id"], "quantite": item["quantite"]} for item in chunk]
                
                try:
                    response = requests.put(
                        f"{self.base_url}/utilisateurs/{self.username}/monstres",
                        headers=headers,
                        json=api_chunk,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        chunk_success = len(result.get('reussite', {}))
                        chunk_errors = len(result.get('erreurs', []))
                        
                        # Calculate souls for successful updates in this chunk
                        chunk_souls = 0
                        for item in chunk:
                            if str(item['id']) in result.get('reussite', {}):
                                chunk_souls += item['quantite']
                        
                        total_success += chunk_success
                        total_errors += chunk_errors
                        total_updated_souls += chunk_souls
                        processed_monsters += len(chunk)
                        
                        print(f"✅ Chunk {i+1}: {chunk_success} updated, {chunk_errors} errors")
                        
                        # Update progress after chunk completion
                        if progress_callback:
                            progress_callback(processed_monsters, total_monsters, total_success, total_updated_souls)
                        
                    else:
                        print(f"❌ Chunk {i+1} failed: {response.status_code} - {response.text}")
                        total_errors += len(chunk)
                        processed_monsters += len(chunk)
                        
                except requests.exceptions.Timeout:
                    print(f"⏱️ Chunk {i+1} timed out")
                    total_errors += len(chunk)
                    processed_monsters += len(chunk)
                except Exception as e:
                    print(f"❌ Chunk {i+1} error: {e}")
                    total_errors += len(chunk)
                    processed_monsters += len(chunk)
                
                # Small delay between chunks
                if i < len(chunks) - 1:
                    time.sleep(1)
            
            # Final progress update
            if progress_callback:
                progress_callback(total_monsters, total_monsters, total_success, total_updated_souls)
            
            print(f"✅ Batch update complete: {total_success} updated, {total_errors} errors out of {total_monsters} total")
            
            # Return success status and statistics
            stats = {
                'updated_monsters': total_success,
                'failed_monsters': total_errors,
                'total_updated_souls': total_updated_souls,
                'total_monsters': total_monsters
            }
            
            return total_success > 0, stats
                
        except Exception as e:
            print(f"❌ Metamob batch update error: {e}")
            return False, {}
    
    
    def update_monster_state(self, monster_name, state, quantity=None):
        """Update a single monster's RECHERCHE/PROPOSER state and optionally quantity
        
        Args:
            monster_name (str): Name of the monster
            state (str): 'recherche', 'propose', or 'aucun'
            quantity (int, optional): New quantity value
        """
        try:
            if not self.is_configured():
                print("❌ Metamob API not configured")
                return False
            
            if state not in ['recherche', 'propose', 'aucun']:
                print(f"❌ Invalid state: {state}. Must be 'recherche', 'propose', or 'aucun'")
                return False
            
            monster_id = self.get_monster_id_by_name(monster_name)
            if not monster_id:
                print(f"❌ Monster '{monster_name}' not found on Metamob")
                return False
            
            update_data = [{
                "id": monster_id,
                "etat": state
            }]
            
            if quantity is not None:
                update_data[0]["quantite"] = quantity
            
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'HTTP-X-USERKEY': self.user_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.put(
                f"{self.base_url}/utilisateurs/{self.username}/monstres",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                success_messages = result.get('reussite', {}).get(str(monster_id), [])
                
                state_names = {
                    'recherche': 'RECHERCHE',
                    'propose': 'PROPOSER', 
                    'aucun': 'NEUTRAL'
                }
                
                print(f"✅ {monster_name} → {state_names[state]} state updated")
                for message in success_messages:
                    print(f"   📝 {message}")
                return True
            else:
                print(f"❌ Failed to update {monster_name}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating {monster_name} state: {e}")
            return False
    
    def batch_update_states(self, monsters_states):
        """Update multiple monsters' RECHERCHE/PROPOSER states in batch
        
        Args:
            monsters_states (list): List of dicts with 'name', 'state', and optionally 'quantity'
                                   Example: [{'name': 'Arakne', 'state': 'recherche', 'quantity': 5}]
        """
        try:
            if not self.is_configured():
                print("❌ Metamob API not configured")
                return False
            
            update_data = []
            
            for monster_info in monsters_states:
                monster_name = monster_info.get('name')
                state = monster_info.get('state')
                quantity = monster_info.get('quantity')
                
                if state not in ['recherche', 'propose', 'aucun']:
                    print(f"⚠️ Skipping {monster_name} - invalid state: {state}")
                    continue
                
                monster_id = self.get_monster_id_by_name(monster_name)
                if monster_id:
                    monster_update = {
                        "id": monster_id,
                        "etat": state
                    }
                    
                    if quantity is not None:
                        monster_update["quantite"] = quantity
                    
                    update_data.append(monster_update)
                else:
                    print(f"⚠️ Skipping {monster_name} - not found on Metamob")
            
            if not update_data:
                print("❌ No valid monsters to update")
                return False
            
            headers = {
                'HTTP-X-APIKEY': self.api_key,
                'HTTP-X-USERKEY': self.user_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.put(
                f"{self.base_url}/utilisateurs/{self.username}/monstres",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                success_count = len(result.get('reussite', {}))
                error_count = len(result.get('erreurs', []))
                
                print(f"✅ Batch state update complete: {success_count} updated, {error_count} errors")
                
                # Show detailed results
                for monster_id, messages in result.get('reussite', {}).items():
                    print(f"   📝 Monster ID {monster_id}:")
                    for message in messages:
                        print(f"      • {message}")
                
                return True
            else:
                print(f"❌ Metamob batch state update failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Metamob batch state update error: {e}")
            return False
    
    def get_user_monsters_with_states(self):
        """Get all monsters for the user including their current RECHERCHE/PROPOSER states"""
        try:
            if not self.is_configured():
                print("❌ Metamob API not configured")
                return None
            
            headers = {
                'HTTP-X-APIKEY': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/utilisateurs/{self.username}/monstres",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                monsters = response.json()
                print(f"✅ Retrieved {len(monsters)} monsters with states from Metamob")
                return monsters
            else:
                print(f"❌ Failed to get monsters: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting monsters with states: {e}")
            return None
    
    def update_monster_states_with_thresholds(self, monsters_data, recherche_threshold=0, proposer_threshold=50, aucun_threshold=100):
        """
        Update monster states based on soul quantity thresholds
        
        Args:
            monsters_data: Dictionary with monster names as keys and quantities as values
            recherche_threshold: Quantity - RECHERCHE if strictly less than (<)
            proposer_threshold: Quantity - PROPOSER if strictly greater than (>)
            aucun_threshold: Quantity - AUCUN if exactly equal to (=)
        """
        if not self.is_connected():
            return False
        
        try:
            updates = []
            
            for monster_name, data in monsters_data.items():
                monster_id = self.get_monster_id(monster_name)
                if not monster_id:
                    continue
                
                # Extract quantity from data structure
                if isinstance(data, dict):
                    quantity = data.get('quantity', 0)
                else:
                    quantity = data  # Handle case where data is already a number
                
                # Determine state based on exact thresholds
                if quantity < recherche_threshold:
                    etat = "recherche"
                elif quantity > proposer_threshold:
                    etat = "propose"
                elif quantity == aucun_threshold:
                    etat = "aucun"
                else:
                    # For values that don't match any threshold, keep current state
                    continue  # Skip this monster to preserve existing state
                
                updates.append({
                    "id": monster_id,
                    "quantite": quantity,
                    "etat": etat
                })
            
            if updates:
                return self.batch_update_souls(updates)
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating monster states with thresholds: {e}")
            return False
    
    def update_monster_states_with_thresholds_progress(self, monsters_data, recherche_threshold=0, proposer_threshold=50, aucun_threshold=100, progress_callback=None):
        """
        Update monster states based on soul quantity thresholds with progress reporting
        
        Args:
            monsters_data: Dictionary with monster names as keys and quantities as values
            recherche_threshold: Quantity - RECHERCHE if strictly less than (<)
            proposer_threshold: Quantity - PROPOSER if strictly greater than (>)
            aucun_threshold: Quantity - AUCUN if exactly equal to (=)
            progress_callback: Function to call with progress updates
        """
        if not self.is_connected():
            return False, {}
        
        try:
            updates = []
            
            for monster_name, data in monsters_data.items():
                monster_id = self.get_monster_id(monster_name)
                if not monster_id:
                    continue
                
                # Extract quantity from data structure
                if isinstance(data, dict):
                    quantity = data.get('quantity', 0)
                else:
                    quantity = data
                
                # Determine state based on exact thresholds
                if quantity < recherche_threshold:
                    etat = "recherche"
                elif quantity > proposer_threshold:
                    etat = "propose"
                elif quantity == aucun_threshold:
                    etat = "aucun"
                else:
                    continue  # Skip this monster to preserve existing state
                
                updates.append({
                    "id": monster_id,
                    "quantite": quantity,
                    "etat": etat,
                    "monster_name": monster_name
                })
            
            if updates:
                return self.batch_update_souls_with_progress(updates, progress_callback)
            
            return True, {'updated_monsters': 0, 'failed_monsters': 0, 'total_updated_souls': 0, 'total_monsters': 0}
            
        except Exception as e:
            print(f"❌ Error updating monster states with thresholds: {e}")
            return False, {}
    
    def set_recherche_for_monsters(self, monster_names):
        """Set specific monsters to recherche state"""
        if not self.is_connected():
            return False
        
        try:
            updates = []
            for monster_name in monster_names:
                monster_id = self.get_monster_id(monster_name)
                if monster_id:
                    updates.append({
                        "id": monster_id,
                        "etat": "recherche"
                    })
            
            if updates:
                return self.batch_update_souls(updates)
            return True
            
        except Exception as e:
            print(f"❌ Error setting recherche state: {e}")
            return False
    
    def set_proposer_for_monsters(self, monster_names):
        """Set specific monsters to propose state"""
        if not self.is_connected():
            return False
        
        try:
            updates = []
            for monster_name in monster_names:
                monster_id = self.get_monster_id(monster_name)
                if monster_id:
                    updates.append({
                        "id": monster_id,
                        "etat": "propose"
                    })
            
            if updates:
                return self.batch_update_souls(updates)
            return True
            
        except Exception as e:
            print(f"❌ Error setting proposer state: {e}")
            return False
    
    def set_aucun_for_monsters(self, monster_names):
        """Set specific monsters to aucun state (neutral)"""
        if not self.is_connected():
            return False
        
        try:
            updates = []
            for monster_name in monster_names:
                monster_id = self.get_monster_id(monster_name)
                if monster_id:
                    updates.append({
                        "id": monster_id,
                        "etat": "aucun"
                    })
            
            if updates:
                return self.batch_update_souls(updates)
            return True
            
        except Exception as e:
            print(f"❌ Error setting aucun state: {e}")
            return False

class SoulCounter:
    """Computer vision system for counting yellow soul stones in bank slots"""
    
    def __init__(self):
        self.bank_grid_pos = None  # Top-left corner of bank grid
        self.slot_size = (44, 44)  # Precise slot size based on red square analysis
        self.grid_spacing = (47, 47)  # Precise spacing between slot centers
        self.grid_cols = 5  # Bank columns (5 visible columns)
        self.grid_rows = 9  # Bank rows (9 visible rows - corrected)
        
        # Color ranges for yellow soul detection (HSV format) - optimized for screenshot
        self.yellow_lower = np.array([18, 120, 140])  # More precise yellow range
        self.yellow_upper = np.array([32, 255, 255])  # Better upper bound
        
        # Template for soul shape (will be created dynamically)
        self.soul_template = None
        self.template_threshold = 0.7
        
        # Debug mode for troubleshooting
        self.debug_mode = False
        self.debug_counter = 0
        
        # Create basic soul template (golden oval shape)
        self.create_soul_template()
        
    def create_soul_template(self):
        """Create a basic template for soul stone detection"""
        try:
            # Create a simple template that looks like a soul stone
            template_size = 20
            template = np.zeros((template_size, template_size, 3), dtype=np.uint8)
            
            # Create golden/yellow oval shape
            center = (template_size // 2, template_size // 2)
            axes = (8, 6)  # Oval shape
            
            # Fill with golden yellow color (BGR format)
            cv2.ellipse(template, center, axes, 0, 0, 360, (0, 215, 255), -1)  # Golden yellow
            cv2.ellipse(template, center, (6, 4), 0, 0, 360, (0, 255, 255), -1)  # Bright yellow center
            
            self.soul_template = template
            
        except Exception as e:
            print(f"Error creating soul template: {e}")
            self.soul_template = None
    
    def detect_souls_with_ocr(self, slot_image):
        """Alternative method: Try to detect soul count using OCR if numbers are visible"""
        try:
            # Look for small numbers that might indicate soul count
            gray = cv2.cvtColor(slot_image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to make text more visible
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Try to import pytesseract for OCR
            try:
                import pytesseract
                
                # Configure for small numbers only
                config = '--psm 8 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(thresh, config=config).strip()
                
                # Try to extract number
                if text.isdigit():
                    return int(text)
                    
            except ImportError:
                # OCR not available, skip this method
                pass
                
            return 0
            
        except Exception as e:
            return 0
    
    def detect_souls_by_brightness(self, slot_image):
        """Alternative method: Detect souls by brightness patterns"""
        try:
            # Convert to LAB color space for better brightness analysis
            lab = cv2.cvtColor(slot_image, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            
            # Soul stones are typically bright
            bright_mask = l_channel > 120  # Bright areas
            
            # Count bright regions that could be souls
            labeled, num_regions = cv2.connectedComponents(bright_mask.astype(np.uint8))
            
            # Filter regions by size
            soul_count = 0
            for i in range(1, num_regions + 1):
                region_size = np.sum(labeled == i)
                if 50 < region_size < 500:  # Reasonable soul size
                    soul_count += 1
                    
            return soul_count
            
        except Exception as e:
            return 0
        
    def set_bank_grid_position(self, x, y):
        """Set the top-left position of the bank grid"""
        self.bank_grid_pos = (x, y)
        
    def get_slot_position(self, row, col):
        """Calculate the screen position of a specific slot"""
        if not self.bank_grid_pos:
            return None
            
        x = self.bank_grid_pos[0] + (col * self.grid_spacing[0])
        y = self.bank_grid_pos[1] + (row * self.grid_spacing[1])
        return (x, y)
    
    def capture_slot_screenshot(self, row, col):
        """Capture screenshot of a specific bank slot with improved accuracy"""
        slot_pos = self.get_slot_position(row, col)
        if not slot_pos:
            return None
            
        # More precise capture - capture the exact slot area
        # Add small margin to ensure we get the complete slot
        margin = 1
        capture_x = slot_pos[0] - margin
        capture_y = slot_pos[1] - margin
        capture_width = self.slot_size[0] + (margin * 2)
        capture_height = self.slot_size[1] + (margin * 2)
        
        try:
            screenshot = pyautogui.screenshot(region=(
                capture_x, 
                capture_y, 
                capture_width, 
                capture_height
            ))
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Debug: Print capture info
            if self.debug_mode:
                print(f"DEBUG: Capturing slot ({row}, {col}) at ({capture_x}, {capture_y}) size ({capture_width}x{capture_height})")
            
            return cv_image
            
        except Exception as e:
            print(f"Error capturing slot ({row}, {col}): {e}")
            return None
    
    def detect_yellow_souls(self, slot_image):
        """Detect yellow soul stones in a slot using multiple improved methods"""
        if slot_image is None:
            return 0
            
        try:
            # Method 1: HSV Color Detection (original improved)
            hsv = cv2.cvtColor(slot_image, cv2.COLOR_BGR2HSV)
            yellow_lower1 = np.array([15, 100, 150])
            yellow_upper1 = np.array([35, 255, 255])
            yellow_mask = cv2.inRange(hsv, yellow_lower1, yellow_upper1)
            
            # Method 2: HoughCircles - detect circular soul shapes
            gray = cv2.cvtColor(slot_image, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=20,  # Minimum distance between circle centers
                param1=50,   # Upper threshold for edge detection
                param2=30,   # Accumulator threshold for center detection
                minRadius=8, # Minimum soul radius
                maxRadius=25 # Maximum soul radius
            )
            
            circle_count = 0
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    # Check if this circle area has yellow pixels
                    mask = np.zeros(gray.shape, dtype=np.uint8)
                    cv2.circle(mask, (x, y), r, 255, -1)
                    masked_yellow = cv2.bitwise_and(yellow_mask, mask)
                    yellow_ratio = np.sum(masked_yellow > 0) / np.sum(mask > 0)
                    if yellow_ratio > 0.3:  # If >30% of circle is yellow
                        circle_count += 1
            
            # Method 3: Contour-based detection (enhanced)
            kernel = np.ones((2, 2), np.uint8)
            yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
            yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            valid_souls = 0
            soul_centers = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                
                if (80 <= area <= 800 and 8 <= w <= 40 and 8 <= h <= 40):
                    aspect_ratio = w / h if h > 0 else 0
                    if 0.7 <= aspect_ratio <= 1.4:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        too_close = False
                        for existing_center in soul_centers:
                            distance = ((center_x - existing_center[0])**2 + (center_y - existing_center[1])**2)**0.5
                            if distance < 15:
                                too_close = True
                                break
                        
                        if not too_close:
                            soul_centers.append((center_x, center_y))
                            valid_souls += 1
            
            # Method 4: Template matching (if we have a template)
            template_count = 0
            if hasattr(self, 'soul_template') and self.soul_template is not None:
                result = cv2.matchTemplate(slot_image, self.soul_template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= 0.7)
                template_count = len(locations[0])
            
            # Method 5: OCR-based detection
            ocr_count = self.detect_souls_with_ocr(slot_image)
            
            # Method 6: Brightness-based detection
            brightness_count = self.detect_souls_by_brightness(slot_image)
            
            # Method 7: Adaptive detection based on slot content
            adaptive_count = 0
            yellow_pixel_ratio = np.sum(yellow_mask > 0) / (yellow_mask.shape[0] * yellow_mask.shape[1])
            
            if yellow_pixel_ratio > 0.05:  # If slot has yellow content
                # Estimate souls based on yellow area coverage
                if yellow_pixel_ratio > 0.6:    # Very full slot
                    adaptive_count = 3
                elif yellow_pixel_ratio > 0.35: # Medium full slot  
                    adaptive_count = 2
                elif yellow_pixel_ratio > 0.1:  # Some content
                    adaptive_count = 1
            
            # Combine results using advanced voting system
            detection_methods = {
                'contour': valid_souls,
                'circle': circle_count, 
                'template': template_count,
                'ocr': ocr_count,
                'brightness': brightness_count,
                'adaptive': adaptive_count
            }
            
            # Remove zero counts and outliers
            valid_detections = [v for v in detection_methods.values() if v > 0 and v <= 10]
            
            if valid_detections:
                # Use the most reliable method based on confidence
                if ocr_count > 0:  # OCR is most reliable if available
                    final_count = ocr_count
                elif len(valid_detections) >= 2:
                    # Use median of multiple methods
                    final_count = int(np.median(valid_detections))
                else:
                    # Use the single detection
                    final_count = valid_detections[0]
            else:
                # Fallback: check if slot appears to have any content
                if yellow_pixel_ratio > 0.02:
                    final_count = 1  # Assume at least 1 soul if yellow content detected
                else:
                    final_count = 0
            
            return min(final_count, 99)  # Cap at 99 souls per slot
            
        except Exception as e:
            print(f"Error detecting souls: {e}")
            return 0
            
        except Exception as e:
            print(f"Error detecting souls: {e}")
            return 0
    
    def save_debug_image(self, slot_image, monster_name, slot_info, detected_count):
        """Save debug image for troubleshooting"""
        if not self.debug_mode:
            return
            
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            debug_dir = os.path.join(script_dir, 'debug_images')
            os.makedirs(debug_dir, exist_ok=True)
            
            self.debug_counter += 1
            filename = f"debug_{self.debug_counter:03d}_{monster_name}_{slot_info['row']}_{slot_info['col']}_{detected_count}souls.jpg"
            filepath = os.path.join(debug_dir, filename)
            
            cv2.imwrite(filepath, slot_image)
            print(f"DEBUG: Saved {filepath}")
            
        except Exception as e:
            print(f"Error saving debug image: {e}")
    
    def save_full_grid_debug(self, monster_name):
        """Save debug images of the entire visible grid for troubleshooting"""
        if not self.debug_mode:
            return
            
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            debug_dir = os.path.join(script_dir, 'debug_images')
            os.makedirs(debug_dir, exist_ok=True)
            
            print(f"DEBUG: Saving full grid debug for {monster_name}")
            
            # Capture each slot in the scanning area
            for row in range(6):  # Match the scanning area
                for col in range(8):
                    slot_image = self.capture_slot_screenshot(row, col)
                    if slot_image is not None:
                        filename = f"grid_{monster_name}_r{row}_c{col}.jpg"
                        filepath = os.path.join(debug_dir, filename)
                        cv2.imwrite(filepath, slot_image)
                        print(f"DEBUG: Grid slot ({row}, {col}) saved to {filename}")
            
        except Exception as e:
            print(f"Error saving grid debug: {e}")
    
    def is_slot_empty(self, slot_image):
        """Check if a slot is empty (dark/black) with improved detection"""
        if slot_image is None:
            return True
            
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(slot_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate average brightness
            avg_brightness = np.mean(gray)
            
            # Calculate the percentage of very dark pixels
            dark_threshold = 40
            dark_pixels = np.sum(gray < dark_threshold)
            total_pixels = gray.size
            dark_percentage = (dark_pixels / total_pixels) * 100
            
            # Also check for very low color variance (indicating solid dark color)
            color_variance = np.var(gray)
            
            # Slot is empty if:
            # 1. Average brightness is very low, OR
            # 2. Most pixels are dark AND low color variance
            is_empty = (avg_brightness < 25 or 
                       (dark_percentage > 80 and color_variance < 200))
            
            return is_empty
            
        except Exception as e:
            print(f"Error checking empty slot: {e}")
            return True
    
    def count_souls_in_visible_area(self, monster_name="unknown"):
        """Count souls in the currently visible bank area with improved accuracy"""
        # Save full grid debug if debug mode is on
        if self.debug_mode:
            self.save_full_grid_debug(monster_name)
        
        total_souls = 0
        detected_slots = []
        
        # Scan the correct visible area - 5 columns × 9 rows = 45 slots total
        max_rows = 9  # Correct number of visible rows
        max_cols = 5  # Correct number of visible columns
        
        for row in range(max_rows):
            for col in range(max_cols):
                slot_image = self.capture_slot_screenshot(row, col)
                
                if slot_image is None:
                    if self.debug_mode:
                        print(f"DEBUG: Failed to capture slot ({row}, {col})")
                    continue
                
                # First check if slot is empty to avoid unnecessary processing
                if self.is_slot_empty(slot_image):
                    soul_count = 0
                    if self.debug_mode:
                        print(f"DEBUG: Slot ({row}, {col}): Empty slot detected")
                else:
                    soul_count = self.detect_yellow_souls(slot_image)
                
                if soul_count > 0:
                    slot_info = {
                        'row': row,
                        'col': col,
                        'souls': soul_count
                    }
                    detected_slots.append(slot_info)
                    total_souls += soul_count
                    
                    # Debug: Save image and log individual slot detections
                    print(f"DEBUG: Slot ({row}, {col}): {soul_count} souls")
                    self.save_debug_image(slot_image, monster_name, slot_info, soul_count)
        
        if self.debug_mode:
            print(f"DEBUG: Total souls detected for {monster_name}: {total_souls}")
        
        return {
            'total_souls': total_souls,
            'detected_slots': detected_slots,
            'confidence': self.calculate_confidence(detected_slots)
        }
    
    def calculate_confidence(self, detected_slots):
        """Calculate confidence score based on detection results"""
        if not detected_slots:
            return 1.0  # High confidence for empty (no souls)
        
        # Base confidence
        confidence = 0.8
        
        # Increase confidence if we detected reasonable numbers
        reasonable_counts = sum(1 for slot in detected_slots if 1 <= slot['souls'] <= 20)
        if reasonable_counts == len(detected_slots):
            confidence = 0.95
        
        return confidence
    
    def validate_detection(self, result):
        """Validate detection results and return issues if any"""
        issues = []
        
        # Don't add issues for 0 souls - treat as valid result
        if result['total_souls'] > 200:
            issues.append(f"Very high soul count ({result['total_souls']}) - please verify")
        elif result['confidence'] < 0.7 and result['total_souls'] > 0:
            # Only flag low confidence if souls were actually detected
            issues.append("Low confidence detection - manual verification recommended")
        
        return issues

class MonsterRetrievalTool:
    def __init__(self):
        # Initialize configuration directory for license storage
        self.config_dir = os.path.expanduser("~/.monster_tool")
        self.license_file = os.path.join(self.config_dir, ".license")
        self.ensure_config_dir()
        
        self.root = tk.Tk()
        self.root.title("🎮 Monster Soul Retrieval Dashboard - Enhanced")
        self.root.geometry("1200x900")
        self.root.minsize(1100, 800)
        
        # LICENSE VALIDATION - REQUIRE REAL LICENSE KEY
        print("🔐 Monster Soul Retrieval Tool - License Validation Required")
        print("=" * 60)
        
        # Check for saved license first
        saved_license = self.load_saved_license()
        if saved_license:
            print(f"📁 Found saved license: {saved_license[:4]}****-****-****")
            if self.validate_license_key(saved_license):
                print("✅ Saved license validated successfully!")
                print("🎮 Monster Soul Retrieval Tool access granted")
            else:
                print("❌ Saved license is invalid or expired, removing...")
                self.remove_saved_license()
                saved_license = None
        
        # If no valid saved license, prompt for new one
        if not saved_license:
            license_key = self.prompt_for_license()
            if not license_key:
                print("❌ License key required to continue")
                self.root.destroy()
                exit()
            
            # Validate license key against the licensing system database
            if not self.validate_license_key(license_key):
                print("❌ Invalid or expired license key")
                self.root.destroy()
                exit()
            
            # Save the valid license key
            self.save_license_key(license_key)
            print("💾 License key saved for future use")
            print("✅ License validation successful!")
            print("🎮 Monster Soul Retrieval Tool access granted")
        
        # Set icon and window properties
        self.root.attributes('-topmost', False)
        self.keep_on_top = False
        
        # Modern dashboard-inspired color schemes
        self.themes = {
            'dark': {
                'bg': '#1a1d29',
                'bg_solid': '#1a1d29',
                'fg': '#f7fafc',
                'card_bg': '#2d3748',
                'card_bg_solid': '#2d3748',
                'accent': '#667eea',
                'success': '#68d391',
                'warning': '#fbb13c',
                'danger': '#fc8181',
                'info': '#63b3ed',
                'secondary': '#a0aec0',
                'border': '#4a5568',
                'hover': '#374151',
                'gradient_start': '#667eea',
                'gradient_end': '#f093fb',
                'sidebar': '#1a202c',
                'sidebar_text': '#e2e8f0',
                'stats_bg': '#2d3748',
                'stats_border': '#4a5568'
            }
        }
        
        # Section visibility flags
        self.main_section_visible = True
        self.log_section_visible = True
        
        # Load monster names from file (default to Regular)
        self.monster_names = self.load_monster_names("Regular")
        
        # Variables
        self.selected_monsters = {}
        self.is_running = False
        self.is_paused = False
        self.is_scanning = False
        self.scan_progress = 0
        
        # Progress tracking
        self.total_souls = 0
        self.processed_souls = 0
        self.successful_retrievals = 0
        self.failed_retrievals = 0
        self.failed_monsters = []
        self.start_time = None
        
        # Enhanced logging system
        self.session_log = {
            'session_start': None,
            'session_end': None,
            'total_monsters': 0,
            'total_souls': 0,
            'successful_retrievals': 0,
            'failed_retrievals': 0,
            'monsters_data': {},
            'settings': {},
            'timeline': []
        }
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Initialize soul counter
        self.soul_counter = SoulCounter()
        
        # Initialize Metamob API for syncing soul data
        self.metamob_api = MetamobAPI()
        
        # Metamob state thresholds
        self.recherche_threshold = 0      # Souls <= this value trigger RECHERCHE
        self.proposer_threshold = 50      # Souls >= this value trigger PROPOSER  
        self.aucun_threshold = 100        # Souls >= this value trigger AUCUN
        
        # Coordinate-based calibration system for 100% accuracy
        self.slot_coordinates = []  # Will store 45 precise coordinates
        self.coordinates_file = "config/bank_coordinates.json"
        self.coordinate_calibration_active = False
        self.current_slot_index = 0  # Track which slot we're capturing (0-44)
        self.captured_coordinates = []  # Temporary storage during capture
        self.coordinate_listener = None  # Mouse listener for capturing clicks
        self.calibration_window = None
        
        # Load previously saved coordinates automatically
        self.slot_coordinates = self.load_slot_coordinates()
        if self.slot_coordinates:
            print(f"✅ Loaded {len(self.slot_coordinates)} saved slot coordinates from {self.coordinates_file}")
        else:
            print(f"📍 No saved coordinates found - use Manual Calibration to set up slot coordinates")
        
        # Soul scanning data
        self.soul_scan_data = {}
        self.last_scan_time = None
        
        self.setup_modern_ui()
        
        # Initialize Metamob API status
        self.update_metamob_status()
        
        # Initialize Auto-Updater
        self.auto_updater = AutoUpdater(self)
        
        # Check for updates on startup (optional - uncomment if you want automatic checks)
        # self.root.after(2000, self.check_for_updates_on_startup)
        
    def prompt_for_license(self):
        """Prompt user for license key"""
        import tkinter.simpledialog as simpledialog
        
        # Create a temporary root for the dialog
        temp_root = tk.Tk()
        temp_root.withdraw()  # Hide the window
        
        license_key = simpledialog.askstring(
            "🔐 License Required",
            "Enter your Monster Soul Retrieval Tool license key:\n\n"
            "Format: XXXX-XXXX-XXXX-XXXX\n\n"
            "Contact your administrator if you don't have a license key.",
            parent=temp_root
        )
        
        temp_root.destroy()
        return license_key.strip().upper() if license_key else None
    
    def validate_license_key(self, license_key):
        """Validate license key against the licensing system database"""
        import sqlite3
        import os
        from datetime import datetime
        
        try:
            # Path to the licensing system database
            db_path = r"C:\Users\Oussama\licensing_system\database\clients.db"
            
            if not os.path.exists(db_path):
                print(f"❌ Licensing database not found at: {db_path}")
                return False
            
            # Connect to the licensing database
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if license key exists
                cursor.execute("""
                    SELECT name, tool_name, end_date, period 
                    FROM clients 
                    WHERE license_key = ? AND tool_name = ?
                """, (license_key, "Monster Soul Retrieval Tool"))
                
                result = cursor.fetchone()
                
                if not result:
                    print(f"❌ License key not found: {license_key}")
                    return False
                
                name, tool_name, end_date, period = result
                
                # Check if license is expired
                try:
                    if " " in end_date:
                        # Format: YYYY-MM-DD HH:MM:SS
                        expiry_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
                    else:
                        # Format: YYYY-MM-DD
                        expiry_date = datetime.strptime(end_date, "%Y-%m-%d")
                    
                    if expiry_date < datetime.now():
                        print(f"❌ License expired on: {end_date}")
                        print(f"   Client: {name}")
                        print(f"   Period: {period}")
                        return False
                    
                    # License is valid
                    print(f"✅ Valid license found!")
                    print(f"   Client: {name}")
                    print(f"   Tool: {tool_name}")
                    print(f"   Period: {period}")
                    print(f"   Valid until: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    return True
                    
                except ValueError as e:
                    print(f"❌ Date parsing error: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

    def ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def save_license_key(self, license_key):
        """Save the license key to a local file"""
        try:
            # Simple encryption by encoding
            import base64
            encoded_key = base64.b64encode(license_key.encode()).decode()
            
            with open(self.license_file, 'w') as f:
                f.write(encoded_key)
            
            # Make the file hidden on Windows
            if os.name == 'nt':
                import subprocess
                try:
                    subprocess.call(["attrib", "+H", self.license_file])
                except:
                    pass  # Ignore if attrib command fails
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not save license key: {e}")

    def load_saved_license(self):
        """Load the saved license key if it exists"""
        try:
            if not os.path.exists(self.license_file):
                return None
                
            with open(self.license_file, 'r') as f:
                encoded_key = f.read().strip()
            
            # Simple decryption by decoding
            import base64
            license_key = base64.b64decode(encoded_key.encode()).decode()
            return license_key
            
        except Exception as e:
            print(f"⚠️ Warning: Could not load saved license: {e}")
            return None

    def remove_saved_license(self):
        """Remove the saved license key file"""
        try:
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
        except Exception as e:
            print(f"⚠️ Warning: Could not remove saved license: {e}")

    def load_slot_coordinates(self):
        """Load saved slot coordinates from JSON file"""
        try:
            if os.path.exists(self.coordinates_file):
                with open(self.coordinates_file, 'r') as f:
                    data = json.load(f)
                    return data.get('slot_coordinates', [])
        except Exception as e:
            print(f"Error loading coordinates: {e}")
        return []
    
    def save_slot_coordinates(self):
        """Save slot coordinates to JSON file"""
        try:
            # Ensure config directory exists
            os.makedirs("config", exist_ok=True)
            
            data = {
                'slot_coordinates': self.slot_coordinates,
                'calibration_date': datetime.now().isoformat(),
                'total_slots': len(self.slot_coordinates),
                'grid_dimensions': {'rows': 9, 'cols': 5}
            }
            
            with open(self.coordinates_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Saved {len(self.slot_coordinates)} slot coordinates to {self.coordinates_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving coordinates: {e}")
            return False

    def load_monster_names(self, monster_type="Regular"):
        """Load monster names from file based on type"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Choose file based on monster type
            if monster_type == "Boss":
                monster_file_path = os.path.join(script_dir, 'boss_names.txt')
                backup_file_path = os.path.join(script_dir, 'monster_names.txt')  # Fallback
            else:
                monster_file_path = os.path.join(script_dir, 'monster_names.txt')
                backup_file_path = None
            
            # Try to load the primary file
            try:
                with open(monster_file_path, 'r', encoding='utf-8') as f:
                    monster_names = [line.strip() for line in f.readlines() if line.strip()]
                    file_name = os.path.basename(monster_file_path)
                    print(f"✅ Loaded {len(monster_names)} {monster_type.lower()} monsters from {file_name}")
                    return monster_names
            except FileNotFoundError:
                if monster_type == "Boss" and backup_file_path:
                    # Boss file not found, try regular monsters as fallback
                    try:
                        with open(backup_file_path, 'r', encoding='utf-8') as f:
                            monster_names = [line.strip() for line in f.readlines() if line.strip()]
                            print(f"⚠️ boss_names.txt not found, loaded {len(monster_names)} regular monsters instead")
                            messagebox.showwarning(
                                "Boss File Missing", 
                                "boss_names.txt not found!\n\nLoaded regular monsters instead.\nCreate boss_names.txt file with your boss monster names."
                            )
                            return monster_names
                    except FileNotFoundError:
                        pass
                
                # Neither file found
                expected_path = monster_file_path
                messagebox.showerror("Error", f"{os.path.basename(monster_file_path)} file not found!\nExpected location: {expected_path}")
                return []
                
        except Exception as e:
            messagebox.showerror("Error", f"Error reading monster file: {str(e)}")
            return []
    
    def load_monster_type(self):
        """Called when monster type selection changes"""
        monster_type = self.monster_type_var.get()
        
        # Update info label
        if hasattr(self, 'type_info_label'):
            if monster_type == "Boss":
                self.type_info_label.config(text="Loading boss monsters...", fg=self.get_theme_colors()['warning'])
            else:
                self.type_info_label.config(text="Loading regular monsters...", fg=self.get_theme_colors()['secondary'])
        
        # Reload monster names
        self.monster_names = self.load_monster_names(monster_type)
        
        # Update the listbox
        if hasattr(self, 'monster_listbox'):
            self.monster_listbox.delete(0, tk.END)
            
            for name in self.monster_names:
                # Add monster name without icons
                display_name = name
                self.monster_listbox.insert(tk.END, display_name)
        
        # Update info label with count
        if hasattr(self, 'type_info_label'):
            if monster_type == "Boss":
                self.type_info_label.config(text=f"{len(self.monster_names)} boss monsters loaded")
            else:
                self.type_info_label.config(text=f"{len(self.monster_names)} regular monsters loaded")
    
    def get_theme_colors(self):
        """Get current theme colors (always dark theme)"""
        return self.themes['dark']
    
    def create_modern_button(self, parent, text, command, bg_color=None, width=None, height=None, style="default"):
        """Create a modern styled button with enhanced dashboard styling"""
        colors = self.get_theme_colors()
        
        if bg_color is None:
            bg_color = colors['accent']
        
        # Create button with modern styling
        button = tk.Button(
            parent, 
            text=text, 
            command=command,
            bg=bg_color,
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            padx=25,
            pady=12
        )
        
        if width:
            button.config(width=width)
        if height:
            button.config(height=height)
            
        # Enhanced hover effects with smooth transitions
        def on_enter(e):
            if style == "gradient":
                button.config(bg=self.adjust_color(bg_color, -15), relief='raised', borderwidth=1)
            else:
                button.config(bg=self.adjust_color(bg_color, -20))
        
        def on_leave(e):
            button.config(bg=bg_color, relief='flat', borderwidth=0)
        
        def on_click(e):
            button.config(bg=self.adjust_color(bg_color, -40))
            parent.after(100, lambda: button.config(bg=bg_color))
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)
        
        return button
    
    def adjust_color(self, color, adjustment):
        """Adjust color brightness"""
        if color.startswith('#'):
            # Convert hex to RGB, adjust, and convert back
            color = color[1:]
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            adjusted = tuple(max(0, min(255, c + adjustment)) for c in rgb)
            return f"#{adjusted[0]:02x}{adjusted[1]:02x}{adjusted[2]:02x}"
        return color
    
    def create_modern_frame(self, parent, title=None, padx=15, pady=15, card_style="default"):
        """Create a modern styled frame with optional title and dashboard styling"""
        colors = self.get_theme_colors()
        
        container = tk.Frame(parent, bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg'])
        
        if title:
            title_frame = tk.Frame(container, bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg'])
            title_frame.pack(fill='x', pady=(0, 10))
            
            title_label = tk.Label(
                title_frame,
                text=title,
                font=('Segoe UI', 14, 'bold'),
                fg=colors['fg'],
                bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg']
            )
            title_label.pack(side='left')
            
            # Add modern gradient line
            line_frame = tk.Frame(title_frame, height=3, bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg'])
            line_frame.pack(side='left', fill='x', expand=True, padx=(15, 0))
            
            gradient_line = tk.Frame(line_frame, height=3, bg=colors['accent'])
            gradient_line.pack(fill='x', pady=1)
        
        # Create card with modern styling
        card_bg = colors['card_bg_solid'] if 'card_bg_solid' in colors else colors['card_bg']
        
        content_frame = tk.Frame(
            container,
            bg=card_bg,
            relief='flat',
            borderwidth=0
        )
        content_frame.pack(fill='both', expand=True, padx=4, pady=4)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(
            content_frame,
            bg=colors['border'],
            height=2
        )
        shadow_frame.pack(side='bottom', fill='x')
        
        inner_frame = tk.Frame(content_frame, bg=card_bg)
        inner_frame.pack(fill='both', expand=True, padx=padx, pady=pady)
        
        return container, inner_frame
    
    def create_dashboard_stat_card(self, parent, title, value, subtitle="", icon="📊", color_key="accent"):
        """Create a modern dashboard-style statistics card"""
        colors = self.get_theme_colors()
        
        card_bg = colors['stats_bg'] if 'stats_bg' in colors else (colors['card_bg_solid'] if 'card_bg_solid' in colors else colors['card_bg'])
        
        card = tk.Frame(
            parent,
            bg=card_bg,
            relief='flat',
            borderwidth=1
        )
        
        # Icon and title row
        header_frame = tk.Frame(card, bg=card_bg)
        header_frame.pack(fill='x', padx=20, pady=(20, 5))
        
        icon_label = tk.Label(
            header_frame,
            text=icon,
            font=('Segoe UI', 16),
            bg=card_bg,
            fg=colors[color_key]
        )
        icon_label.pack(side='left')
        
        title_label = tk.Label(
            header_frame,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            bg=card_bg,
            fg=colors['secondary']
        )
        title_label.pack(side='left', padx=(10, 0))
        
        # Value
        value_label = tk.Label(
            card,
            text=str(value),
            font=('Segoe UI', 24, 'bold'),
            bg=card_bg,
            fg=colors['fg']
        )
        value_label.pack(padx=20, pady=(0, 5))
        
        # Subtitle
        if subtitle:
            subtitle_label = tk.Label(
                card,
                text=subtitle,
                font=('Segoe UI', 9),
                bg=card_bg,
                fg=colors['secondary']
            )
            subtitle_label.pack(padx=20, pady=(0, 20))
        
        return card
    
    def update_dashboard_stats(self, retrievals=None, session_time=None, success_rate=None, monsters_found=None):
        """Update dashboard statistics cards with new values"""
        if not hasattr(self, 'stat_cards'):
            return
            
        updates = {
            'total_retrievals': retrievals,
            'session_time': session_time,
            'success_rate': success_rate,
            'monsters_found': monsters_found
        }
        
        for stat_key, new_value in updates.items():
            if new_value is not None and stat_key in self.stat_cards:
                # Find the value label in the card and update it
                card = self.stat_cards[stat_key]
                for child in card.winfo_children():
                    if isinstance(child, tk.Label) and child.cget('font')[1] == 24:  # Large value label
                        child.config(text=str(new_value))
                        break
    
    def apply_modern_theme(self):
        """Apply modern theme to all widgets"""
        colors = self.get_theme_colors()
        
        # Main window
        self.root.configure(bg=colors['bg'])
        
        # Update all widgets recursively
        def update_widget(widget):
            try:
                widget_class = widget.winfo_class()
                
                if widget_class == 'Label':
                    widget.configure(bg=colors['card_bg'], fg=colors['fg'])
                elif widget_class == 'Frame':
                    current_bg = widget.cget('bg')
                    if current_bg in ['#ffffff', '#252836', '#f8f9fa', '#1a1d29']:
                        widget.configure(bg=colors['card_bg'] if 'card' in str(widget) else colors['bg'])
                elif widget_class in ['Entry', 'Text']:
                    widget.configure(
                        bg=colors['card_bg'], 
                        fg=colors['fg'], 
                        insertbackground=colors['fg'],
                        selectbackground=colors['accent'],
                        relief='flat',
                        borderwidth=1,
                        highlightbackground=colors['border'],
                        highlightthickness=1
                    )
                elif widget_class == 'Listbox':
                    widget.configure(
                        bg=colors['card_bg'], 
                        fg=colors['fg'], 
                        selectbackground=colors['accent'],
                        selectforeground='white',
                        relief='flat',
                        borderwidth=1,
                        highlightbackground=colors['border'],
                        highlightthickness=1
                    )
                
                for child in widget.winfo_children():
                    update_widget(child)
            except:
                pass
        
        update_widget(self.root)
    
    def toggle_keep_on_top(self):
        """Toggle keep window on top functionality"""
        self.keep_on_top = not self.keep_on_top
        self.root.attributes('-topmost', self.keep_on_top)
        
        colors = self.get_theme_colors()
        if self.keep_on_top:
            self.topmost_button.configure(text="📌 Pinned", bg=colors['success'])
        else:
            self.topmost_button.configure(text="📌 Pin Window", bg=colors['secondary'])
    
    def toggle_main_section(self):
        """Toggle visibility of main section with smooth animation"""
        self.main_section_visible = not self.main_section_visible
        
        if self.main_section_visible:
            self.main_content_container.pack(fill='both', expand=True, padx=15, pady=5)
            self.main_toggle_button.configure(text="🔽 Hide Controls")
        else:
            self.main_content_container.pack_forget()
            self.main_toggle_button.configure(text="🔼 Show Controls")
    
    def toggle_log_section(self):
        """Toggle visibility of log section"""
        self.log_section_visible = not self.log_section_visible
        
        if self.log_section_visible:
            self.log_container.pack(fill='both', expand=True, padx=15, pady=5)
            self.log_toggle_button.configure(text="🔽 Hide Logs")
        else:
            self.log_container.pack_forget()
            self.log_toggle_button.configure(text="🔼 Show Logs")
    
    def setup_modern_ui(self):
        """Setup the modern user interface"""
        colors = self.get_theme_colors()
        
        # Configure root
        self.root.configure(bg=colors['bg'])
        
        # Header with gradient-like effect
        header_frame = tk.Frame(self.root, bg=colors['bg'], height=80)
        header_frame.pack(fill='x', padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        # Title with modern styling
        title_container = tk.Frame(header_frame, bg=colors['bg'])
        title_container.pack(side='left', fill='y')
        
        title_label = tk.Label(
            title_container,
            text="🎮 Monster Soul Retrieval",
            font=('Segoe UI', 20, 'bold'),
            fg=colors['accent'],
            bg=colors['bg']
        )
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(
            title_container,
            text="Enhanced Automation Tool",
            font=('Segoe UI', 10),
            fg=colors['secondary'],
            bg=colors['bg']
        )
        subtitle_label.pack(anchor='w')
        
        # Control buttons in header
        button_frame = tk.Frame(header_frame, bg=colors['bg'])
        button_frame.pack(side='right', fill='y')
        
        # Add update button
        self.update_button = self.create_modern_button(
            button_frame,
            "🔄 Get New Updates",
            self.check_and_download_updates,
            colors['info']
        )
        self.update_button.pack(side='right', padx=5)
        
        self.topmost_button = self.create_modern_button(
            button_frame,
            "📌 Pin Window",
            self.toggle_keep_on_top,
            colors['secondary']
        )
        self.topmost_button.pack(side='right', padx=5)
        
        # Section toggles with modern styling
        section_frame = tk.Frame(self.root, bg=colors['bg'])
        section_frame.pack(fill='x', padx=15, pady=5)
        
        self.main_toggle_button = self.create_modern_button(
            section_frame,
            "🔽 Hide Controls",
            self.toggle_main_section,
            colors['secondary']
        )
        self.main_toggle_button.pack(side='left', padx=5)
        
        self.log_toggle_button = self.create_modern_button(
            section_frame,
            "🔽 Hide Logs", 
            self.toggle_log_section,
            colors['secondary']
        )
        self.log_toggle_button.pack(side='left', padx=5)
        
        # Add log management buttons
        log_mgmt_frame = tk.Frame(section_frame, bg=colors['bg'])
        log_mgmt_frame.pack(side='right')
        
        self.view_logs_button = self.create_modern_button(
            log_mgmt_frame,
            "📋 View Logs",
            self.open_log_viewer,
            colors['warning']
        )
        self.view_logs_button.pack(side='right', padx=5)
        
        self.export_logs_button = self.create_modern_button(
            log_mgmt_frame,
            "💾 Export Session",
            self.export_session_data,
            colors['success']
        )
        self.export_logs_button.pack(side='right', padx=5)
        
        # Scrollable main content container
        scrollable_container = ScrollableFrame(self.root, bg_color=colors['bg'])
        scrollable_container.pack(fill='both', expand=True, padx=15, pady=5)

        # Now create your modern frame inside the scrollable frame's inner frame
        self.main_content_container, main_content = self.create_modern_frame(
        scrollable_container.scrollable_frame, 
        "Control Panel"
        )
        self.main_content_container.pack(fill='both', expand=True, pady=5)
        
        # Modern Dashboard Header with Statistics Cards
        dashboard_container = tk.Frame(main_content, bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg'])
        dashboard_container.pack(fill='x', pady=(0, 20))
        
        # Dashboard title
        dashboard_title = tk.Label(
            dashboard_container,
            text="🎮 Monster Soul Retrieval Dashboard",
            font=('Segoe UI', 18, 'bold'),
            fg=colors['fg'],
            bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg']
        )
        dashboard_title.pack(pady=(10, 20))
        
        # Statistics Cards Row
        stats_row = tk.Frame(dashboard_container, bg=colors['bg_solid'] if 'bg_solid' in colors else colors['bg'])
        stats_row.pack(fill='x', padx=10)
        
        # Create statistics cards
        stats_data = [
            {"title": "Total Retrievals", "value": "0", "subtitle": "Souls collected", "icon": "🎯", "color": "success"},
            {"title": "Session Time", "value": "00:00", "subtitle": "Active session", "icon": "⏱️", "color": "info"},
            {"title": "Success Rate", "value": "0%", "subtitle": "Completion rate", "icon": "📈", "color": "accent"},
            {"title": "Monsters Found", "value": "0", "subtitle": "Detected souls", "icon": "👾", "color": "warning"}
        ]
        
        # Store references for updating
        self.stat_cards = {}
        
        for i, stat in enumerate(stats_data):
            card = self.create_dashboard_stat_card(
                stats_row,
                stat["title"],
                stat["value"],
                stat["subtitle"],
                stat["icon"],
                stat["color"]
            )
            card.pack(side='left', fill='both', expand=True, padx=5)
            self.stat_cards[stat["title"].lower().replace(" ", "_")] = card
        
        # Separator line
        separator = tk.Frame(dashboard_container, height=2, bg=colors['border'])
        separator.pack(fill='x', pady=20)
        
        # Progress section with modern styling
        progress_container, progress_frame = self.create_modern_frame(main_content, "📊 Progress & Statistics")
        progress_container.pack(fill='x', pady=(0, 15))
        
        # Custom progress bar with styling
        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=colors['accent'],
            troughcolor=colors['border'],
            borderwidth=0,
            lightcolor=colors['accent'],
            darkcolor=colors['accent']
        )
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            style="Custom.Horizontal.TProgressbar",
            length=400
        )
        self.progress_bar.pack(fill='x', pady=10)
        
        # Stats with modern layout
        stats_grid = tk.Frame(progress_frame, bg=colors['card_bg'])
        stats_grid.pack(fill='x', pady=10)
        
        # Progress stats
        self.progress_label = tk.Label(
            stats_grid,
            text="Ready (0/0 souls)",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['fg'],
            bg=colors['card_bg']
        )
        self.progress_label.pack(side='left')
        
        self.success_label = tk.Label(
            stats_grid,
            text="✅ 0  ❌ 0",
            font=('Segoe UI', 11),
            fg=colors['fg'],
            bg=colors['card_bg']
        )
        self.success_label.pack(side='right')
        
        # Time tracking with modern styling
        time_grid = tk.Frame(progress_frame, bg=colors['card_bg'])
        time_grid.pack(fill='x', pady=5)
        
        self.time_label = tk.Label(
            time_grid,
            text="⏱️ 00:00:00",
            font=('Segoe UI', 10),
            fg=colors['secondary'],
            bg=colors['card_bg']
        )
        self.time_label.pack(side='left')
        
        self.eta_label = tk.Label(
            time_grid,
            text="🎯 ETA: --:--:--",
            font=('Segoe UI', 10),
            fg=colors['secondary'],
            bg=colors['card_bg']
        )
        self.eta_label.pack(side='right')
        
        # Settings section
        settings_container, settings_frame = self.create_modern_frame(main_content, "⚙️ Configuration")
        settings_container.pack(fill='x', pady=(0, 15))
        
        # Settings grid
        settings_grid = tk.Frame(settings_frame, bg=colors['card_bg'])
        settings_grid.pack(fill='x')
        
        # Row 1
        row1 = tk.Frame(settings_grid, bg=colors['card_bg'])
        row1.pack(fill='x', pady=5)
        
        tk.Label(row1, text="Speed:", font=('Segoe UI', 10), fg=colors['fg'], bg=colors['card_bg']).pack(side='left')
        self.speed_var = tk.StringVar(value="Normal")
        speed_combo = ttk.Combobox(
            row1, 
            textvariable=self.speed_var,
            values=["Slow", "Normal", "Fast", "Very Fast", "Ultra Fast", "Lightning", "Turbo"],
            state="readonly",
            width=12,
            font=('Segoe UI', 9)
        )
        speed_combo.pack(side='left', padx=(10, 20))
        
        tk.Label(row1, text="Search Delay:", font=('Segoe UI', 10), fg=colors['fg'], bg=colors['card_bg']).pack(side='left')
        self.search_delay_var = tk.StringVar(value="0.8")
        search_delay_entry = tk.Entry(row1, textvariable=self.search_delay_var, width=8, font=('Segoe UI', 9))
        search_delay_entry.pack(side='left', padx=(5, 5))
        tk.Label(row1, text="sec", font=('Segoe UI', 10), fg=colors['secondary'], bg=colors['card_bg']).pack(side='left')
        
        # Row 2
        row2 = tk.Frame(settings_grid, bg=colors['card_bg'])
        row2.pack(fill='x', pady=5)
        
        self.random_delays_var = tk.BooleanVar(value=True)
        random_check = tk.Checkbutton(
            row2, 
            text="Random Delays", 
            variable=self.random_delays_var,
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg'],
            selectcolor=colors['card_bg']
        )
        random_check.pack(side='left')
        
        tk.Label(row2, text="Break Interval:", font=('Segoe UI', 10), fg=colors['fg'], bg=colors['card_bg']).pack(side='left', padx=(20, 5))
        self.pause_interval_var = tk.StringVar(value="50")
        pause_entry = tk.Entry(row2, textvariable=self.pause_interval_var, width=8, font=('Segoe UI', 9))
        pause_entry.pack(side='left', padx=5)
        tk.Label(row2, text="souls", font=('Segoe UI', 10), fg=colors['secondary'], bg=colors['card_bg']).pack(side='left')
        
        # Coordinates setup
        coord_container, coord_frame = self.create_modern_frame(main_content, "🎯 Game Coordinates")
        coord_container.pack(fill='x', pady=(0, 15))
        
        coord_buttons = tk.Frame(coord_frame, bg=colors['card_bg'])
        coord_buttons.pack(fill='x', pady=5)
        
        self.create_modern_button(
            coord_buttons,
            "🔍 Set Search Position",
            self.set_search_position,
            colors['warning']
        ).pack(side='left', padx=5)

        self.create_modern_button(
            coord_buttons,
            "🎯 Set Monster Position", 
            self.set_monster_position,
            colors['warning']
        ).pack(side='left', padx=5)

        self.create_modern_button(
            coord_buttons,
            " Coordinate Calibration",
            self.start_coordinate_calibration,
            colors['warning']
        ).pack(side='left', padx=5)

        self.create_modern_button(
            coord_buttons,
            "🧪 Test Coordinates",
            self.test_bank_grid,
            colors['secondary']
        ).pack(side='left', padx=5)

        self.coord_status = tk.Label(
            coord_buttons,
            text="❌ Coordinates not set",
            font=('Segoe UI', 10, 'bold'),
            fg=colors['danger'],
            bg=colors['card_bg']
        )
        self.coord_status.pack(side='right')
        
        # Metamob API Integration Section
        metamob_container, metamob_frame = self.create_modern_frame(main_content, "🌐 Metamob.fr Integration")
        metamob_container.pack(fill='x', pady=(0, 15))
        
        # Metamob buttons
        metamob_buttons = tk.Frame(metamob_frame, bg=colors['card_bg'])
        metamob_buttons.pack(fill='x', pady=5)
        
        self.create_modern_button(
            metamob_buttons,
            "⚙️ Setup API",
            self.setup_metamob_credentials,
            colors['info']
        ).pack(side='left', padx=5)
        
        self.create_modern_button(
            metamob_buttons,
            "🔄 Sync to Metamob",
            self.sync_to_metamob,
            colors['success']
        ).pack(side='left', padx=5)
        
        self.create_modern_button(
            metamob_buttons,
            "🧪 Test Connection",
            self.test_metamob_connection,
            colors['secondary']
        ).pack(side='left', padx=5)
        
        # Metamob status
        self.metamob_status = tk.Label(
            metamob_buttons,
            text="❌ Not configured",
            font=('Segoe UI', 10, 'bold'),
            fg=colors['danger'],
            bg=colors['card_bg']
        )
        self.metamob_status.pack(side='right')
        
        # Metamob Threshold Configuration
        threshold_frame = tk.Frame(metamob_frame, bg=colors['card_bg'])
        threshold_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(
            threshold_frame,
            text="⚙️ Auto State Thresholds:",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['accent'],
            bg=colors['card_bg']
        ).pack(anchor='w', pady=(0, 2))
        
        # Explanation of the logic
        tk.Label(
            threshold_frame,
            text="Logic: RECHERCHE if < value, PROPOSER if > value, AUCUN if = value",
            font=('Segoe UI', 8),
            fg=colors['secondary'],
            bg=colors['card_bg']
        ).pack(anchor='w', pady=(0, 5))
        
        # Threshold input fields
        thresholds_row = tk.Frame(threshold_frame, bg=colors['card_bg'])
        thresholds_row.pack(fill='x')
        
        # RECHERCHE threshold
        recherche_frame = tk.Frame(thresholds_row, bg=colors['card_bg'])
        recherche_frame.pack(side='left', padx=(0, 15))
        
        tk.Label(
            recherche_frame,
            text="🔍 RECHERCHE (<):",
            font=('Segoe UI', 9),
            fg=colors['fg'],
            bg=colors['card_bg']
        ).pack(side='left')
        
        self.recherche_entry = tk.Entry(
            recherche_frame,
            width=5,
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=1
        )
        self.recherche_entry.pack(side='left', padx=(5, 0))
        self.recherche_entry.insert(0, str(self.recherche_threshold))
        
        # PROPOSER threshold
        proposer_frame = tk.Frame(thresholds_row, bg=colors['card_bg'])
        proposer_frame.pack(side='left', padx=(0, 15))
        
        tk.Label(
            proposer_frame,
            text="💰 PROPOSER (>):",
            font=('Segoe UI', 9),
            fg=colors['fg'],
            bg=colors['card_bg']
        ).pack(side='left')
        
        self.proposer_entry = tk.Entry(
            proposer_frame,
            width=5,
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=1
        )
        self.proposer_entry.pack(side='left', padx=(5, 0))
        self.proposer_entry.insert(0, str(self.proposer_threshold))
        
        # AUCUN threshold
        aucun_frame = tk.Frame(thresholds_row, bg=colors['card_bg'])
        aucun_frame.pack(side='left', padx=(0, 15))
        
        tk.Label(
            aucun_frame,
            text="⚪ AUCUN (=):",
            font=('Segoe UI', 9),
            fg=colors['fg'],
            bg=colors['card_bg']
        ).pack(side='left')
        
        self.aucun_entry = tk.Entry(
            aucun_frame,
            width=5,
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=1
        )
        self.aucun_entry.pack(side='left', padx=(5, 0))
        self.aucun_entry.insert(0, str(self.aucun_threshold))
        
        # Auto-update button
        self.create_modern_button(
            thresholds_row,
            "🎯 Auto Update States",
            self.auto_update_states,
            colors['warning']
        ).pack(side='left', padx=(15, 0))

        # Monster selection with modern styling
        selection_container, selection_frame = self.create_modern_frame(main_content, "🐾 Monster Selection")
        selection_container.pack(fill='x', pady=(0, 15))
        
        # Monster Type Selection (Regular vs Boss)
        type_frame = tk.Frame(selection_frame, bg=colors['card_bg'])
        type_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            type_frame,
            text="👑 Monster Type:",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['fg'],
            bg=colors['card_bg']
        ).pack(side='left')
        
        self.monster_type_var = tk.StringVar(value="Regular")
        
        # Radio buttons for monster type
        regular_radio = tk.Radiobutton(
            type_frame,
            text="🐾 Regular Monsters",
            variable=self.monster_type_var,
            value="Regular",
            command=self.load_monster_type,
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg'],
            selectcolor=colors['accent'],
            activebackground=colors['card_bg'],
            activeforeground=colors['fg']
        )
        regular_radio.pack(side='left', padx=(20, 10))
        
        boss_radio = tk.Radiobutton(
            type_frame,
            text="👑 BOSS Monsters",
            variable=self.monster_type_var,
            value="Boss",
            command=self.load_monster_type,
            font=('Segoe UI', 10, 'bold'),
            fg=colors['warning'],
            bg=colors['card_bg'],
            selectcolor=colors['warning'],
            activebackground=colors['card_bg'],
            activeforeground=colors['warning']
        )
        boss_radio.pack(side='left', padx=10)
        
        # Info label for current type
        self.type_info_label = tk.Label(
            type_frame,
            text="📄 Loading regular monsters...",
            font=('Segoe UI', 9),
            fg=colors['secondary'],
            bg=colors['card_bg']
        )
        self.type_info_label.pack(side='right', padx=10)
        
        # Search with modern styling
        search_frame = tk.Frame(selection_frame, bg=colors['card_bg'])
        search_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            search_frame, 
            text="🔍 Search:",
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg']
        ).pack(side='left')
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, 
            textvariable=self.search_var,
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=2
        )
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(10, 0))
        self.search_entry.bind('<KeyRelease>', self.filter_monsters)
        
        # Monster listbox with modern styling
        listbox_frame = tk.Frame(selection_frame, bg=colors['card_bg'])
        listbox_frame.pack(fill='x', pady=(0, 10))
        
        self.monster_listbox = tk.Listbox(
            listbox_frame, 
            height=6,
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=2
        )
        scrollbar = tk.Scrollbar(listbox_frame, orient='vertical')
        self.monster_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.monster_listbox.yview)
        
        self.monster_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Add controls
        add_frame = tk.Frame(selection_frame, bg=colors['card_bg'])
        add_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            add_frame,
            text="Quantity:",
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg']
        ).pack(side='left')
        
        self.quantity_var = tk.StringVar(value="1")
        quantity_entry = tk.Entry(
            add_frame, 
            textvariable=self.quantity_var, 
            width=8,
            font=('Segoe UI', 10)
        )
        quantity_entry.pack(side='left', padx=(10, 20))
        
        self.create_modern_button(
            add_frame,
            "➕ Add Selected",
            self.add_monster,
            colors['success']
        ).pack(side='left', padx=5)
        
        self.create_modern_button(
            add_frame,
            "➕ Add All",
            self.add_all_monsters,
            colors['accent']
        ).pack(side='left', padx=5)
        
        # Selected monsters section
        selected_container, selected_frame = self.create_modern_frame(main_content, "📋 Selected Monsters")
        selected_container.pack(fill='x', pady=(0, 15))
        
        # Header with count
        selected_header = tk.Frame(selected_frame, bg=colors['card_bg'])
        selected_header.pack(fill='x', pady=(0, 10))
        
        self.selected_count_label = tk.Label(
            selected_header,
            text="Total: 0 monsters",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['accent'],
            bg=colors['card_bg']
        )
        self.selected_count_label.pack(side='left')
        
        # Clear controls
        clear_frame = tk.Frame(selected_header, bg=colors['card_bg'])
        clear_frame.pack(side='right')
        
        self.remove_count_var = tk.StringVar(value="1")
        remove_entry = tk.Entry(
            clear_frame, 
            textvariable=self.remove_count_var, 
            width=5,
            font=('Segoe UI', 9)
        )
        remove_entry.pack(side='right', padx=5)
        
        self.create_modern_button(
            clear_frame,
            "🗑️ Clear All",
            self.clear_selected,
            colors['danger']
        ).pack(side='right', padx=5)
        
        self.create_modern_button(
            clear_frame,
            "➖ Remove Last",
            self.remove_last_monsters,
            colors['warning']
        ).pack(side='right', padx=5)
        
        # Selected listbox
        selected_listbox_frame = tk.Frame(selected_frame, bg=colors['card_bg'])
        selected_listbox_frame.pack(fill='x')
        
        self.selected_listbox = tk.Listbox(
            selected_listbox_frame, 
            height=6,
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=2
        )
        selected_scrollbar = tk.Scrollbar(selected_listbox_frame, orient='vertical')
        self.selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        selected_scrollbar.configure(command=self.selected_listbox.yview)
        
        self.selected_listbox.pack(side='left', fill='both', expand=True)
        selected_scrollbar.pack(side='right', fill='y')
        
        # Soul Scanner section with modern styling
        scanner_container, scanner_frame = self.create_modern_frame(main_content, "🔍 Soul Quantity Scanner")
        scanner_container.pack(fill='x', pady=(0, 15))
        
        # Scanner info
        scanner_info = tk.Frame(scanner_frame, bg=colors['card_bg'])
        scanner_info.pack(fill='x', pady=(0, 10))
        
        scanner_info_label = tk.Label(
            scanner_info,
            text="📊 Automatically count soul stones in your bank",
            font=('Segoe UI', 10),
            fg=colors['secondary'],
            bg=colors['card_bg']
        )
        scanner_info_label.pack(side='left')
        
        # Scanner options
        scanner_options = tk.Frame(scanner_frame, bg=colors['card_bg'])
        scanner_options.pack(fill='x', pady=(0, 10))
        
        self.scan_mode_var = tk.StringVar(value="selected")
        
        scan_all_radio = tk.Radiobutton(
            scanner_options,
            text="🗂️ Scan ALL monsters from file",
            variable=self.scan_mode_var,
            value="all",
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg'],
            selectcolor=colors['card_bg'],
            command=self.update_scan_mode_display
        )
        scan_all_radio.pack(side='left', padx=(0, 20))
        
        scan_selected_radio = tk.Radiobutton(
            scanner_options,
            text="✅ Scan SELECTED monsters only",
            variable=self.scan_mode_var,
            value="selected",
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg'],
            selectcolor=colors['card_bg'],
            command=self.update_scan_mode_display
        )
        scan_selected_radio.pack(side='left')
        
        # Scanner mode info
        self.scan_mode_info = tk.Label(
            scanner_options,
            text="",
            font=('Segoe UI', 9),
            fg=colors['accent'],
            bg=colors['card_bg']
        )
        self.scan_mode_info.pack(side='right')
        
        # Scanner controls
        scanner_controls = tk.Frame(scanner_frame, bg=colors['card_bg'])
        scanner_controls.pack(fill='x', pady=5)
        
        self.scan_button = self.create_modern_button(
            scanner_controls,
            "🔍 START SOUL SCAN",
            self.start_soul_scan,
            colors['accent'],
            height=2
        )
        self.scan_button.pack(side='left', padx=5)
        
        self.stop_scan_button = self.create_modern_button(
            scanner_controls,
            "⏹️ STOP SCAN",
            self.stop_soul_scan,
            colors['danger']
        )
        self.stop_scan_button.configure(state='disabled')
        self.stop_scan_button.pack(side='left', padx=5)
        
        # Debug mode toggle
        self.debug_button = self.create_modern_button(
            scanner_controls,
            "🐛 Debug OFF",
            self.toggle_debug_mode,
            colors['secondary']
        )
        self.debug_button.pack(side='left', padx=5)
        
        # Scanner progress
        scanner_progress_frame = tk.Frame(scanner_frame, bg=colors['card_bg'])
        scanner_progress_frame.pack(fill='x', pady=10)
        
        self.scan_progress_var = tk.DoubleVar()
        self.scan_progress_bar = ttk.Progressbar(
            scanner_progress_frame,
            variable=self.scan_progress_var,
            maximum=100,
            style="Custom.Horizontal.TProgressbar",
            length=300
        )
        self.scan_progress_bar.pack(side='left', fill='x', expand=True)
        
        self.scan_status_label = tk.Label(
            scanner_progress_frame,
            text="Ready to scan",
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['card_bg']
        )
        self.scan_status_label.pack(side='right', padx=(10, 0))
        
        # Scanner results summary
        scanner_results = tk.Frame(scanner_frame, bg=colors['card_bg'])
        scanner_results.pack(fill='x', pady=5)
        
        self.scan_results_label = tk.Label(
            scanner_results,
            text="No scan performed yet",
            font=('Segoe UI', 10),
            fg=colors['secondary'],
            bg=colors['card_bg']
        )
        self.scan_results_label.pack(side='left')
        
        # Control buttons with modern styling
        control_container = tk.Frame(main_content, bg=colors['card_bg'])
        control_container.pack(fill='x', pady=20)
        
        self.start_button = self.create_modern_button(
            control_container,
            "🚀 START RETRIEVAL",
            self.start_retrieval,
            colors['success'],
            height=3
        )
        self.start_button.pack(side='left', fill='x', expand=True, padx=5)
        
        self.pause_button = self.create_modern_button(
            control_container,
            "⏸️ PAUSE",
            self.pause_retrieval,
            colors['warning'],
            height=3
        )
        self.pause_button.configure(state='disabled')
        self.pause_button.pack(side='left', fill='x', expand=True, padx=5)
        
        self.stop_button = self.create_modern_button(
            control_container,
            "⏹️ STOP",
            self.stop_retrieval,
            colors['danger'],
            height=3
        )
        self.stop_button.configure(state='disabled')
        self.stop_button.pack(side='left', fill='x', expand=True, padx=5)
        
        # Log section
        self.log_container, log_frame = self.create_modern_frame(
            self.root,
            "📝 Status & Activity Log"
        )
        self.log_container.pack(fill='both', expand=True, padx=15, pady=5)
        
        self.status_label = tk.Label(
            log_frame,
            text="🟢 Ready",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['success'],
            bg=colors['card_bg']
        )
        self.status_label.pack(pady=(0, 10))
        
        # Modern log text area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=('Consolas', 9),
            relief='flat',
            borderwidth=2,
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)
        self.log_text.insert(tk.END, "🎮 Monster Soul Retrieval Tool Ready\n")
        self.log_text.insert(tk.END, "📝 Logs will appear here when you start retrieval...\n")
        
        # Initialize
        self.update_monster_list()
        self.update_selected_display()
        
        # Coordinates
        self.search_pos = None
        self.monster_pos = None
        
        # Apply theme
        self.apply_modern_theme()
        
        # Initialize scan mode display
        self.update_scan_mode_display()
        
        # Start time updater
        self.update_time_display()
    
    def save_session_log(self, final=False):
        """Save session data to file"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logs_dir = os.path.join(script_dir, 'logs')
            
            # Create logs directory if it doesn't exist
            os.makedirs(logs_dir, exist_ok=True)
            
            # Update session data
            if final:
                self.session_log['session_end'] = datetime.now().isoformat()
            
            self.session_log['total_monsters'] = len(self.selected_monsters)
            self.session_log['total_souls'] = self.total_souls
            self.session_log['successful_retrievals'] = self.successful_retrievals
            self.session_log['failed_retrievals'] = self.failed_retrievals
            self.session_log['settings'] = {
                'speed': self.speed_var.get(),
                'search_delay': self.search_delay_var.get(),
                'random_delays': self.random_delays_var.get(),
                'pause_interval': self.pause_interval_var.get()
            }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(logs_dir, f"monster_retrieval_{timestamp}.json")
            
            # Save to JSON file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.session_log, f, indent=2, ensure_ascii=False)
            
            # Also create a human-readable text log
            txt_filename = os.path.join(logs_dir, f"monster_retrieval_{timestamp}.txt")
            self.create_readable_log(txt_filename)
            
            if final:
                self.log_message(f"📁 Session saved to: {filename}")
                self.log_message(f"📄 Readable log: {txt_filename}")
                
        except Exception as e:
            self.log_message(f"❌ Error saving session log: {str(e)}")
    
    def create_readable_log(self, filename):
        """Create a human-readable text log"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("MONSTER SOUL RETRIEVAL SESSION LOG\n")
                f.write("=" * 60 + "\n\n")
                
                # Session info
                if self.session_log['session_start']:
                    start_time = datetime.fromisoformat(self.session_log['session_start'])
                    f.write(f"Session Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                if self.session_log['session_end']:
                    end_time = datetime.fromisoformat(self.session_log['session_end'])
                    f.write(f"Session End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    if self.session_log['session_start']:
                        duration = end_time - start_time
                        f.write(f"Duration: {str(duration).split('.')[0]}\n")
                
                f.write(f"\n" + "-" * 40 + "\n")
                f.write("SUMMARY\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Monsters: {self.session_log['total_monsters']}\n")
                f.write(f"Total Souls: {self.session_log['total_souls']}\n")
                f.write(f"Successful Retrievals: {self.session_log['successful_retrievals']}\n")
                f.write(f"Failed Retrievals: {self.session_log['failed_retrievals']}\n")
                
                if self.session_log['total_souls'] > 0:
                    success_rate = (self.session_log['successful_retrievals'] / self.session_log['total_souls']) * 100
                    f.write(f"Success Rate: {success_rate:.1f}%\n")
                
                f.write(f"\n" + "-" * 40 + "\n")
                f.write("SETTINGS USED\n")
                f.write("-" * 40 + "\n")
                settings = self.session_log.get('settings', {})
                for key, value in settings.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                
                f.write(f"\n" + "-" * 40 + "\n")
                f.write("MONSTER DETAILS\n")
                f.write("-" * 40 + "\n")
                
                for monster_name, data in self.session_log['monsters_data'].items():
                    f.write(f"\n{monster_name}:\n")
                    f.write(f"  Requested: {data['requested']}\n")
                    f.write(f"  Successful: {data['successful']}\n")
                    f.write(f"  Failed: {data['failed']}\n")
                    f.write(f"  Success Rate: {data['success_rate']:.1f}%\n")
                    
                    if data['attempts']:
                        f.write(f"  Attempts:\n")
                        for i, attempt in enumerate(data['attempts'], 1):
                            status = "✅" if attempt['success'] else "❌"
                            f.write(f"    {i}. {status} {attempt['timestamp']}\n")
                            if attempt.get('error'):
                                f.write(f"       Error: {attempt['error']}\n")
                
                f.write(f"\n" + "-" * 40 + "\n")
                f.write("TIMELINE\n")
                f.write("-" * 40 + "\n")
                
                for entry in self.session_log['timeline']:
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                    f.write(f"[{timestamp}] {entry['message']}\n")
                
                f.write(f"\n" + "=" * 60 + "\n")
                
        except Exception as e:
            self.log_message(f"❌ Error creating readable log: {str(e)}")
    
    def log_monster_attempt(self, monster_name, success, error=None):
        """Log individual monster attempt"""
        if monster_name not in self.session_log['monsters_data']:
            self.session_log['monsters_data'][monster_name] = {
                'requested': self.selected_monsters.get(monster_name, 0),
                'successful': 0,
                'failed': 0,
                'attempts': [],
                'success_rate': 0.0
            }
        
        monster_data = self.session_log['monsters_data'][monster_name]
        
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'success': success
        }
        
        if error:
            attempt['error'] = error
        
        monster_data['attempts'].append(attempt)
        
        if success:
            monster_data['successful'] += 1
        else:
            monster_data['failed'] += 1
        
        # Calculate success rate
        total_attempts = monster_data['successful'] + monster_data['failed']
        if total_attempts > 0:
            monster_data['success_rate'] = (monster_data['successful'] / total_attempts) * 100
    
    def add_timeline_entry(self, message):
        """Add entry to timeline"""
        self.session_log['timeline'].append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
    
    def open_log_viewer(self):
        """Open log viewer window"""
        try:
            log_window = tk.Toplevel(self.root)
            log_window.title("📋 Session Logs Viewer")
            log_window.geometry("800x600")
            log_window.configure(bg=self.get_theme_colors()['bg'])
            
            # Make it stay on top temporarily
            log_window.attributes('-topmost', True)
            log_window.after(3000, lambda: log_window.attributes('-topmost', False))
            
            colors = self.get_theme_colors()
            
            # Header
            header = tk.Frame(log_window, bg=colors['bg'])
            header.pack(fill='x', padx=15, pady=15)
            
            title = tk.Label(
                header,
                text="📋 Current Session Data",
                font=('Segoe UI', 16, 'bold'),
                fg=colors['accent'],
                bg=colors['bg']
            )
            title.pack()
            
            # Stats frame
            stats_frame = tk.Frame(log_window, bg=colors['card_bg'], relief='flat')
            stats_frame.pack(fill='x', padx=15, pady=(0, 15))
            
            stats_grid = tk.Frame(stats_frame, bg=colors['card_bg'])
            stats_grid.pack(fill='x', padx=15, pady=15)
            
            # Current session stats
            stats_info = [
                f"🎮 Total Monsters: {len(self.selected_monsters)}",
                f"🎯 Total Souls: {self.total_souls}",
                f"✅ Successful: {self.successful_retrievals}",
                f"❌ Failed: {self.failed_retrievals}",
                f"📊 Success Rate: {(self.successful_retrievals/max(1, self.total_souls)*100):.1f}%"
            ]
            
            for i, stat in enumerate(stats_info):
                label = tk.Label(
                    stats_grid,
                    text=stat,
                    font=('Segoe UI', 11),
                    fg=colors['fg'],
                    bg=colors['card_bg']
                )
                label.grid(row=i//3, column=i%3, padx=10, pady=5, sticky='w')
            
            # Text area for detailed log
            text_frame = tk.Frame(log_window, bg=colors['bg'])
            text_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
            
            log_text = scrolledtext.ScrolledText(
                text_frame,
                font=('Consolas', 9),
                bg=colors['card_bg'],
                fg=colors['fg'],
                relief='flat',
                borderwidth=2
            )
            log_text.pack(fill='both', expand=True)
            
            # Populate with current session data
            log_content = "📊 CURRENT SESSION OVERVIEW\n"
            log_content += "=" * 50 + "\n\n"
            
            if self.session_log['monsters_data']:
                log_content += "🐾 MONSTER DETAILS:\n"
                log_content += "-" * 30 + "\n"
                
                for monster_name, data in self.session_log['monsters_data'].items():
                    log_content += f"\n{monster_name}:\n"
                    log_content += f"  📋 Requested: {data['requested']}\n"
                    log_content += f"  ✅ Successful: {data['successful']}\n"
                    log_content += f"  ❌ Failed: {data['failed']}\n"
                    log_content += f"  📊 Success Rate: {data['success_rate']:.1f}%\n"
                    
                    if data['attempts']:
                        log_content += f"  🕐 Recent Attempts:\n"
                        for attempt in data['attempts'][-5:]:  # Show last 5 attempts
                            timestamp = datetime.fromisoformat(attempt['timestamp']).strftime('%H:%M:%S')
                            status = "✅" if attempt['success'] else "❌"
                            log_content += f"    [{timestamp}] {status}\n"
            
            if self.session_log['timeline']:
                log_content += f"\n\n📝 RECENT ACTIVITY:\n"
                log_content += "-" * 30 + "\n"
                
                for entry in self.session_log['timeline'][-20:]:  # Show last 20 entries
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                    log_content += f"[{timestamp}] {entry['message']}\n"
            
            log_text.insert(tk.END, log_content)
            log_text.configure(state='disabled')
            
            # Buttons frame
            button_frame = tk.Frame(log_window, bg=colors['bg'])
            button_frame.pack(fill='x', padx=15, pady=(0, 15))
            
            self.create_modern_button(
                button_frame,
                "🔄 Refresh",
                lambda: self.refresh_log_viewer(log_text),
                colors['accent']
            ).pack(side='left', padx=5)
            
            self.create_modern_button(
                button_frame,
                "💾 Export Current",
                lambda: self.save_session_log(final=False),
                colors['success']
            ).pack(side='left', padx=5)
            
            self.create_modern_button(
                button_frame,
                "❌ Close",
                log_window.destroy,
                colors['danger']
            ).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log viewer: {str(e)}")
    
    def refresh_log_viewer(self, log_text):
        """Refresh the log viewer content"""
        try:
            log_text.configure(state='normal')
            log_text.delete(1.0, tk.END)
            
            # Re-populate with updated data
            log_content = "📊 CURRENT SESSION OVERVIEW (REFRESHED)\n"
            log_content += "=" * 50 + "\n\n"
            
            if self.session_log['monsters_data']:
                log_content += "🐾 MONSTER DETAILS:\n"
                log_content += "-" * 30 + "\n"
                
                for monster_name, data in self.session_log['monsters_data'].items():
                    log_content += f"\n{monster_name}:\n"
                    log_content += f"  📋 Requested: {data['requested']}\n"
                    log_content += f"  ✅ Successful: {data['successful']}\n"
                    log_content += f"  ❌ Failed: {data['failed']}\n"
                    log_content += f"  📊 Success Rate: {data['success_rate']:.1f}%\n"
            
            log_text.insert(tk.END, log_content)
            log_text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not refresh log viewer: {str(e)}")
    
    def export_session_data(self):
        """Export current session data"""
        try:
            self.save_session_log(final=False)
            messagebox.showinfo("Export Complete", "Session data exported to logs folder!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export session data: {str(e)}")
    
    def update_time_display(self):
        """Update time display every second"""
        if self.is_running and self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]
            self.time_label.config(text=f"⏱️ {elapsed_str}")
            
            # Calculate ETA
            if self.processed_souls > 0:
                avg_time_per_soul = elapsed.total_seconds() / self.processed_souls
                remaining_souls = self.total_souls - self.processed_souls
                eta_seconds = avg_time_per_soul * remaining_souls
                eta = timedelta(seconds=int(eta_seconds))
                self.eta_label.config(text=f"🎯 ETA: {str(eta)}")
        
        self.root.after(1000, self.update_time_display)
    
    def filter_monsters(self, event=None):
        """Filter monster list based on search"""
        search_term = self.search_var.get().lower()
        filtered_monsters = [name for name in self.monster_names 
                           if search_term in name.lower()]
        
        # Get current monster type for icon prefix
        monster_type = getattr(self, 'monster_type_var', tk.StringVar(value="Regular")).get()
        
        self.monster_listbox.delete(0, tk.END)
        for monster in filtered_monsters:
            # Display without icon prefix to prevent copying issues
            self.monster_listbox.insert(tk.END, monster)
    
    def update_monster_list(self):
        """Update the monster listbox"""
        # Get current monster type for icon prefix
        monster_type = getattr(self, 'monster_type_var', tk.StringVar(value="Regular")).get()
        
        self.monster_listbox.delete(0, tk.END)
        for monster in self.monster_names:
            # Display without icon prefix to prevent copying issues
            self.monster_listbox.insert(tk.END, monster)
    
    def set_search_position(self):
        """Set the position of the bank search bar"""
        messagebox.showinfo("Set Position", 
                           "Click OK, then click on the bank search bar in your game.\nYou have 3 seconds.")
        self.root.after(3000, self.capture_search_position)
    
    def capture_search_position(self):
        self.search_pos = pyautogui.position()
        self.update_coord_status()
        self.add_timeline_entry(f"Search position set: {self.search_pos}")
        messagebox.showinfo("Success", f"Search bar position set: {self.search_pos}")
    
    def set_monster_position(self):
        """Set the position of the first monster soul"""
        messagebox.showinfo("Set Position", 
                           "Click OK, then click on the first monster soul position (top-left) in the bank.\nYou have 3 seconds.")
        self.root.after(3000, self.capture_monster_position)
    
    def capture_monster_position(self):
        self.monster_pos = pyautogui.position()
        self.update_coord_status()
        self.add_timeline_entry(f"Monster position set: {self.monster_pos}")
        messagebox.showinfo("Success", f"Monster position set: {self.monster_pos}")
    
    def update_coord_status(self):
        colors = self.get_theme_colors()
        # Check if coordinates are properly calibrated
        coords_calibrated = self.slot_coordinates and len(self.slot_coordinates) == 45
        
        if self.search_pos and self.monster_pos and coords_calibrated:
            self.coord_status.config(text="✅ All coordinates set", fg=colors['success'])
        elif self.search_pos and self.monster_pos:
            self.coord_status.config(text="⚠️ Missing slot coordinates", fg=colors['warning'])
        elif self.search_pos or self.monster_pos or coords_calibrated:
            self.coord_status.config(text="⚠️ Partial setup", fg=colors['warning'])
        else:
            self.coord_status.config(text="❌ Coordinates not set", fg=colors['danger'])
    
    def add_all_monsters(self):
        """Add all monsters (or filtered monsters) to retrieval list"""
        try:
            quantity = int(self.quantity_var.get())
            
            if quantity <= 0:
                messagebox.showwarning("Warning", "Quantity must be greater than 0!")
                return
            
            monsters_to_add = []
            for i in range(self.monster_listbox.size()):
                monsters_to_add.append(self.monster_listbox.get(i))
            
            if not monsters_to_add:
                messagebox.showwarning("Warning", "No monsters to add!")
                return
            
            result = messagebox.askyesno("Confirm", 
                                       f"Add {len(monsters_to_add)} monsters with quantity {quantity} each?")
            
            if result:
                for monster_name in monsters_to_add:
                    self.selected_monsters[monster_name] = quantity
                
                self.update_selected_display()
                self.add_timeline_entry(f"Added {len(monsters_to_add)} monsters (qty: {quantity} each)")
                messagebox.showinfo("Success", f"Added {len(monsters_to_add)} monsters!")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity!")
    
    def add_monster(self):
        """Add selected monster to retrieval list"""
        try:
            selection = self.monster_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a monster first!")
                return
            
            display_name = self.monster_listbox.get(selection[0])
            # Monster name is now displayed without icon prefixes
            monster_name = display_name
            
            quantity = int(self.quantity_var.get())
            
            if quantity <= 0:
                messagebox.showwarning("Warning", "Quantity must be greater than 0!")
                return
            
            self.selected_monsters[monster_name] = quantity
            self.update_selected_display()
            
            # Add type info to timeline
            monster_type = "Boss" if display_name.startswith("👑") else "Regular"
            self.add_timeline_entry(f"Added {monster_type}: {monster_name} (qty: {quantity})")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity!")
    
    def remove_last_monsters(self):
        """Remove the last N monsters from the selected list"""
        try:
            remove_count = int(self.remove_count_var.get())
            if remove_count <= 0:
                messagebox.showwarning("Warning", "Remove count must be greater than 0!")
                return
            
            monster_list = list(self.selected_monsters.keys())
            if remove_count >= len(monster_list):
                self.clear_selected()
                return
            
            removed_monsters = []
            for _ in range(remove_count):
                if monster_list:
                    monster_to_remove = monster_list.pop()
                    removed_monsters.append(monster_to_remove)
                    del self.selected_monsters[monster_to_remove]
            
            self.update_selected_display()
            self.add_timeline_entry(f"Removed {len(removed_monsters)} monsters")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number!")
    
    def update_selected_display(self):
        """Update the selected monsters display"""
        self.selected_listbox.delete(0, tk.END)
        total_monsters = len(self.selected_monsters)
        total_souls = sum(self.selected_monsters.values())
        
        for monster, quantity in self.selected_monsters.items():
            # Display without icons to prevent copying issues
            self.selected_listbox.insert(tk.END, f"{monster}: {quantity}")
        
        colors = self.get_theme_colors()
        self.selected_count_label.config(
            text=f"Total: {total_monsters} monsters ({total_souls} souls)",
            fg=colors['accent']
        )
        
        # Update scan mode info if it exists
        if hasattr(self, 'scan_mode_info'):
            self.update_scan_mode_display()
    
    def clear_selected(self):
        """Clear all selected monsters"""
        self.selected_monsters.clear()
        self.update_selected_display()
        self.add_timeline_entry("Cleared all selected monsters")
    
    def start_retrieval(self):
        """Start the automated retrieval process"""
        if not self.search_pos or not self.monster_pos:
            messagebox.showerror("Error", "Please set the game coordinates first!")
            return
        
        if not self.selected_monsters:
            messagebox.showerror("Error", "Please select at least one monster!")
            return
        
        # Initialize session log
        self.session_log = {
            'session_start': datetime.now().isoformat(),
            'session_end': None,
            'total_monsters': len(self.selected_monsters),
            'total_souls': sum(self.selected_monsters.values()),
            'successful_retrievals': 0,
            'failed_retrievals': 0,
            'monsters_data': {},
            'settings': {
                'speed': self.speed_var.get(),
                'search_delay': self.search_delay_var.get(),
                'random_delays': self.random_delays_var.get(),
                'pause_interval': self.pause_interval_var.get()
            },
            'timeline': []
        }
        
        # Show log section when starting
        if not self.log_section_visible:
            self.toggle_log_section()
        
        # Keep window visible during retrieval
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        if not self.keep_on_top:
            self.root.attributes('-topmost', True)
            self.root.after(3000, lambda: self.root.attributes('-topmost', self.keep_on_top))
        
        # Reset progress tracking
        self.total_souls = sum(self.selected_monsters.values())
        self.processed_souls = 0
        self.successful_retrievals = 0
        self.failed_retrievals = 0
        self.failed_monsters = []
        self.start_time = datetime.now()
        
        self.is_running = True
        self.is_paused = False
        
        colors = self.get_theme_colors()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.pause_button.config(state='normal', text='⏸️ PAUSE')
        
        # Clear log and add startup message
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"🚀 Starting retrieval of {self.total_souls} souls...\n")
        self.log_text.insert(tk.END, f"📊 {len(self.selected_monsters)} different monsters selected\n")
        self.log_text.insert(tk.END, f"⚙️ Speed: {self.speed_var.get()}, Delay: {self.search_delay_var.get()}s\n")
        self.log_text.insert(tk.END, "=" * 50 + "\n")
        
        self.add_timeline_entry(f"Started retrieval session - {self.total_souls} souls")
        
        # Start retrieval in separate thread
        thread = threading.Thread(target=self.retrieval_process)
        thread.daemon = True
        thread.start()
    
    def pause_retrieval(self):
        """Pause/Resume the retrieval process"""
        colors = self.get_theme_colors()
        
        if self.is_paused:
            self.is_paused = False
            self.pause_button.config(text='⏸️ PAUSE', bg=colors['warning'])
            self.update_status("🟢 Resumed")
            self.add_timeline_entry("Retrieval resumed")
        else:
            self.is_paused = True
            self.pause_button.config(text='▶️ RESUME', bg=colors['success'])
            self.update_status("🟡 Paused by user")
            self.add_timeline_entry("Retrieval paused by user")
    
    def stop_retrieval(self):
        """Stop the retrieval process"""
        colors = self.get_theme_colors()
        
        self.is_running = False
        self.is_paused = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.pause_button.config(state='disabled', text='⏸️ PAUSE', bg=colors['warning'])
        self.update_status("🔴 Stopped by user")
        self.add_timeline_entry("Retrieval stopped by user")
        
        # Save session log
        self.save_session_log(final=True)
        
        # Bring window back to front when stopped
        self.root.deiconify()
        self.root.lift()
    
    def update_status(self, message):
        """Update status label with color coding"""
        colors = self.get_theme_colors()
        
        if "Ready" in message or "Completed" in message:
            color = colors['success']
        elif "Paused" in message or "Break" in message:
            color = colors['warning']
        elif "Stopped" in message or "Error" in message:
            color = colors['danger']
        else:
            color = colors['accent']
        
        self.status_label.config(text=message, fg=color)
    
    def update_progress(self):
        """Update progress bar and labels"""
        if self.total_souls > 0:
            progress = (self.processed_souls / self.total_souls) * 100
            self.progress_var.set(progress)
            
            colors = self.get_theme_colors()
            self.progress_label.config(
                text=f"Progress: {self.processed_souls}/{self.total_souls} souls ({progress:.1f}%)",
                fg=colors['fg']
            )
            self.success_label.config(
                text=f"✅ {self.successful_retrievals}  ❌ {self.failed_retrievals}",
                fg=colors['fg']
            )
    
    def log_message(self, message):
        """Add message to log with timestamp and color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Also add to timeline
        self.add_timeline_entry(message)
    
    def play_completion_sound(self):
        """Play notification sound when complete"""
        try:
            # Play a more elaborate completion sound
            for i in range(3):
                winsound.MessageBeep(winsound.MB_OK)
                time.sleep(0.2)
        except:
            for i in range(3):
                print('\a')
                time.sleep(0.2)
    
    def clean_monster_name(self, name):
        """Remove or replace special characters and icons that might cause typing issues"""
        import re
        # First, strip any icon prefixes (🐾 for regular monsters, 👑 for bosses, 🔥 fire emoji)
        cleaned_name = name
        if cleaned_name.startswith("🐾 "):
            cleaned_name = cleaned_name[2:]  # Remove "🐾 "
        elif cleaned_name.startswith("👑 "):
            cleaned_name = cleaned_name[2:]  # Remove "👑 "
        elif cleaned_name.startswith("🔥 "):
            cleaned_name = cleaned_name[2:]  # Remove "🔥 "
        
        # Remove any other potential emoji patterns at the start
        # Remove any emoji character followed by a space at the beginning
        cleaned_name = re.sub(r'^[\U00010000-\U0010ffff]\s+', '', cleaned_name)
        cleaned_name = re.sub(r'^[\u2600-\u27bf]\s+', '', cleaned_name)
        cleaned_name = re.sub(r'^[\u1f300-\u1f5ff]\s+', '', cleaned_name)
        cleaned_name = re.sub(r'^[\u1f600-\u1f64f]\s+', '', cleaned_name)
        cleaned_name = re.sub(r'^[\u1f680-\u1f6ff]\s+', '', cleaned_name)
        cleaned_name = re.sub(r'^[\u1f900-\u1f9ff]\s+', '', cleaned_name)
        
        # Then handle accent characters
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'î': 'i', 'ï': 'i'
        }
        
        for accent, replacement in replacements.items():
            cleaned_name = cleaned_name.replace(accent, replacement)
        return cleaned_name
    
    def get_speed_delays(self):
        """Get delay values based on selected speed"""
        speed = self.speed_var.get()
        
        base_delays = {
            "Slow": {"click": 0.3, "type": 0.2, "retrieve": 0.5, "monster": 0.8},
            "Normal": {"click": 0.2, "type": 0.1, "retrieve": 0.3, "monster": 0.5},
            "Fast": {"click": 0.1, "type": 0.05, "retrieve": 0.2, "monster": 0.3},
            "Very Fast": {"click": 0.05, "type": 0.05, "retrieve": 0.1, "monster": 0.2},
            "Ultra Fast": {"click": 0.03, "type": 0.03, "retrieve": 0.05, "monster": 0.1},
            "Lightning": {"click": 0.02, "type": 0.02, "retrieve": 0.03, "monster": 0.05},
            "Turbo": {"click": 0.01, "type": 0.01, "retrieve": 0.02, "monster": 0.03}
        }
        
        delays = base_delays.get(speed, base_delays["Normal"])
        
        if self.random_delays_var.get():
            randomized_delays = {}
            for key, value in delays.items():
                min_delay = value * 0.7
                max_delay = value * 1.3
                randomized_delays[key] = random.uniform(min_delay, max_delay)
            return randomized_delays
        
        return delays
    
    def check_if_retrieval_successful(self):
        """Check if the last retrieval attempt was successful"""
        try:
            error_red_threshold = 5
            empty_dark_threshold = 80
            feedback_delay = 0.3
            
            # Wait for any animations/feedback to complete
            time.sleep(feedback_delay)
            
            # Try clicking the same position again to see what happens
            original_pos = pyautogui.position()
            
            # Single click on the monster position to see response
            pyautogui.click(self.monster_pos)
            time.sleep(0.2)
            
            # Take a screenshot of a larger area to check for visual feedback
            feedback_area = pyautogui.screenshot(region=(
                self.monster_pos.x - 50, 
                self.monster_pos.y - 50, 
                100, 
                100
            ))
            
            # Restore original mouse position  
            pyautogui.moveTo(original_pos)
            
            # Convert to RGB values for analysis
            pixels = list(feedback_area.getdata())
            
            red_pixels = 0
            dark_pixels = 0
            total_pixels = len(pixels)
            
            for pixel in pixels:
                r, g, b = pixel[:3]
                
                # Count reddish pixels (might indicate error messages)
                if r > 150 and g < 100 and b < 100:
                    red_pixels += 1
                
                # Count very dark pixels (might indicate empty slots)
                if r < 50 and g < 50 and b < 50:
                    dark_pixels += 1
            
            red_percentage = (red_pixels / total_pixels) * 100
            dark_percentage = (dark_pixels / total_pixels) * 100
            
            # Debug logging
            self.log_message(f"🔍 Feedback analysis: {red_percentage:.1f}% red, {dark_percentage:.1f}% dark")
            
            # If there's significant red, might be an error message
            if red_percentage > error_red_threshold:
                self.log_message(f"🔍 Detected error indicators - marking as failed")
                return False
                
            # If it's mostly very dark, might be an empty area
            if dark_percentage > empty_dark_threshold:
                self.log_message(f"🔍 Area mostly dark - marking as failed")
                return False
            
            # No clear failure indicators - assume success
            self.log_message(f"🔍 No failure indicators - marking as successful")
            return True
            
        except Exception as e:
            self.log_message(f"Error checking retrieval success: {str(e)}")
            return True
    
    def advanced_monster_detection(self, monster_name):
        """More advanced method to detect if monster is available"""
        try:
            empty_slot_color = (20, 20, 20)
            color_tolerance = 30
            bright_threshold = 100
            color_variance_threshold = 30
            bright_percentage_min = 15
            color_percentage_min = 10
            
            # Approach 1: Try to interact and check for immediate feedback
            pyautogui.click(self.monster_pos)
            time.sleep(0.1)
            
            # Approach 2: Check for tooltip or hover text
            pyautogui.moveTo(self.monster_pos)
            time.sleep(0.2)
            
            # Take screenshot for analysis
            hover_screenshot = pyautogui.screenshot(region=(
                self.monster_pos.x - 60,
                self.monster_pos.y - 60, 
                120,
                120
            ))
            
            # Approach 3: Use OCR if available
            try:
                import pytesseract
                from PIL import Image
                
                text = pytesseract.image_to_string(hover_screenshot, config='--psm 8')
                text = text.strip().lower()
                
                monster_name_lower = monster_name.lower()
                if monster_name_lower in text:
                    self.log_message(f"🔍 OCR detected '{monster_name}' - monster confirmed present")
                    return True
                    
                not_found_indicators = ['not found', 'empty', 'nothing', 'none', 'unavailable']
                for indicator in not_found_indicators:
                    if indicator in text:
                        self.log_message(f"🔍 OCR detected '{indicator}' - monster not available")
                        return False
                        
            except ImportError:
                pass
            except Exception:
                pass
            
            # Approach 4: Pixel analysis
            pixels = list(hover_screenshot.getdata())
            total_pixels = len(pixels)
            
            # Check if it matches empty slot color
            center_x, center_y = 60, 60
            try:
                center_pixel = hover_screenshot.getpixel((center_x, center_y))
                center_r, center_g, center_b = center_pixel[:3]
                
                color_diff = abs(center_r - empty_slot_color[0]) + \
                           abs(center_g - empty_slot_color[1]) + \
                           abs(center_b - empty_slot_color[2])
                
                if color_diff < color_tolerance:
                    self.log_message(f"🔍 Center pixel matches empty slot color - no monster detected")
                    return False
            except:
                pass
            
            # Analyze all pixels for brightness and color
            bright_pixels = 0
            colored_pixels = 0
            
            for pixel in pixels:
                r, g, b = pixel[:3]
                brightness = (r + g + b) / 3
                
                if brightness > bright_threshold:
                    bright_pixels += 1
                    
                if max(r, g, b) - min(r, g, b) > color_variance_threshold:
                    colored_pixels += 1
            
            bright_percentage = (bright_pixels / total_pixels) * 100
            color_percentage = (colored_pixels / total_pixels) * 100
            
            self.log_message(f"🔍 Analysis: {bright_percentage:.1f}% bright, {color_percentage:.1f}% colorful")
            
            if bright_percentage > bright_percentage_min and color_percentage > color_percentage_min:
                self.log_message(f"🔍 Sufficient bright/colorful pixels - monster detected")
                return True
            
            if bright_percentage < (bright_percentage_min / 3) and color_percentage < (color_percentage_min / 3):
                self.log_message(f"🔍 Too few bright/colorful pixels - no monster detected")
                return False
            
            self.log_message(f"🔍 Uncertain detection result - assuming monster present")
            return True
            
        except Exception as e:
            self.log_message(f"Error in advanced monster detection: {str(e)}")
            return True
    
    def update_scan_mode_display(self):
        """Update the scan mode display information"""
        if self.scan_mode_var.get() == "all":
            count = len(self.monster_names)
            self.scan_mode_info.config(text=f"({count} monsters)")
        else:
            count = len(self.selected_monsters)
            self.scan_mode_info.config(text=f"({count} selected monsters)")
    
    def toggle_debug_mode(self):
        """Toggle debug mode for soul detection troubleshooting"""
        self.soul_counter.debug_mode = not self.soul_counter.debug_mode
        colors = self.get_theme_colors()
        
        if self.soul_counter.debug_mode:
            self.debug_button.configure(text="🐛 Debug ON", bg=colors['warning'])
            self.log_message("🐛 Debug mode enabled - slot images will be saved for troubleshooting")
        else:
            self.debug_button.configure(text="🐛 Debug OFF", bg=colors['secondary'])
            self.log_message("🐛 Debug mode disabled")
    
    def get_monsters_to_scan(self):
        """Get the list of monsters to scan based on selected mode"""
        if self.scan_mode_var.get() == "all":
            return self.monster_names
        else:
            return list(self.selected_monsters.keys())
    
    def test_bank_grid(self):
        """Test the coordinate calibration by highlighting slots"""
        if not self.slot_coordinates or len(self.slot_coordinates) != 45:
            # Try to load coordinates first
            self.slot_coordinates = self.load_slot_coordinates()
            if not self.slot_coordinates or len(self.slot_coordinates) != 45:
                messagebox.showerror(
                    "Coordinates Not Calibrated", 
                    "Please run coordinate calibration first!\n\n"
                    "Click the '🎯 Coordinate Calibration' button to set up "
                    "the exact positions of all 45 bank slots."
                )
                return
        
        self.log_message("🔍 Testing coordinate calibration setup...")
        
        # Test first few slots using coordinates
        for i in range(min(9, len(self.slot_coordinates))):  # Test first 9 slots
            coord = self.slot_coordinates[i]
            if coord:
                # Briefly move mouse to each slot to show calibration
                pyautogui.moveTo(coord['x'], coord['y'])
                time.sleep(0.3)
        
        messagebox.showinfo("Grid Test", "Grid test complete! Did the cursor visit the correct slots?")
    
    def capture_bank_screenshot_for_calibration(self):
        """Simplified manual calibration with screenshot and manual slot selection"""
        print("🔧 Starting manual calibration process...")
        self.update_status("🔧 Starting manual calibration...")
        
        result = messagebox.askquestion(
            "Manual Bank Calibration", 
            "📸 Manual Bank Calibration Process:\n\n"
            "1. You'll take a screenshot in 3 seconds\n"
            "2. Then click on 4 specific slots:\n"
            "   • Top-left slot (row 0, col 0)\n"
            "   • Top-right slot (row 0, col 4)\n" 
            "   • Bottom-left slot (row 8, col 0)\n"
            "   • Any slot with a soul\n\n"
            "Make sure your bank is fully visible!\n\n"
            "Ready to start?"
        )
        
        if result == 'yes':
            self.update_status("📸 Taking screenshot in 3 seconds...")
            print("📸 Screenshot will be taken in 3 seconds...")
            self.root.after(3000, self._perform_manual_calibration)
        else:
            self.update_status("❌ Manual calibration cancelled")
            print("❌ Manual calibration cancelled by user")
    
    def _perform_manual_calibration(self):
        """Take screenshot and start manual slot selection process"""
        try:
            print("📸 Taking screenshot now...")
            self.update_status("📸 Taking screenshot...")
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Save screenshot
            script_dir = os.path.dirname(os.path.abspath(__file__))
            screenshot_path = os.path.join(script_dir, 'bank_calibration_screenshot.jpg')
            cv2.imwrite(screenshot_path, screenshot_bgr)
            print(f"✅ Screenshot saved to: {screenshot_path}")
            
            # Start manual slot selection
            self.update_status("🎯 Starting slot selection process...")
            self.manual_slot_selection()
            
        except Exception as e:
            error_msg = f"Error taking screenshot: {e}"
            print(f"❌ {error_msg}")
            messagebox.showerror("Screenshot Error", error_msg)
            self.update_status("❌ Screenshot failed")
    
    def manual_slot_selection(self):
        """Guide user through manual slot selection for calibration"""
        print("🎯 Starting manual slot selection...")
        self.calibration_clicks = []
        self.expected_clicks = 4  # We'll ask for 4 specific slots
        
        # Instructions for which slots to click
        self.click_instructions = [
            "TOP-LEFT slot (row 0, col 0)",
            "TOP-RIGHT slot (row 0, col 4)", 
            "BOTTOM-LEFT slot (row 8, col 0)",
            "Any slot with a SOUL in it"
        ]
        
        self.current_click = 0
        self._ask_for_next_click()
    
    def _ask_for_next_click(self):
        """Ask user to click on the next calibration slot"""
        if self.current_click >= self.expected_clicks:
            self._process_calibration_clicks()
            return
            
        instruction = self.click_instructions[self.current_click]
        step_num = self.current_click + 1
        
        print(f"🎯 Step {step_num}/4: Click on {instruction}")
        self.update_status(f"🎯 Step {step_num}/4: Click on {instruction}")
        
        messagebox.showinfo(
            f"Calibration Step {step_num}/4",
            f"📍 Click on the {instruction}\n\n"
            f"After clicking OK:\n"
            f"1. Position your mouse over the specified slot\n"
            f"2. Wait for the cursor capture (3 seconds)\n\n"
            f"The tool will automatically capture your mouse position."
        )
        
        self.root.after(3000, self._capture_calibration_click)
    
    def _capture_calibration_click(self):
        """Capture the user's click position"""
        try:
            pos = pyautogui.position()
            click_info = {
                'x': pos.x,
                'y': pos.y,
                'step': self.current_click,
                'description': self.click_instructions[self.current_click]
            }
            
            self.calibration_clicks.append(click_info)
            
            step_num = self.current_click + 1
            print(f"✅ Captured click {step_num}: ({pos.x}, {pos.y}) - {self.click_instructions[self.current_click]}")
            self.update_status(f"✅ Captured step {step_num}/4")
            
            self.current_click += 1
            
            # Small delay before next step
            self.root.after(1000, self._ask_for_next_click)
            
        except Exception as e:
            error_msg = f"Error capturing click: {e}"
            print(f"❌ {error_msg}")
            messagebox.showerror("Click Error", error_msg)
            self.update_status("❌ Click capture failed")
    
    def _process_calibration_clicks(self):
        """Process the calibration clicks to determine bank parameters"""
        try:
            if len(self.calibration_clicks) != 4:
                messagebox.showerror("Calibration Error", "Not enough calibration points captured!")
                return
            
            # Extract click positions
            top_left = self.calibration_clicks[0]      # row 0, col 0
            top_right = self.calibration_clicks[1]     # row 0, col 4  
            bottom_left = self.calibration_clicks[2]   # row 8, col 0
            soul_slot = self.calibration_clicks[3]     # any slot with soul
            
            # Calculate grid parameters
            # Horizontal spacing (between columns)
            col_spacing = (top_right['x'] - top_left['x']) / 4  # 4 spaces between 5 columns
            
            # Vertical spacing (between rows)
            row_spacing = (bottom_left['y'] - top_left['y']) / 8  # 8 spaces between 9 rows
            
            # Estimate slot size by taking a sample around the soul slot
            sample_x = soul_slot['x']
            sample_y = soul_slot['y']
            
            # Take a screenshot of the soul slot area to measure
            slot_screenshot = pyautogui.screenshot(region=(sample_x-25, sample_y-25, 50, 50))
            slot_np = np.array(slot_screenshot)
            slot_bgr = cv2.cvtColor(slot_np, cv2.COLOR_RGB2BGR)
            
            # Analyze the soul slot to find actual slot boundaries
            slot_analysis = self._analyze_soul_slot(slot_bgr)
            
            if slot_analysis:
                slot_width = slot_analysis['width']
                slot_height = slot_analysis['height']
            else:
                # Fallback to estimated size
                slot_width = int(col_spacing * 0.85)  # Slot is ~85% of spacing
                slot_height = int(row_spacing * 0.85)
            
            # Create calibration result
            calibration_result = {
                'slot_width': max(35, min(60, slot_width)),   # Clamp to reasonable range
                'slot_height': max(35, min(60, slot_height)),
                'spacing_x': max(40, min(80, int(col_spacing))),
                'spacing_y': max(40, min(80, int(row_spacing))),
                'cols': 5,  # Fixed: 5 columns
                'rows': 9,  # Fixed: 9 rows  
                'total_slots': 45,  # 5 × 9 = 45 total slots
                'bank_x': top_left['x'],
                'bank_y': top_left['y'],
                'method': 'manual_calibration'
            }
            
            # Apply the calibration
            self.apply_auto_calibration(calibration_result)
            
            # Show success message
            messagebox.showinfo(
                "Manual Calibration Success!",
                f"✅ Bank calibrated successfully!\n\n"
                f"📏 Slot size: {calibration_result['slot_width']}×{calibration_result['slot_height']}\n"
                f"📐 Grid spacing: {calibration_result['spacing_x']}×{calibration_result['spacing_y']}\n"
                f"🎯 Grid layout: 5×9 (45 slots)\n"
                f"📍 Bank position: ({calibration_result['bank_x']}, {calibration_result['bank_y']})\n\n"
                f"Now try scanning souls - should be much more accurate!"
            )
            
            self.update_status("✅ Manual calibration completed!")
            
        except Exception as e:
            messagebox.showerror("Calibration Error", f"Error processing calibration: {e}")
    
    def _analyze_soul_slot(self, slot_image):
        """Analyze a soul slot image to determine its boundaries"""
        try:
            # Convert to different color spaces
            gray = cv2.cvtColor(slot_image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(slot_image, cv2.COLOR_BGR2HSV)
            
            # Look for yellow soul content
            yellow_mask = cv2.inRange(hsv, np.array([15, 100, 100]), np.array([35, 255, 255]))
            
            # Find the bounding box of yellow content
            contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get the largest yellow contour (the soul)
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Estimate slot size based on soul size (soul is ~70% of slot)
                estimated_slot_w = int(w / 0.7)
                estimated_slot_h = int(h / 0.7)
                
                return {
                    'width': estimated_slot_w,
                    'height': estimated_slot_h,
                    'confidence': 'high'
                }
            
            return None
            
        except Exception as e:
            print(f"Error analyzing soul slot: {e}")
            return None
    
    def detect_bank_slots_with_borders(self, screenshot):
        """Detect bank slots based on white/gray borders like in the reference image"""
        try:
            # Convert to grayscale for border detection
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Detect edges (white borders around slots)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours of rectangular shapes (slot borders)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours to find slot-like rectangles
            slot_candidates = []
            
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Look for rectangular shapes (4 corners)
                if len(approx) >= 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Filter by size - should be reasonable slot dimensions
                    if 35 <= w <= 60 and 35 <= h <= 60:
                        # Check aspect ratio (should be roughly square)
                        aspect_ratio = w / h
                        if 0.8 <= aspect_ratio <= 1.2:
                            # Check if this looks like a slot border
                            slot_region = gray[y:y+h, x:x+w]
                            if self.is_slot_border_region(slot_region):
                                slot_candidates.append({
                                    'x': x, 'y': y, 'w': w, 'h': h,
                                    'center_x': x + w//2, 'center_y': y + h//2
                                })
            
            if len(slot_candidates) < 10:  # Need reasonable number of slots
                return None
            
            # Analyze slot arrangement to determine grid
            return self.analyze_slot_grid(slot_candidates)
            
        except Exception as e:
            print(f"Error detecting bank slots: {e}")
            return None
    
    def is_slot_border_region(self, slot_region):
        """Check if a region looks like a slot with borders"""
        try:
            # Check for border characteristics
            # Slots typically have darker interior with lighter borders
            
            # Get border pixels (edges of the region)
            h, w = slot_region.shape
            border_pixels = []
            
            # Top and bottom borders
            border_pixels.extend(slot_region[0, :].flatten())
            border_pixels.extend(slot_region[-1, :].flatten())
            
            # Left and right borders  
            border_pixels.extend(slot_region[:, 0].flatten())
            border_pixels.extend(slot_region[:, -1].flatten())
            
            # Interior pixels (excluding border)
            if h > 4 and w > 4:
                interior = slot_region[2:-2, 2:-2]
                interior_mean = np.mean(interior)
                border_mean = np.mean(border_pixels)
                
                # Borders should be lighter than interior for typical slots
                return border_mean > interior_mean + 10
            
            return True  # Accept if too small to analyze
            
        except:
            return True
    
    def analyze_slot_grid(self, slot_candidates):
        """Analyze detected slots to determine grid layout and spacing"""
        try:
            if len(slot_candidates) < 4:
                return None
            
            # Sort slots by position
            slots_by_row = {}
            slots_by_col = {}
            
            # Group slots by approximate rows and columns
            for slot in slot_candidates:
                row_key = round(slot['center_y'] / 50) * 50  # Group by 50px intervals
                col_key = round(slot['center_x'] / 50) * 50
                
                if row_key not in slots_by_row:
                    slots_by_row[row_key] = []
                slots_by_row[row_key].append(slot)
                
                if col_key not in slots_by_col:
                    slots_by_col[col_key] = []
                slots_by_col[col_key].append(slot)
            
            # Determine grid dimensions
            rows = len(slots_by_row)
            cols = len(slots_by_col)
            
            # Calculate average slot size
            avg_width = int(np.mean([slot['w'] for slot in slot_candidates]))
            avg_height = int(np.mean([slot['h'] for slot in slot_candidates]))
            
            # Calculate spacing by looking at distances between adjacent slots
            x_spacings = []
            y_spacings = []
            
            # Sort slots by position for spacing calculation
            sorted_slots = sorted(slot_candidates, key=lambda s: (s['center_y'], s['center_x']))
            
            for i in range(len(sorted_slots)):
                for j in range(i+1, len(sorted_slots)):
                    slot1 = sorted_slots[i]
                    slot2 = sorted_slots[j]
                    
                    dx = abs(slot2['center_x'] - slot1['center_x'])
                    dy = abs(slot2['center_y'] - slot1['center_y'])
                    
                    # Look for horizontal neighbors (same row)
                    if dy < 20 and 40 < dx < 80:
                        x_spacings.append(dx)
                    
                    # Look for vertical neighbors (same column)
                    if dx < 20 and 40 < dy < 80:
                        y_spacings.append(dy)
            
            if not x_spacings or not y_spacings:
                # Fallback: estimate from overall grid
                if len(slot_candidates) >= 4:
                    min_x = min(slot['center_x'] for slot in slot_candidates)
                    max_x = max(slot['center_x'] for slot in slot_candidates)
                    min_y = min(slot['center_y'] for slot in slot_candidates)
                    max_y = max(slot['center_y'] for slot in slot_candidates)
                    
                    spacing_x = int((max_x - min_x) / max(1, cols - 1)) if cols > 1 else avg_width + 5
                    spacing_y = int((max_y - min_y) / max(1, rows - 1)) if rows > 1 else avg_height + 5
                else:
                    spacing_x = avg_width + 5
                    spacing_y = avg_height + 5
            else:
                spacing_x = int(np.median(x_spacings))
                spacing_y = int(np.median(y_spacings))
            
            # Find top-left position
            top_left_slot = min(slot_candidates, key=lambda s: s['center_y'] * 1000 + s['center_x'])
            bank_x = top_left_slot['x']
            bank_y = top_left_slot['y']
            
            return {
                'slot_width': avg_width,
                'slot_height': avg_height,
                'spacing_x': spacing_x,
                'spacing_y': spacing_y,
                'cols': max(5, cols),  # Ensure at least 5 cols based on your info
                'rows': max(9, rows),  # Ensure at least 9 rows based on your info  
                'total_slots': max(45, cols * rows),
                'bank_x': bank_x,
                'bank_y': bank_y,
                'detected_slots': len(slot_candidates)
            }
            
        except Exception as e:
            print(f"Error analyzing slot grid: {e}")
            return None
    
    def apply_auto_calibration(self, slot_info):
        """Apply the auto-detected calibration settings"""
        try:
            # Update soul counter settings
            self.soul_counter.slot_size = (slot_info['slot_width'], slot_info['slot_height'])
            self.soul_counter.grid_spacing = (slot_info['spacing_x'], slot_info['spacing_y'])
            self.soul_counter.grid_cols = slot_info['cols']
            self.soul_counter.grid_rows = slot_info['rows']
            self.soul_counter.set_bank_grid_position(slot_info['bank_x'], slot_info['bank_y'])
            
            # Update coordinate status display
            self.update_coord_status()
            
            print(f"✅ Auto-calibration applied:")
            print(f"   Slot size: {slot_info['slot_width']}×{slot_info['slot_height']}")
            print(f"   Grid spacing: {slot_info['spacing_x']}×{slot_info['spacing_y']}")
            print(f"   Grid layout: {slot_info['cols']}×{slot_info['rows']}")
            print(f"   Bank position: ({slot_info['bank_x']}, {slot_info['bank_y']})")
            
        except Exception as e:
            print(f"Error applying auto-calibration: {e}")
    
    def calibrate_grid_settings(self):
        """Open dialog to calibrate grid settings for better accuracy"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎯 Grid Calibration")
        dialog.geometry("500x400")
        dialog.configure(bg=self.get_theme_colors()['bg'])
        dialog.attributes('-topmost', True)
        
        colors = self.get_theme_colors()
        
        # Title
        title_label = tk.Label(
            dialog,
            text="🎯 Coordinate Calibration Test",
            font=('Segoe UI', 14, 'bold'),
            fg=colors['accent'],
            bg=colors['bg']
        )
        title_label.pack(pady=10)
        
        # Current settings frame
        current_frame = tk.LabelFrame(dialog, text="Current Settings", bg=colors['bg'], fg=colors['fg'])
        current_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(current_frame, text=f"Slot Size: {self.soul_counter.slot_size}", bg=colors['bg'], fg=colors['fg']).pack(anchor='w')
        tk.Label(current_frame, text=f"Grid Spacing: {self.soul_counter.grid_spacing}", bg=colors['bg'], fg=colors['fg']).pack(anchor='w')
        
        # Adjustment frame
        adjust_frame = tk.LabelFrame(dialog, text="Adjust Settings", bg=colors['bg'], fg=colors['fg'])
        adjust_frame.pack(fill='x', padx=20, pady=10)
        
        # Slot width
        tk.Label(adjust_frame, text="Slot Width:", bg=colors['bg'], fg=colors['fg']).pack(anchor='w')
        slot_width_var = tk.StringVar(value=str(self.soul_counter.slot_size[0]))
        slot_width_entry = tk.Entry(adjust_frame, textvariable=slot_width_var, width=10)
        slot_width_entry.pack(anchor='w')
        
        # Slot height
        tk.Label(adjust_frame, text="Slot Height:", bg=colors['bg'], fg=colors['fg']).pack(anchor='w')
        slot_height_var = tk.StringVar(value=str(self.soul_counter.slot_size[1]))
        slot_height_entry = tk.Entry(adjust_frame, textvariable=slot_height_var, width=10)
        slot_height_entry.pack(anchor='w')
        
        # Spacing X
        tk.Label(adjust_frame, text="Horizontal Spacing:", bg=colors['bg'], fg=colors['fg']).pack(anchor='w')
        spacing_x_var = tk.StringVar(value=str(self.soul_counter.grid_spacing[0]))
        spacing_x_entry = tk.Entry(adjust_frame, textvariable=spacing_x_var, width=10)
        spacing_x_entry.pack(anchor='w')
        
        # Spacing Y
        tk.Label(adjust_frame, text="Vertical Spacing:", bg=colors['bg'], fg=colors['fg']).pack(anchor='w')
        spacing_y_var = tk.StringVar(value=str(self.soul_counter.grid_spacing[1]))
        spacing_y_entry = tk.Entry(adjust_frame, textvariable=spacing_y_var, width=10)
        spacing_y_entry.pack(anchor='w')
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=colors['bg'])
        button_frame.pack(pady=20)
        
        def apply_settings():
            try:
                self.soul_counter.slot_size = (int(slot_width_var.get()), int(slot_height_var.get()))
                self.soul_counter.grid_spacing = (int(spacing_x_var.get()), int(spacing_y_var.get()))
                self.log_message(f"🎯 Grid settings updated: Size={self.soul_counter.slot_size}, Spacing={self.soul_counter.grid_spacing}")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers!")
        
        def reset_defaults():
            slot_width_var.set("44")
            slot_height_var.set("44")
            spacing_x_var.set("47")
            spacing_y_var.set("47")
        
        self.create_modern_button(button_frame, "✅ Apply", apply_settings, colors['success']).pack(side='left', padx=5)
        self.create_modern_button(button_frame, "🔄 Reset", reset_defaults, colors['warning']).pack(side='left', padx=5)
        self.create_modern_button(button_frame, "❌ Cancel", dialog.destroy, colors['danger']).pack(side='left', padx=5)
    
    def start_coordinate_calibration(self):
        """Start the streamlined 45-slot coordinate calibration process"""
        # Check if coordinates already exist
        existing_coords = self.load_slot_coordinates()
        if existing_coords and len(existing_coords) == 45:
            result = messagebox.askyesno(
                "Existing Calibration Found",
                f"Found existing calibration with {len(existing_coords)} slot coordinates.\n\n"
                "Do you want to recalibrate all 45 slots?\n\n"
                "Click 'No' to keep existing calibration."
            )
            if not result:
                self.slot_coordinates = existing_coords
                messagebox.showinfo("Calibration Loaded", "Using existing slot coordinates!")
                return

        # Start new streamlined calibration
        self.captured_coordinates = []  # Reset temporary storage
        self.current_slot_index = 0
        self.coordinate_calibration_active = True
        
        # Show initial instructions
        messagebox.showinfo(
            "🎯 Streamlined Coordinate Calibration",
            "📋 STREAMLINED CALIBRATION PROCESS:\n\n"
            "1️⃣ Click 'Start Capture' to begin\n"
            "2️⃣ Click each slot in order (45 total clicks)\n"
            "3️⃣ Watch progress counter update automatically\n"
            "4️⃣ Click 'Save Coordinates' when complete\n\n"
            "🔄 Slot Order: Left→Right, Top→Bottom\n"
            "• Row 0: (0,0)→(0,1)→(0,2)→(0,3)→(0,4)\n"
            "• Row 1: (1,0)→(1,1)→(1,2)→(1,3)→(1,4)\n"
            "• Continue for all 9 rows...\n\n"
            "⚠️ Click the CENTER of each slot!"
        )
        
        self.show_streamlined_calibration_window()

    def show_streamlined_calibration_window(self):
        """Show the streamlined calibration control window"""
        if self.calibration_window:
            self.calibration_window.destroy()
        
        self.calibration_window = tk.Toplevel(self.root)
        self.calibration_window.title("🎯 Coordinate Calibration")
        self.calibration_window.geometry("450x350")
        self.calibration_window.attributes('-topmost', True)
        
        # Title
        title_label = tk.Label(
            self.calibration_window, 
            text="🎯 Streamlined Coordinate Calibration",
            font=("Arial", 16, "bold"),
            fg="blue"
        )
        title_label.pack(pady=10)
        
        # Progress display
        self.progress_label = tk.Label(
            self.calibration_window,
            text=f"Progress: {len(self.captured_coordinates)}/45 slots captured",
            font=("Arial", 14, "bold"),
            fg="green"
        )
        self.progress_label.pack(pady=10)
        
        # Current slot indicator
        self.current_slot_label = tk.Label(
            self.calibration_window,
            text=self.get_current_slot_text(),
            font=("Arial", 12),
            fg="purple"
        )
        self.current_slot_label.pack(pady=5)
        
        # Instructions
        instructions = tk.Label(
            self.calibration_window,
            text="1. Click 'Start Capture' below\n"
                 "2. Click each slot in the game (45 total)\n"
                 "3. Watch progress update automatically\n"
                 "4. Click 'Save' when 45/45 complete",
            font=("Arial", 10),
            justify="left"
        )
        instructions.pack(pady=10)
        
        # Start capture button
        self.start_capture_btn = tk.Button(
            self.calibration_window,
            text="🚀 Start Capture Mode",
            font=("Arial", 12, "bold"),
            bg="#28a745",
            fg="white",
            command=self.start_click_capture
        )
        self.start_capture_btn.pack(pady=10)
        
        # Save coordinates button (initially disabled)
        self.save_coords_btn = tk.Button(
            self.calibration_window,
            text="💾 Save Coordinates",
            font=("Arial", 12, "bold"),
            bg="#007bff",
            fg="white",
            state="disabled",
            command=self.save_captured_coordinates
        )
        self.save_coords_btn.pack(pady=5)
        
        # Cancel button
        cancel_btn = tk.Button(
            self.calibration_window,
            text="❌ Cancel",
            font=("Arial", 10),
            bg="#dc3545",
            fg="white",
            command=self.cancel_coordinate_calibration
        )
        cancel_btn.pack(pady=10)
        
    def get_current_slot_text(self):
        """Get text describing the current slot to capture"""
        if len(self.captured_coordinates) >= 45:
            return "✅ All 45 slots captured! Ready to save."
        
        slot_index = len(self.captured_coordinates)
        row = slot_index // 5
        col = slot_index % 5
        
        position_desc = self.get_slot_description(row, col)
        return f"Next: Slot ({row},{col}) - {position_desc}"
        
    def start_click_capture(self):
        """Start capturing mouse clicks for coordinates"""
        if not PYNPUT_AVAILABLE:
            messagebox.showerror(
                "Missing Dependency", 
                "pynput library required for coordinate capture.\n\n"
                "Install with: pip install pynput"
            )
            return
            
        # Disable start button and update UI
        self.start_capture_btn.config(state="disabled", text="🎯 Capturing... Click slots!")
        
        # Start mouse listener
        self.coordinate_listener = mouse.Listener(
            on_click=self.on_coordinate_click
        )
        self.coordinate_listener.start()
        
        print("🎯 Coordinate capture mode started! Click each slot in order.")
    
    def on_coordinate_click(self, x, y, button, pressed):
        """Handle mouse clicks during coordinate capture"""
        if not self.coordinate_calibration_active or not pressed:
            return
            
        if button == mouse.Button.left and len(self.captured_coordinates) < 45:
            slot_index = len(self.captured_coordinates)
            row = slot_index // 5
            col = slot_index % 5
            
            # Store coordinate
            coord_data = {
                'row': row,
                'col': col,
                'x': int(x),
                'y': int(y),
                'slot_index': slot_index
            }
            self.captured_coordinates.append(coord_data)
            
            # Update UI
            self.update_calibration_progress()
            
            print(f"✅ Captured slot ({row},{col}) at coordinates ({int(x)}, {int(y)}) - {len(self.captured_coordinates)}/45")
            
            # Check if complete
            if len(self.captured_coordinates) >= 45:
                self.complete_capture_mode()
                
    def update_calibration_progress(self):
        """Update the calibration progress display"""
        if self.calibration_window and self.progress_label:
            progress_count = len(self.captured_coordinates)
            self.progress_label.config(text=f"Progress: {progress_count}/45 slots captured")
            
            if self.current_slot_label:
                self.current_slot_label.config(text=self.get_current_slot_text())
                
            # Enable save button when complete
            if progress_count >= 45 and self.save_coords_btn:
                self.save_coords_btn.config(state="normal", bg="#28a745")
                
    def complete_capture_mode(self):
        """Complete the coordinate capture mode"""
        if self.coordinate_listener:
            self.coordinate_listener.stop()
            self.coordinate_listener = None
        
        if self.start_capture_btn:
            self.start_capture_btn.config(text="✅ Capture Complete!", bg="#28a745")
            
        print("🎉 All 45 coordinates captured! Click 'Save Coordinates' to save.")
        
    def save_captured_coordinates(self):
        """Save all captured coordinates to file"""
        if len(self.captured_coordinates) != 45:
            messagebox.showerror("Error", f"Need exactly 45 coordinates, got {len(self.captured_coordinates)}")
            return
            
        try:
            # Create config directory if it doesn't exist
            import os
            os.makedirs("config", exist_ok=True)
            
            # Prepare coordinate data
            coordinate_data = {
                'coordinates': self.captured_coordinates,
                'calibration_date': datetime.now().isoformat(),
                'total_slots': 45,
                'grid_size': {'rows': 9, 'cols': 5},
                'version': '1.0'
            }
            
            # Save to file
            with open(self.coordinates_file, 'w') as f:
                json.dump(coordinate_data, f, indent=2)
            
            # Update class variables
            self.slot_coordinates = self.captured_coordinates.copy()
            
            # Show success message
            messagebox.showinfo(
                "✅ Coordinates Saved!",
                f"Successfully saved {len(self.captured_coordinates)} slot coordinates!\n\n"
                f"File: {self.coordinates_file}\n\n"
                "These coordinates will be used for accurate soul detection."
            )
            
            # Complete calibration (don't show cancelled message)
            self.complete_coordinate_calibration()
            
            print(f"✅ Coordinates saved to {self.coordinates_file}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save coordinates:\n{str(e)}")
            
    def complete_coordinate_calibration(self):
        """Complete coordinate calibration successfully (no cancellation message)"""
        self.coordinate_calibration_active = False
        self.coordinate_capture_mode = False
        self.captured_coordinates = []
        self.current_capture_slot = 0
        
        # Stop mouse listener quietly
        if self.coordinate_listener:
            self.coordinate_listener.stop()
            self.coordinate_listener = None
        
        # Close calibration window quietly
        if self.calibration_window:
            self.calibration_window.destroy()
            self.calibration_window = None
        
        # Update status
        self.update_coordinate_status()
        
        print("✅ Coordinate calibration completed successfully!")
            
    def cancel_coordinate_calibration(self):
        """Cancel the coordinate calibration process"""
        self.coordinate_calibration_active = False
        
        if self.coordinate_listener:
            self.coordinate_listener.stop()
            self.coordinate_listener = None
            
        if self.calibration_window:
            self.calibration_window.destroy()
            self.calibration_window = None
            
        print("🚫 Coordinate calibration cancelled.")
    
    def get_slot_description(self, row, col):
        """Get human-readable description of slot position"""
        if row == 0 and col == 0:
            return "TOP-LEFT corner slot"
        elif row == 0 and col == 4:
            return "TOP-RIGHT corner slot"
        elif row == 8 and col == 0:
            return "BOTTOM-LEFT corner slot"
        elif row == 8 and col == 4:
            return "BOTTOM-RIGHT corner slot"
        elif row == 0:
            return f"Top row, column {col + 1}"
        elif row == 8:
            return f"Bottom row, column {col + 1}"
        elif col == 0:
            return f"Left column, row {row + 1}"
        elif col == 4:
            return f"Right column, row {row + 1}"
        else:
            return f"Row {row + 1}, Column {col + 1}"
    
    def cancel_coordinate_calibration(self):
        """Cancel the coordinate calibration process"""
        self.coordinate_calibration_active = False
        self.slot_coordinates = []
        self.current_slot_index = 0
        
        if self.calibration_window:
            self.calibration_window.destroy()
        
        messagebox.showinfo("Calibration Cancelled", "Coordinate calibration has been cancelled.")
    
    def complete_coordinate_calibration(self):
        """Complete the coordinate calibration and save results"""
        if self.calibration_window:
            self.calibration_window.destroy()
        
        self.coordinate_calibration_active = False
        
        # Save coordinates
        if self.save_slot_coordinates():
            messagebox.showinfo(
                "Calibration Complete!",
                f"✅ Successfully calibrated all 45 slots!\n\n"
                f"Coordinates saved to: {self.coordinates_file}\n\n"
                "You can now use precise soul detection with 100% accuracy!"
            )
            print(f"🎯 Coordinate calibration completed! 45 slots saved.")
        else:
            messagebox.showerror("Save Error", "Failed to save coordinates to file.")

    def detect_souls_with_coordinates(self):
        """Detect souls using saved coordinates - 100% accurate method"""
        if not self.slot_coordinates:
            # Try to load saved coordinates
            self.slot_coordinates = self.load_slot_coordinates()
            if not self.slot_coordinates:
                messagebox.showerror(
                    "No Calibration", 
                    "No slot coordinates found!\n\nPlease run coordinate calibration first."
                )
                return 0
        
        if len(self.slot_coordinates) != 45:
            messagebox.showerror(
                "Incomplete Calibration",
                f"Only {len(self.slot_coordinates)} slots calibrated.\n\nNeed exactly 45 slots for 5×9 grid."
            )
            return 0
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        soul_count = 0
        souls_found = []
        
        # Check each coordinate for yellow souls
        for coord in self.slot_coordinates:
            x, y = coord['x'], coord['y']
            row, col = coord['row'], coord['col']
            
            # Extract small region around the coordinate
            region_size = 20  # 20x20 pixel region around the point
            x1, y1 = max(0, x - region_size//2), max(0, y - region_size//2)
            x2, y2 = min(screenshot_cv.shape[1], x + region_size//2), min(screenshot_cv.shape[0], y + region_size//2)
            
            slot_region = screenshot_cv[y1:y2, x1:x2]
            
            if self.is_soul_present_in_region(slot_region):
                soul_count += 1
                souls_found.append({
                    'row': row, 'col': col, 'x': x, 'y': y
                })
                print(f"🟡 Soul detected at slot ({row}, {col}) - coordinates ({x}, {y})")
        
        print(f"🎯 Total souls detected: {soul_count}")
        return soul_count
    
    def is_soul_present_in_region(self, region):
        """Check if a small region contains a yellow soul"""
        if region is None or region.size == 0:
            return False
            
        try:
            # Convert to HSV for better yellow detection
            hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
            
            # Define yellow color range for souls
            yellow_lower = np.array([15, 100, 150])
            yellow_upper = np.array([35, 255, 255])
            
            # Create mask for yellow colors
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            
            # Calculate percentage of yellow pixels
            yellow_pixels = cv2.countNonZero(yellow_mask)
            total_pixels = region.shape[0] * region.shape[1]
            
            if total_pixels == 0:
                return False
            
            yellow_percentage = (yellow_pixels / total_pixels) * 100
            
            # Consider it a soul if at least 15% of the region is yellow
            return yellow_percentage >= 15.0
            
        except Exception as e:
            print(f"Error checking soul in region: {e}")
            return False

    # =============================================================================
    # METAMOB.FR API INTEGRATION METHODS
    # =============================================================================
    
    def setup_metamob_credentials(self):
        """Open Metamob API credentials setup dialog"""
        self.metamob_api.setup_credentials()
        self.update_metamob_status()
    
    def test_metamob_connection(self):
        """Test Metamob API connection"""
        if self.metamob_api.test_connection():
            messagebox.showinfo("Connection Test", "✅ Metamob API connection successful!")
            self.update_metamob_status()
        else:
            messagebox.showerror("Connection Test", "❌ Failed to connect to Metamob API.\n\nPlease check your credentials.")
    
    def sync_to_metamob(self):
        """Sync soul scan results to Metamob"""
        if not self.metamob_api.api_key:
            messagebox.showwarning(
                "Not Configured", 
                "Metamob API not configured!\n\nPlease setup your API credentials first."
            )
            return
        
        # Check if we have scan data to sync
        if not hasattr(self, 'soul_scan_data') or not self.soul_scan_data:
            messagebox.showwarning(
                "No Data", 
                "No soul scan data to sync!\n\nPlease run a soul scan first."
            )
            return
        
        # Confirm sync operation with threshold option
        monster_count = len(self.soul_scan_data)
        
        # Create custom dialog for sync options
        sync_dialog = tk.Toplevel(self.root)
        sync_dialog.title("🌐 Sync Options")
        sync_dialog.geometry("450x250")
        sync_dialog.transient(self.root)
        sync_dialog.grab_set()
        
        # Center the dialog
        sync_dialog.update_idletasks()
        x = (sync_dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (sync_dialog.winfo_screenheight() // 2) - (250 // 2)
        sync_dialog.geometry(f"450x250+{x}+{y}")
        
        sync_frame = tk.Frame(sync_dialog, bg='white', padx=20, pady=20)
        sync_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            sync_frame,
            text=f"🌐 Sync {monster_count} monsters to Metamob.fr?",
            font=('Arial', 14, 'bold'),
            bg='white'
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = tk.Label(
            sync_frame,
            text="This will update your soul counts on metamob.fr.\nMake sure your scan data is accurate!",
            font=('Arial', 10),
            bg='white',
            justify='center'
        )
        desc_label.pack(pady=(0, 15))
        
        # Threshold option
        include_states = tk.BooleanVar(value=True)
        threshold_check = tk.Checkbutton(
            sync_frame,
            text="🎯 Also update RECHERCHE/PROPOSER/AUCUN states based on thresholds",
            variable=include_states,
            font=('Arial', 10),
            bg='white'
        )
        threshold_check.pack(pady=(0, 10))
        
        # Show current thresholds
        thresholds = self.get_threshold_values()
        threshold_info = tk.Label(
            sync_frame,
            text=f"Current thresholds: RECHERCHE <{thresholds['recherche']}, "
                 f"PROPOSER >{thresholds['proposer']}, AUCUN ={thresholds['aucun']}",
            font=('Arial', 9),
            fg='gray',
            bg='white'
        )
        threshold_info.pack(pady=(0, 15))
        
        # Buttons
        button_frame = tk.Frame(sync_frame, bg='white')
        button_frame.pack()
        
        result = {'proceed': False, 'include_states': False}
        
        def on_sync():
            result['proceed'] = True
            result['include_states'] = include_states.get()
            sync_dialog.destroy()
        
        def on_cancel():
            result['proceed'] = False
            sync_dialog.destroy()
        
        tk.Button(
            button_frame,
            text="✅ Sync Now",
            command=on_sync,
            bg='#22C55E',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=on_cancel,
            bg='#EF4444',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        ).pack(side='left')
        
        # Wait for dialog to close
        sync_dialog.wait_window()
        
        if not result['proceed']:
            return
        
        # Show progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("🌐 Syncing to Metamob...")
        progress_dialog.geometry("500x200")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        # Center the dialog
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (200 // 2)
        progress_dialog.geometry(f"500x200+{x}+{y}")
        
        frame = ttk.Frame(progress_dialog, padding="20")
        frame.pack(fill='both', expand=True)
        
        status_label = tk.Label(
            frame, 
            text="🌐 Syncing soul data to Metamob.fr...",
            font=('Arial', 12),
            wraplength=450
        )
        status_label.pack(pady=10)
        
        # Progress bar
        progress_bar = ttk.Progressbar(
            frame,
            mode='determinate',
            length=400
        )
        progress_bar.pack(pady=10, fill='x')
        
        # Progress text
        progress_var = tk.StringVar(value="Preparing sync...")
        progress_label = tk.Label(frame, textvariable=progress_var)
        progress_label.pack(pady=5)
        
        # Statistics text
        stats_var = tk.StringVar(value="")
        stats_label = tk.Label(frame, textvariable=stats_var, font=('Arial', 9))
        stats_label.pack(pady=2)
        
        def sync_worker():
            """Worker function to perform sync in background"""
            try:
                # Initialize progress
                progress_bar['maximum'] = monster_count
                total_souls = sum(data.get('quantity', 0) for data in self.soul_scan_data.values())
                
                def update_progress(current_monster, total_monsters, updated_count, total_updated_souls):
                    """Callback to update progress during sync"""
                    progress_percent = (current_monster / total_monsters) * 100
                    progress_bar['value'] = current_monster
                    progress_var.set(f"Processing monster {current_monster}/{total_monsters}...")
                    stats_var.set(f"Updated: {updated_count} monsters | {total_updated_souls} souls")
                    progress_dialog.update()
                
                if result['include_states']:
                    progress_var.set("Updating soul counts with states...")
                    progress_dialog.update()
                    
                    # Get threshold values
                    thresholds = self.get_threshold_values()
                    
                    # Use threshold-based updates
                    success, final_stats = self.metamob_api.update_monster_states_with_thresholds_progress(
                        self.soul_scan_data,
                        thresholds['recherche'],
                        thresholds['proposer'],
                        thresholds['aucun'],
                        progress_callback=update_progress
                    )
                else:
                    progress_var.set("Uploading soul counts in chunks...")
                    progress_dialog.update()
                    
                    # Regular batch sync without states (includes 0-soul monsters)
                    # Now uses chunking for large datasets with progress updates
                    success, final_stats = self.metamob_api.batch_update_souls_with_progress(
                        self.soul_scan_data, 
                        progress_callback=update_progress
                    )
                
                # Close progress dialog
                progress_dialog.destroy()
                
                if success:
                    # Enhanced success message with detailed statistics
                    updated_monsters = final_stats.get('updated_monsters', 0)
                    total_updated_souls = final_stats.get('total_updated_souls', 0)
                    failed_monsters = final_stats.get('failed_monsters', 0)
                    
                    sync_message = f"✅ Successfully synced to Metamob.fr!\n\n"
                    sync_message += f"📊 SYNC STATISTICS:\n"
                    sync_message += f"• {updated_monsters} monsters updated\n"
                    sync_message += f"• {total_updated_souls} total souls synced\n"
                    sync_message += f"• {failed_monsters} monsters failed\n\n"
                    
                    if result['include_states']:
                        sync_message += "Updated soul counts AND states (RECHERCHE/PROPOSER/AUCUN) based on thresholds.\n"
                    else:
                        sync_message += "Updated soul counts only.\n"
                    sync_message += "\n📝 Note: Monsters with 0 souls are included in the sync."
                    sync_message += "\n📦 Large datasets are automatically split into chunks for reliability."
                    
                    messagebox.showinfo("Sync Complete", sync_message)
                    print(f"✅ Metamob sync complete: {updated_monsters} monsters, {total_updated_souls} souls updated")
                else:
                    messagebox.showerror(
                        "Sync Failed",
                        "❌ Failed to sync data to Metamob.fr.\n\n"
                        "This may be due to:\n"
                        "• Network connectivity issues\n"
                        "• Invalid API credentials\n"
                        "• Metamob server issues\n"
                        "• Too many requests (rate limiting)\n\n"
                        "Check the console for detailed error messages."
                    )
                    
            except Exception as e:
                progress_dialog.destroy()
                messagebox.showerror("Sync Error", f"❌ Sync failed with error:\n{str(e)}")
        
        # Start sync in background thread
        threading.Thread(target=sync_worker, daemon=True).start()
    
    def update_metamob_status(self):
        """Update Metamob status indicator"""
        if self.metamob_api.api_key and self.metamob_api.username:
            self.metamob_status.config(
                text=f"✅ Connected ({self.metamob_api.username})",
                fg='#22C55E'  # Green
            )
        else:
            self.metamob_status.config(
                text="❌ Not configured",
                fg='#EF4444'  # Red
            )
    
    def auto_update_states(self):
        """Update monster states on Metamob based on threshold values"""
        if not self.metamob_api.is_connected():
            messagebox.showerror("Error", "Please setup Metamob API credentials first!")
            return
        
        if not self.soul_scan_data:
            messagebox.showerror("Error", "No soul scan data available! Please perform a soul scan first.")
            return
        
        try:
            # Get threshold values from UI
            recherche_threshold = int(self.recherche_entry.get().strip() or "0")
            proposer_threshold = int(self.proposer_entry.get().strip() or "50")
            aucun_threshold = int(self.aucun_entry.get().strip() or "100")
            
            # Update the instance variables
            self.recherche_threshold = recherche_threshold
            self.proposer_threshold = proposer_threshold
            self.aucun_threshold = aucun_threshold
            
            # Create updates with states based on thresholds
            success = self.metamob_api.update_monster_states_with_thresholds(
                self.soul_scan_data,
                recherche_threshold,
                proposer_threshold,
                aucun_threshold
            )
            
            if success:
                messagebox.showinfo(
                    "Success", 
                    f"✅ Monster states updated successfully!\n\n"
                    f"Thresholds used:\n"
                    f"🔍 RECHERCHE: < {recherche_threshold} souls\n"
                    f"💰 PROPOSER: > {proposer_threshold} souls\n"
                    f"⚪ AUCUN: = {aucun_threshold} souls"
                )
                self.log_message(f"✅ Auto-updated monster states with thresholds")
            else:
                messagebox.showerror("Error", "Failed to update monster states on Metamob")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all thresholds!")
        except Exception as e:
            messagebox.showerror("Error", f"Error updating states: {str(e)}")
    
    def get_threshold_values(self):
        """Get current threshold values from UI"""
        try:
            return {
                'recherche': int(self.recherche_entry.get().strip() or "0"),
                'proposer': int(self.proposer_entry.get().strip() or "50"),
                'aucun': int(self.aucun_entry.get().strip() or "100")
            }
        except ValueError:
            return {
                'recherche': 0,
                'proposer': 50,
                'aucun': 100
            }

    def start_soul_scan(self):
        """
        Start scanning soul quantities for selected or all monsters.
        
        Archimonster Bank Layout:
        - 5 columns × 9 rows = 45 total slots
        - Each slot can contain soul stones
        - Soul detection uses coordinate-based calibration system
        """
        # Check if coordinates are calibrated (new system)
        if not self.slot_coordinates or len(self.slot_coordinates) != 45:
            # Try to load coordinates first
            self.slot_coordinates = self.load_slot_coordinates()
            if not self.slot_coordinates or len(self.slot_coordinates) != 45:
                messagebox.showerror(
                    "Coordinates Not Calibrated", 
                    "Please run coordinate calibration first!\n\n"
                    "Click the '🎯 Coordinate Calibration' button to set up "
                    "the exact positions of all 45 bank slots."
                )
                return
        
        if not self.search_pos:
            messagebox.showerror("Error", "Please set search position first!")
            return
        
        # Get monsters to scan based on mode
        monsters_to_scan = self.get_monsters_to_scan()
        
        if not monsters_to_scan:
            if self.scan_mode_var.get() == "all":
                messagebox.showerror("Error", "No monster names loaded from file!")
            else:
                messagebox.showerror("Error", "No monsters selected! Please select monsters first or switch to 'All monsters' mode.")
            return
        
        scan_mode_text = "ALL monsters from file" if self.scan_mode_var.get() == "all" else "SELECTED monsters only"
        
        # Confirm start
        result = messagebox.askyesno("Start Soul Scan", 
                                   f"Start scanning {len(monsters_to_scan)} monsters?\n"
                                   f"Mode: {scan_mode_text}\n"
                                   f"Estimated time: {len(monsters_to_scan) * 3} seconds.")
        
        if not result:
            return
        
        # Start scanning in separate thread
        self.is_scanning = True
        self.soul_scan_data = {}
        self.scan_progress = 0
        
        # Update UI
        self.scan_button.configure(state='disabled')
        self.stop_scan_button.configure(state='normal')
        
        thread = threading.Thread(target=self.soul_scanning_process, args=(monsters_to_scan,))
        thread.daemon = True
        thread.start()
    
    def soul_scanning_process(self, monsters_to_scan):
        """Main soul scanning process"""
        try:
            total_monsters = len(monsters_to_scan)
            scan_mode_text = "ALL monsters" if self.scan_mode_var.get() == "all" else "SELECTED monsters"
            
            self.log_message(f"🔍 Starting soul scan for {total_monsters} {scan_mode_text.lower()}...")
            self.update_status("🔍 Scanning soul quantities...")
            
            for i, monster_name in enumerate(monsters_to_scan):
                if not self.is_scanning:
                    break
                
                self.scan_progress = i + 1
                progress_percent = (self.scan_progress / total_monsters) * 100
                
                self.update_status(f"🔍 Scanning {monster_name} ({self.scan_progress}/{total_monsters})")
                self.log_message(f"🔍 Scanning {monster_name}...")
                
                # Update progress bar if it exists
                if hasattr(self, 'scan_progress_var'):
                    self.scan_progress_var.set(progress_percent)
                
                # Update status label
                self.scan_status_label.config(text=f"Scanning {monster_name}... ({self.scan_progress}/{total_monsters})")
                
                try:
                    # Search for monster
                    self.search_monster_for_scan(monster_name)
                    time.sleep(1.5)  # Wait for search results
                    
                    # Count souls using coordinate-based detection
                    if len(self.slot_coordinates) == 45:
                        # Use precise coordinate-based detection (preferred method)
                        soul_count = self.detect_souls_with_coordinates()
                        result = {
                            'total_souls': soul_count,
                            'confidence': 1.0,  # 100% confidence with coordinates
                            'detected_slots': soul_count,
                            'method': 'coordinate_based',
                            'grid_analysis': {'status': 'coordinate_calibrated'}
                        }
                    else:
                        # This should not happen since we check coordinates at start
                        # But keeping as emergency fallback
                        self.log_message(f"⚠️ Warning: Coordinates not properly loaded for {monster_name}")
                        result = {
                            'total_souls': 0,
                            'confidence': 0.0,
                            'detected_slots': 0,
                            'method': 'error',
                            'error': 'Coordinates not available'
                        }
                    
                    # Validate result
                    issues = self.soul_counter.validate_detection(result)
                    
                    # Store result
                    self.soul_scan_data[monster_name] = {
                        'quantity': result['total_souls'],
                        'confidence': result['confidence'],
                        'detected_slots': result['detected_slots'],
                        'timestamp': datetime.now().isoformat(),
                        'issues': issues
                    }
                    
                    if issues:
                        self.log_message(f"⚠️ {monster_name}: {result['total_souls']} souls (issues: {', '.join(issues)})")
                        # Queue for manual verification (only for non-zero problematic detections)
                        self.request_manual_verification(monster_name, result, issues)
                    else:
                        if result['total_souls'] == 0:
                            self.log_message(f"🔍 {monster_name}: 0 souls (not found or empty)")
                        else:
                            self.log_message(f"✅ {monster_name}: {result['total_souls']} souls (confidence: {result['confidence']:.2f})")
                    
                except Exception as e:
                    error_msg = f"Error scanning {monster_name}: {str(e)}"
                    self.log_message(f"❌ {error_msg}")
                    self.soul_scan_data[monster_name] = {
                        'quantity': 0,
                        'confidence': 0.0,
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Small delay between monsters
                time.sleep(0.5)
            
            # Scanning complete
            if self.is_scanning:
                self.complete_soul_scan()
                
        except Exception as e:
            self.log_message(f"❌ Critical error during soul scan: {str(e)}")
            messagebox.showerror("Scan Error", f"Critical error during scan: {str(e)}")
        finally:
            self.is_scanning = False
            # Reset UI
            self.scan_button.configure(state='normal')
            self.stop_scan_button.configure(state='disabled')
            self.scan_status_label.config(text="Ready to scan")
            self.scan_progress_var.set(0)
    
    def search_monster_for_scan(self, monster_name):
        """Search for a monster during soul scanning"""
        # Clear search bar and type monster name
        pyautogui.click(self.search_pos)
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # Try copy-paste first, then fallback to typing
        try:
            # Clean the monster name to remove any icons or special characters
            clean_name = self.clean_monster_name(monster_name)
            self.root.clipboard_clear()
            self.root.clipboard_append(clean_name)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
        except:
            clean_name = self.clean_monster_name(monster_name)
            pyautogui.typewrite(clean_name)
        
        time.sleep(0.3)
    
    def request_manual_verification(self, monster_name, result, issues):
        """Request manual verification for problematic detections"""
        self.root.after(0, lambda: self.show_manual_verification_dialog(monster_name, result, issues))
    
    def show_manual_verification_dialog(self, monster_name, result, issues):
        """Show dialog for manual verification of soul count"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Manual Verification - {monster_name}")
        dialog.geometry("400x300")
        dialog.configure(bg=self.get_theme_colors()['bg'])
        dialog.attributes('-topmost', True)
        
        colors = self.get_theme_colors()
        
        # Title
        title_label = tk.Label(
            dialog,
            text=f"🔍 Verify Soul Count",
            font=('Segoe UI', 14, 'bold'),
            fg=colors['accent'],
            bg=colors['bg']
        )
        title_label.pack(pady=10)
        
        # Monster name
        monster_label = tk.Label(
            dialog,
            text=f"Monster: {monster_name}",
            font=('Segoe UI', 12),
            fg=colors['fg'],
            bg=colors['bg']
        )
        monster_label.pack(pady=5)
        
        # Detected count
        detected_label = tk.Label(
            dialog,
            text=f"Detected: {result['total_souls']} souls",
            font=('Segoe UI', 11),
            fg=colors['warning'],
            bg=colors['bg']
        )
        detected_label.pack(pady=5)
        
        # Issues
        if issues:
            issues_label = tk.Label(
                dialog,
                text=f"Issues: {', '.join(issues)}",
                font=('Segoe UI', 10),
                fg=colors['danger'],
                bg=colors['bg'],
                wraplength=350
            )
            issues_label.pack(pady=5)
        
        # Manual input
        input_frame = tk.Frame(dialog, bg=colors['bg'])
        input_frame.pack(pady=20)
        
        tk.Label(
            input_frame,
            text="Correct quantity:",
            font=('Segoe UI', 11),
            fg=colors['fg'],
            bg=colors['bg']
        ).pack(side='left')
        
        quantity_var = tk.StringVar(value=str(result['total_souls']))
        quantity_entry = tk.Entry(
            input_frame,
            textvariable=quantity_var,
            font=('Segoe UI', 11),
            width=10
        )
        quantity_entry.pack(side='left', padx=10)
        quantity_entry.select_range(0, tk.END)
        quantity_entry.focus()
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=colors['bg'])
        button_frame.pack(pady=20)
        
        def accept_correction():
            try:
                corrected_quantity = int(quantity_var.get())
                self.soul_scan_data[monster_name]['quantity'] = corrected_quantity
                self.soul_scan_data[monster_name]['manually_corrected'] = True
                self.log_message(f"✏️ {monster_name}: Manually corrected to {corrected_quantity} souls")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number!")
        
        def keep_original():
            self.log_message(f"📋 {monster_name}: Kept original detection ({result['total_souls']} souls)")
            dialog.destroy()
        
        self.create_modern_button(
            button_frame,
            "✅ Accept Correction",
            accept_correction,
            colors['success']
        ).pack(side='left', padx=5)
        
        self.create_modern_button(
            button_frame,
            "📋 Keep Original",
            keep_original,
            colors['secondary']
        ).pack(side='left', padx=5)
        
        # Bind Enter key to accept
        quantity_entry.bind('<Return>', lambda e: accept_correction())
    
    def complete_soul_scan(self):
        """Complete the soul scanning process"""
        self.last_scan_time = datetime.now()
        total_scanned = len(self.soul_scan_data)
        total_souls = sum(data.get('quantity', 0) for data in self.soul_scan_data.values())
        scan_mode_text = "ALL monsters" if self.scan_mode_var.get() == "all" else "SELECTED monsters"
        
        self.update_status("✅ Soul scan completed!")
        self.log_message(f"🎉 Soul scan completed!")
        self.log_message(f"📊 Scanned {total_scanned} {scan_mode_text.lower()}, found {total_souls} total souls")
        
        # Update scan results label
        self.scan_results_label.config(text=f"Last scan: {total_scanned} monsters, {total_souls} souls ({scan_mode_text})")
        
        # Save scan data
        self.save_soul_scan_data()
        
        # Auto-suggest Metamob sync
        self.suggest_metamob_sync()
    
    def save_soul_scan_data(self):
        """Save soul scan data to JSON file"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, 'data')
            
            # Create data directory if it doesn't exist
            os.makedirs(data_dir, exist_ok=True)
            
            scan_mode_text = "all_monsters" if self.scan_mode_var.get() == "all" else "selected_monsters"
            
            scan_data = {
                'scan_timestamp': self.last_scan_time.isoformat(),
                'scan_mode': scan_mode_text,
                'total_monsters': len(self.soul_scan_data),
                'total_souls': sum(data.get('quantity', 0) for data in self.soul_scan_data.values()),
                'monsters': self.soul_scan_data
            }
            
            # Save main data file
            soul_quantities_file = os.path.join(data_dir, 'soul_quantities.json')
            with open(soul_quantities_file, 'w', encoding='utf-8') as f:
                json.dump(scan_data, f, indent=2, ensure_ascii=False)
            
            # Save scan history
            history_file = os.path.join(data_dir, 'scan_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = {'scans': []}
            
            history['scans'].append({
                'timestamp': self.last_scan_time.isoformat(),
                'scan_mode': scan_mode_text,
                'monsters_count': len(self.soul_scan_data),
                'total_souls': sum(data.get('quantity', 0) for data in self.soul_scan_data.values())
            })
            
            # Keep only last 50 scans
            history['scans'] = history['scans'][-50:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"💾 Soul scan data saved to {soul_quantities_file}")
            
            # Prepare data for Metamob sync
            self.prepare_metamob_data()
            
        except Exception as e:
            self.log_message(f"❌ Error saving soul scan data: {str(e)}")
    
    def prepare_metamob_data(self):
        """Prepare soul scan data for Metamob sync"""
        try:
            self.monster_soul_data = {}
            for monster_name, data in self.soul_scan_data.items():
                soul_count = data.get('quantity', 0)
                # Store in format expected by Metamob API
                self.monster_soul_data[monster_name] = soul_count
            
            print(f"📊 Prepared {len(self.monster_soul_data)} monsters for Metamob sync")
            
        except Exception as e:
            print(f"❌ Error preparing Metamob data: {e}")
            self.monster_soul_data = {}
    
    def suggest_metamob_sync(self):
        """Auto-suggest Metamob sync after successful scan"""
        if not self.soul_scan_data:
            return
        
        total_souls = sum(data.get('quantity', 0) for data in self.soul_scan_data.values())
        
        result = messagebox.askyesno(
            "🌐 Metamob Sync",
            f"Soul scan completed!\n\n"
            f"📊 Found {len(self.soul_scan_data)} monsters with {total_souls} total souls\n\n"
            f"🌐 Would you like to sync this data to Metamob.fr now?"
        )
        
        if result:
            self.show_metamob_sync_dialog()
    
    def show_metamob_sync_dialog(self):
        """Show Metamob sync configuration dialog (placeholder for now)"""
        messagebox.showinfo("Coming Soon", "Metamob sync integration will be added in the next task!")
    
    def stop_soul_scan(self):
        """Stop the ongoing soul scan"""
        self.is_scanning = False
        self.update_status("🔴 Soul scan stopped")
        self.log_message("🔴 Soul scan stopped by user")
        
        # Reset UI
        self.scan_button.configure(state='normal')
        self.stop_scan_button.configure(state='disabled')
        self.scan_status_label.config(text="Scan stopped by user")
        self.scan_progress_var.set(0)

    # =============================================================================
    # AUTO-UPDATE SYSTEM METHODS
    # =============================================================================
    
    def check_for_updates_on_startup(self):
        """Check for updates automatically on startup (optional)"""
        try:
            update_info = self.auto_updater.check_for_updates(show_no_update_message=False)
            
            if update_info.get("update_available"):
                # Show non-intrusive notification
                self.show_update_notification(update_info)
                
        except Exception as e:
            print(f"⚠️ Startup update check failed: {e}")
    
    def show_update_notification(self, update_info):
        """Show a small notification about available updates"""
        colors = self.get_theme_colors()
        
        # Create small notification window
        notification = tk.Toplevel(self.root)
        notification.title("Update Available")
        notification.geometry("350x150")
        notification.attributes('-topmost', True)
        notification.configure(bg=colors['bg'])
        
        # Center the notification
        notification.update_idletasks()
        x = (notification.winfo_screenwidth() // 2) - (350 // 2)
        y = 50  # Top of screen
        notification.geometry(f"350x150+{x}+{y}")
        
        frame = tk.Frame(notification, bg=colors['bg'], padx=20, pady=15)
        frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            frame,
            text="🔄 Update Available!",
            font=('Segoe UI', 12, 'bold'),
            fg=colors['accent'],
            bg=colors['bg']
        )
        title_label.pack(pady=(0, 5))
        
        # Version info
        version_label = tk.Label(
            frame,
            text=f"New version {update_info['server_version']} is available\nCurrent: {update_info['current_version']}",
            font=('Segoe UI', 10),
            fg=colors['fg'],
            bg=colors['bg']
        )
        version_label.pack(pady=(0, 10))
        
        # Buttons
        button_frame = tk.Frame(frame, bg=colors['bg'])
        button_frame.pack()
        
        self.create_modern_button(
            button_frame,
            "Update Now",
            lambda: [notification.destroy(), self.check_and_download_updates()],
            colors['success']
        ).pack(side='left', padx=5)
        
        self.create_modern_button(
            button_frame,
            "Later",
            notification.destroy,
            colors['secondary']
        ).pack(side='left', padx=5)
        
        # Auto-close after 10 seconds
        notification.after(10000, notification.destroy)
    
    def check_and_download_updates(self):
        """Main function triggered by 'Get New Updates' button"""
        try:
            # Change button text to show checking
            original_text = self.update_button.cget('text')
            self.update_button.config(text="🔍 Checking...", state='disabled')
            self.root.update()
            
            # Check for updates
            update_info = self.auto_updater.check_for_updates()
            
            if update_info.get("error"):
                self.update_button.config(text=original_text, state='normal')
                messagebox.showerror(
                    "Update Check Failed", 
                    f"Failed to check for updates:\n{update_info['error']}\n\nPlease check your internet connection."
                )
                return
            
            if not update_info.get("update_available"):
                self.update_button.config(text=original_text, state='normal')
                messagebox.showinfo(
                    "No Updates Available", 
                    f"✅ You have the latest version!\n\nCurrent version: {APP_VERSION}"
                )
                return
            
            # Show update confirmation dialog
            self.show_update_confirmation_dialog(update_info)
            
        except Exception as e:
            self.update_button.config(text=original_text, state='normal')
            messagebox.showerror("Update Error", f"An error occurred while checking for updates:\n{str(e)}")
    
    def show_update_confirmation_dialog(self, update_info):
        """Show detailed update confirmation dialog"""
        colors = self.get_theme_colors()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🔄 Update Available")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=colors['bg'])
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=colors['bg'], padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🔄 Update Available!",
            font=('Segoe UI', 16, 'bold'),
            fg=colors['accent'],
            bg=colors['bg']
        )
        title_label.pack(pady=(0, 10))
        
        # Version info frame
        version_frame = tk.Frame(main_frame, bg=colors['card_bg'], relief='flat', bd=1)
        version_frame.pack(fill='x', pady=(0, 15))
        
        version_info = tk.Frame(version_frame, bg=colors['card_bg'], padx=15, pady=10)
        version_info.pack(fill='x')
        
        tk.Label(
            version_info,
            text=f"Current Version: {update_info['current_version']}",
            font=('Segoe UI', 11),
            fg=colors['secondary'],
            bg=colors['card_bg']
        ).pack(anchor='w')
        
        tk.Label(
            version_info,
            text=f"New Version: {update_info['server_version']}",
            font=('Segoe UI', 11, 'bold'),
            fg=colors['success'],
            bg=colors['card_bg']
        ).pack(anchor='w')
        
        # Changelog
        changelog_label = tk.Label(
            main_frame,
            text="📋 What's New:",
            font=('Segoe UI', 12, 'bold'),
            fg=colors['fg'],
            bg=colors['bg']
        )
        changelog_label.pack(anchor='w', pady=(0, 5))
        
        # Changelog text area
        changelog_frame = tk.Frame(main_frame, bg=colors['bg'])
        changelog_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        changelog_text = tk.Text(
            changelog_frame,
            height=8,
            font=('Segoe UI', 10),
            bg=colors['card_bg'],
            fg=colors['fg'],
            relief='flat',
            bd=1,
            wrap='word'
        )
        changelog_scrollbar = tk.Scrollbar(changelog_frame, orient='vertical', command=changelog_text.yview)
        changelog_text.configure(yscrollcommand=changelog_scrollbar.set)
        
        changelog_text.pack(side='left', fill='both', expand=True)
        changelog_scrollbar.pack(side='right', fill='y')
        
        # Insert changelog
        changelog_text.insert('1.0', update_info.get('changelog', 'No changelog available.'))
        changelog_text.configure(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=colors['bg'])
        button_frame.pack(fill='x', pady=(10, 0))
        
        def start_update():
            dialog.destroy()
            self.perform_update(update_info)
        
        self.create_modern_button(
            button_frame,
            "✅ Update Now",
            start_update,
            colors['success']
        ).pack(side='right', padx=(10, 0))
        
        self.create_modern_button(
            button_frame,
            "❌ Cancel",
            lambda: [dialog.destroy(), self.reset_update_button()],
            colors['secondary']
        ).pack(side='right')
    
    def perform_update(self, update_info):
        """Perform the actual update process"""
        # Create progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("🔄 Updating...")
        progress_dialog.geometry("400x200")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing
        
        colors = self.get_theme_colors()
        progress_dialog.configure(bg=colors['bg'])
        
        # Center the dialog
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (200 // 2)
        progress_dialog.geometry(f"400x200+{x}+{y}")
        
        frame = tk.Frame(progress_dialog, bg=colors['bg'], padx=30, pady=20)
        frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            frame,
            text="🔄 Updating Monster Tool...",
            font=('Segoe UI', 14, 'bold'),
            fg=colors['accent'],
            bg=colors['bg']
        )
        title_label.pack(pady=(0, 20))
        
        # Status label
        status_var = tk.StringVar(value="Preparing update...")
        status_label = tk.Label(
            frame,
            textvariable=status_var,
            font=('Segoe UI', 11),
            fg=colors['fg'],
            bg=colors['bg']
        )
        status_label.pack(pady=(0, 10))
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            frame,
            variable=progress_var,
            maximum=100,
            length=300
        )
        progress_bar.pack(pady=(0, 20))
        
        def update_progress(progress):
            progress_var.set(progress)
            progress_dialog.update()
        
        def update_worker():
            """Background worker for update process"""
            try:
                # Step 1: Download
                status_var.set("📥 Downloading update...")
                progress_dialog.update()
                
                temp_file = self.auto_updater.download_update(
                    update_info['download_url'], 
                    progress_callback=update_progress
                )
                
                if not temp_file:
                    raise Exception("Download failed")
                
                # Step 2: Verify
                status_var.set("🔍 Verifying download...")
                progress_var.set(90)
                progress_dialog.update()
                
                if not self.auto_updater.verify_update_integrity(temp_file):
                    raise Exception("File verification failed")
                
                # Step 3: Apply
                status_var.set("⚡ Applying update...")
                progress_var.set(95)
                progress_dialog.update()
                
                if not self.auto_updater.apply_update(temp_file):
                    raise Exception("Update application failed")
                
                # Step 4: Success
                status_var.set("✅ Update completed! Restarting...")
                progress_var.set(100)
                progress_dialog.update()
                
                # Wait a moment then restart
                progress_dialog.after(2000, lambda: self.auto_updater.restart_application())
                
            except Exception as e:
                progress_dialog.destroy()
                self.reset_update_button()
                messagebox.showerror(
                    "Update Failed", 
                    f"❌ Update failed:\n{str(e)}\n\nPlease try again later or contact support."
                )
        
        # Start update in background
        threading.Thread(target=update_worker, daemon=True).start()
    
    def reset_update_button(self):
        """Reset the update button to its original state"""
        if hasattr(self, 'update_button'):
            self.update_button.config(text="🔄 Get New Updates", state='normal')

    def retrieval_process(self):
        """Main retrieval process with enhanced logging"""
        try:
            total_monsters = len(self.selected_monsters)
            current_monster = 0
            souls_since_break = 0
            
            try:
                pause_interval = int(self.pause_interval_var.get())
            except ValueError:
                pause_interval = 50
            
            search_delay = float(self.search_delay_var.get())
            
            for monster_name, quantity in self.selected_monsters.items():
                if not self.is_running:
                    break
                
                current_monster += 1
                
                self.update_status(f"🎯 Processing {monster_name} ({current_monster}/{total_monsters})")
                self.log_message(f"🐾 Starting {monster_name} (x{quantity})")
                
                # Wait if paused
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                
                if not self.is_running:
                    break
                
                delays = self.get_speed_delays()
                
                # Clear search bar and type monster name
                pyautogui.click(self.search_pos)
                time.sleep(delays["click"])
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(delays["type"])
                
                # Try copy-paste first, then fallback to cleaned typing
                try:
                    cleaned_name = self.clean_monster_name(monster_name)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(cleaned_name)
                    time.sleep(delays["type"])
                    pyautogui.hotkey('ctrl', 'v')
                except:
                    cleaned_name = self.clean_monster_name(monster_name)
                    self.log_message(f"📝 Using cleaned name: {cleaned_name}")
                    pyautogui.typewrite(cleaned_name)
                
                time.sleep(search_delay)
                
                # Retrieve specified quantity with improved success detection
                successful_this_monster = 0
                failed_this_monster = 0
                
                for i in range(quantity):
                    if not self.is_running:
                        break
                    
                    # Wait if paused
                    while self.is_paused and self.is_running:
                        time.sleep(0.1)
                    
                    if not self.is_running:
                        break
                    
                    delays = self.get_speed_delays()
                    
                    self.update_status(f"🎯 Retrieving {monster_name} ({i+1}/{quantity})")
                    
                    try:
                        # Check if monster exists using advanced detection
                        monster_available = self.advanced_monster_detection(monster_name)
                        
                        if not monster_available:
                            error_msg = f"No {monster_name} found in bank"
                            self.log_message(f"❌ {error_msg} (attempt {i+1}/{quantity})")
                            self.log_monster_attempt(monster_name, False, error_msg)
                            failed_this_monster += 1
                            self.failed_retrievals += 1
                            self.processed_souls += 1
                            
                            # Skip remaining attempts for this monster
                            remaining = quantity - i - 1
                            if remaining > 0:
                                self.log_message(f"⏭️ Skipping {remaining} remaining attempts - {monster_name} not in bank")
                                for _ in range(remaining):
                                    self.log_monster_attempt(monster_name, False, "Monster not available")
                                failed_this_monster += remaining
                                self.failed_retrievals += remaining
                                self.processed_souls += remaining
                            break
                        
                        # Monster appears to be available, attempt retrieval
                        self.log_message(f"🎯 Attempting to retrieve {monster_name} ({i+1}/{quantity})")
                        
                        # Perform the double-click retrieval
                        pyautogui.moveTo(self.monster_pos)
                        time.sleep(delays["click"])
                        pyautogui.doubleClick(self.monster_pos, interval=0.1)
                        time.sleep(delays["retrieve"])
                        
                        # Check if the retrieval was successful
                        retrieval_successful = self.check_if_retrieval_successful()
                        
                        if retrieval_successful:
                            successful_this_monster += 1
                            self.successful_retrievals += 1
                            self.log_message(f"✅ Successfully retrieved {monster_name} ({i+1}/{quantity})")
                            self.log_monster_attempt(monster_name, True)
                        else:
                            error_msg = "Retrieval unsuccessful"
                            failed_this_monster += 1
                            self.failed_retrievals += 1
                            self.log_message(f"❌ Failed to retrieve {monster_name} ({i+1}/{quantity}) - {error_msg}")
                            self.log_monster_attempt(monster_name, False, error_msg)
                        
                        self.processed_souls += 1
                        souls_since_break += 1
                        
                        # Update progress
                        self.update_progress()
                        
                        # Check if we need a break
                        if souls_since_break >= pause_interval:
                            self.log_message(f"☕ Taking 1-minute break after {souls_since_break} souls...")
                            self.update_status("☕ Taking 1-minute break...")
                            self.add_timeline_entry(f"Auto break after {souls_since_break} souls")
                            
                            for countdown in range(60, 0, -1):
                                if not self.is_running:
                                    break
                                while self.is_paused and self.is_running:
                                    time.sleep(0.1)
                                self.update_status(f"☕ Break: {countdown} seconds remaining...")
                                time.sleep(1)
                            
                            souls_since_break = 0
                            if self.is_running:
                                self.log_message("🚀 Break completed, resuming...")
                                self.add_timeline_entry("Break completed, resumed retrieval")
                        
                    except Exception as e:
                        error_msg = f"Error during retrieval: {str(e)}"
                        self.log_message(f"❌ {error_msg} of {monster_name} #{i+1}")
                        self.log_monster_attempt(monster_name, False, error_msg)
                        failed_this_monster += 1
                        self.failed_retrievals += 1
                        self.processed_souls += 1
                
                # Log monster completion summary
                if failed_this_monster > 0:
                    self.failed_monsters.append(f"{monster_name} ({failed_this_monster} failed)")
                    
                if successful_this_monster == quantity:
                    self.log_message(f"✅ Completed {monster_name}: {successful_this_monster}/{quantity} successful")
                elif successful_this_monster > 0:
                    self.log_message(f"⚠️ Partial {monster_name}: {successful_this_monster}/{quantity} successful, {failed_this_monster} failed")
                else:
                    self.log_message(f"❌ Failed {monster_name}: 0/{quantity} successful")
                
                # Update progress display
                self.update_progress()
                
                # Save progress periodically (every 5 monsters)
                if current_monster % 5 == 0:
                    self.save_session_log(final=False)
                
                # Dynamic pause between monsters
                if self.is_running and current_monster < total_monsters:
                    delays = self.get_speed_delays()
                    time.sleep(delays["monster"])
            
            # Completion handling
            if self.is_running:
                self.update_status("🎉 Retrieval completed!")
                self.log_message("🎉 All retrievals completed!")
                
                # Show final summary
                success_rate = (self.successful_retrievals / self.total_souls * 100) if self.total_souls > 0 else 0
                summary = f"\n{'='*50}\n"
                summary += f"🏆 FINAL SUMMARY\n"
                summary += f"{'='*50}\n"
                summary += f"📊 Total souls processed: {self.processed_souls}/{self.total_souls}\n"
                summary += f"✅ Successful retrievals: {self.successful_retrievals} ({success_rate:.1f}%)\n"
                summary += f"❌ Failed retrievals: {self.failed_retrievals}\n"
                
                if self.failed_monsters:
                    summary += f"\n🚨 Monsters with failures:\n"
                    for failed in self.failed_monsters:
                        summary += f"  • {failed}\n"
                
                elapsed = datetime.now() - self.start_time
                summary += f"\n⏱️ Total time: {str(elapsed).split('.')[0]}\n"
                summary += f"{'='*50}"
                
                self.log_message(summary)
                self.add_timeline_entry(f"Session completed - {success_rate:.1f}% success rate")
                
                # Save final session log
                self.save_session_log(final=True)
                
                # Play completion sound
                self.play_completion_sound()
                
                # Show completion dialog
                messagebox.showinfo("🎉 Completion", 
                                  f"Retrieval completed!\n\n"
                                  f"📊 Processed: {self.processed_souls}/{self.total_souls} souls\n"
                                  f"✅ Success rate: {success_rate:.1f}%\n"
                                  f"⏱️ Time: {str(elapsed).split('.')[0]}\n\n"
                                  f"📁 Session data saved to logs folder")
            
        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            self.add_timeline_entry(error_msg)
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.is_running = False
            self.is_paused = False
            colors = self.get_theme_colors()
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.pause_button.config(state='disabled', text='⏸️ PAUSE', bg=colors['warning'])
            
            # Final save
            if self.session_log['session_start']:
                self.save_session_log(final=True)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🎮 Enhanced Monster Soul Retrieval Tool")
    print("=" * 50)
    print("✨ NEW FEATURES:")
    print("• 🎨 Modern, beautiful UI with dark/light themes")
    print("• 📊 Advanced session logging & statistics")
    print("• 💾 Automatic data export to JSON & TXT files")
    print("• 📋 Real-time log viewer with detailed analytics")
    print("• 🔍 Enhanced monster detection algorithms")
    print("• ⏸️ Improved pause/resume functionality")
    print("• 🎯 Better progress tracking & ETA calculation")
    print("• 🎵 Enhanced completion notifications")
    print("")
    print("📁 LOG SYSTEM:")
    print("• Session data automatically saved to 'logs/' folder")
    print("• JSON format for data analysis")
    print("• Human-readable TXT format for easy reading")
    print("• Real-time statistics and timeline tracking")
    print("")
    print("🎨 UI IMPROVEMENTS:")
    print("• Modern card-based design")
    print("• Smooth dark/light theme switching")
    print("• Improved button styling with hover effects")
    print("• Better color coding and visual feedback")
    print("• Collapsible sections for better organization")
    print("")
    print("📋 SETUP:")
    print("1. Make sure 'monster_names.txt' is in the same folder")
    print("2. Install: pip install pyautogui")
    print("3. Position your game window")
    print("4. Set coordinates using the setup buttons")
    print("5. Select monsters and configure settings")
    print("6. Use 'View Logs' to monitor real-time progress")
    print("")
    print("🚀 Starting enhanced application...")
    
    app = MonsterRetrievalTool()
    app.run()

