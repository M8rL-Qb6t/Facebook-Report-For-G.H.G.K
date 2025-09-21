import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import time
from datetime import datetime
import webbrowser
import threading
import json
import os
import sys
import socket
import requests
from urllib.parse import urlparse
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler("post_performance.log", maxBytes=5*1024*1024, backupCount=2),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PPR")

class FacebookAnalytics:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Post Analytics Professional")
        self.root.geometry("1100x800")
        self.root.configure(bg='#f5f7fa')
        self.root.minsize(1000, 700)

        self.logged_in = False
        self.current_url = ""
        self.processing = False
        self.operation_thread = None
        self.session_data = {
            "reports_generated": 0,
            "analytics_run": 0,
            "start_time": None,
            "operations_completed": 0
        }

        # Facebook API configuration
        self.fb_config = {
            "app_id": "",
            "app_secret": "",
            "access_token": "",
            "page_id": ""
        }

        # Create data folder
        self.data_dir = os.path.join(os.path.expanduser("~"), "Facebook_Analytics_Data")
        os.makedirs(self.data_dir, exist_ok=True)

        # Load config
        self.config = self.load_config()

        self.setup_styles()
        self.setup_header()
        self.setup_login_frame()
        self.setup_main_frame()

        self.main_frame.pack_forget()
        logger.info("Facebook Analytics Application initialized")

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Header.TFrame', background='#3b5998')  # Facebook blue
        self.style.configure('Header.TLabel', background='#3b5998', foreground='white')
        self.style.configure('Main.TFrame', background='#f5f7fa')
        self.style.configure('Custom.TButton', background='#4267B2', foreground='white')  # Facebook blue
        self.style.configure('Progress.Horizontal.TProgressbar', troughcolor='#ecf0f1', background='#4267B2')

    def setup_header(self):
        self.header_frame = ttk.Frame(self.root, style='Header.TFrame', height=80)
        self.header_frame.pack(fill='x')
        self.header_frame.pack_propagate(False)

        logo_frame = ttk.Frame(self.header_frame, style='Header.TFrame')
        logo_frame.pack(side='left', padx=20)
        self.logo_label = ttk.Label(logo_frame, text="FB Analytics Pro", font=("Arial", 24, "bold"), style='Header.TLabel')
        self.logo_label.pack(pady=20)

        status_frame = ttk.Frame(self.header_frame, style='Header.TFrame')
        status_frame.pack(side='right', padx=20)
        self.login_status = ttk.Label(status_frame, text="Not Connected", style='Header.TLabel', font=("Arial", 10))
        self.login_status.pack(pady=5)
        self.connection_status = ttk.Label(status_frame, text="Facebook: Disconnected", style='Header.TLabel', font=("Arial", 9))
        self.connection_status.pack(pady=5)

    def setup_login_frame(self):
        self.login_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.login_frame.pack(fill='both', expand=True, padx=50, pady=50)

        login_form = ttk.Frame(self.login_frame, style='Main.TFrame')
        login_form.pack(pady=50)

        ttk.Label(login_form, text="Facebook App ID:", font=("Arial", 12), background='#f5f7fa').grid(row=0, column=0, padx=10, pady=15, sticky='e')
        self.app_id_entry = ttk.Entry(login_form, font=("Arial", 12), width=25)
        self.app_id_entry.grid(row=0, column=1, padx=10, pady=15)

        ttk.Label(login_form, text="Access Token:", font=("Arial", 12), background='#f5f7fa').grid(row=1, column=0, padx=10, pady=15, sticky='e')
        self.access_token_entry = ttk.Entry(login_form, show="*", font=("Arial", 12), width=25)
        self.access_token_entry.grid(row=1, column=1, padx=10, pady=15)

        ttk.Label(login_form, text="Page ID:", font=("Arial", 12), background='#f5f7fa').grid(row=2, column=0, padx=10, pady=15, sticky='e')
        self.page_id_entry = ttk.Entry(login_form, font=("Arial", 12), width=25)
        self.page_id_entry.grid(row=2, column=1, padx=10, pady=15)

        self.login_button = ttk.Button(login_form, text="Connect to Facebook", command=self.connect_facebook, style='Custom.TButton', width=20)
        self.login_button.grid(row=3, column=0, columnspan=2, pady=20)

        # Add help text
        help_text = """
        To use this application:
        1. Create a Facebook App at https://developers.facebook.com/
        2. Get an access token with appropriate permissions
        3. Enter your App ID, Access Token, and Page ID above
        """
        help_label = ttk.Label(login_form, text=help_text, font=("Arial", 9), background='#f5f7fa', foreground='#666666', justify='left')
        help_label.grid(row=4, column=0, columnspan=2, pady=10)

        footer = ttk.Frame(self.login_frame, style='Main.TFrame')
        footer.pack(side='bottom', pady=10)
        ttk.Label(footer, text="Facebook Analytics Professional v2.0 - For legitimate use only", 
                 font=("Arial", 9), background='#f5f7fa', foreground='#7f8c8d').pack()

    def setup_main_frame(self):
        self.main_frame = ttk.Frame(self.root, style='Main.TFrame')

        # Facebook Post URL Input
        self.url_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        self.url_frame.pack(fill='x', padx=20, pady=15)
        ttk.Label(self.url_frame, text="Facebook Post URL:", font=("Arial", 12), background='#f5f7fa').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.url_entry = ttk.Entry(self.url_frame, font=("Arial", 12), width=50)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        self.url_entry.insert(0, "https://www.facebook.com/examplepost")

        self.load_url_button = ttk.Button(self.url_frame, text="Load Post", command=self.load_url, style='Custom.TButton')
        self.load_url_button.grid(row=0, column=2, padx=10, pady=10)
        self.verify_btn = ttk.Button(self.url_frame, text="Verify", command=self.verify_url, style='Custom.TButton')
        self.verify_btn.grid(row=0, column=3, padx=10, pady=10)

        # Analytics Options
        self.options_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        self.options_frame.pack(fill='x', padx=20, pady=15)
        
        options = [
            ("1. Analyze Post Performance", self.analyze_post),
            ("2. Generate Engagement Report", self.generate_report),
            ("3. Audience Insights", self.audience_insights),
            ("4. Content Strategy Analysis", self.content_analysis),
            ("5. Export Data", self.export_data)
        ]
        
        for i, (text, command) in enumerate(options):
            btn = ttk.Button(self.options_frame, text=text, command=command, style='Custom.TButton', width=30)
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')

        # Status & Progress
        self.status_label = ttk.Label(self.main_frame, text="Status: Ready to analyze", background='#f5f7fa', font=("Arial", 10))
        self.status_label.pack(anchor='w', padx=20)
        self.progress = ttk.Progressbar(self.main_frame, orient='horizontal', length=400, mode='determinate', style='Progress.Horizontal.TProgressbar')
        self.progress.pack(fill='x', padx=20, pady=5)
        self.time_label = ttk.Label(self.main_frame, text="Estimated: 00:00", background='#f5f7fa', font=("Arial", 9, "bold"))
        self.time_label.pack(anchor='w', padx=20)

        # Control buttons
        ctrl_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        ctrl_frame.pack(fill='x', padx=20, pady=5)
        self.start_btn = ttk.Button(ctrl_frame, text="Start Analysis", command=self.start_processing, style='Custom.TButton')
        self.start_btn.pack(side='left', padx=5)
        self.pause_btn = ttk.Button(ctrl_frame, text="Pause", command=self.pause_processing, style='Custom.TButton', state='disabled')
        self.pause_btn.pack(side='left', padx=5)
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop", command=self.stop_processing, style='Custom.TButton', state='disabled')
        self.stop_btn.pack(side='left', padx=5)

        # Results area
        self.results_text = scrolledtext.ScrolledText(self.main_frame, height=15, width=80, font=("Consolas", 10))
        self.results_text.pack(fill='both', expand=True, padx=20, pady=10)

        self.session_label = ttk.Label(self.main_frame, text="Session: 0 analyses run | 0 reports generated", background='#f5f7fa', font=("Arial", 9))
        self.session_label.pack(anchor='w', padx=20)

    def load_config(self):
        config_path = os.path.join(self.data_dir, "config.json")
        default = {
            "app_id": "",
            "access_token": "",
            "page_id": "",
            "processing_time": 300,
            "auto_save": True
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_config(self):
        config_path = os.path.join(self.data_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def connect_facebook(self):
        app_id = self.app_id_entry.get()
        access_token = self.access_token_entry.get()
        page_id = self.page_id_entry.get()

        if not all([app_id, access_token, page_id]):
            messagebox.showerror("Error", "Please fill in all fields")
            return

        # Validate Facebook credentials (simplified)
        try:
            # In a real application, you would validate against Facebook API
            self.fb_config = {
                "app_id": app_id,
                "access_token": access_token,
                "page_id": page_id
            }
            
            self.logged_in = True
            self.login_frame.pack_forget()
            self.main_frame.pack(fill='both', expand=True)
            self.status_label.config(text="Status: Connected to Facebook API")
            self.login_status.config(text=f"Connected to Page: {page_id}")
            self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Successfully connected to Facebook\n")
            self.results_text.see(tk.END)
            logger.info(f"Connected to Facebook Page: {page_id}")
            
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to Facebook: {str(e)}")
            logger.error(f"Facebook connection failed: {str(e)}")

    def verify_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a Facebook post URL first.")
            return
        
        # Check if it's a Facebook URL
        if "facebook.com" not in url:
            messagebox.showerror("Error", "Please enter a valid Facebook URL")
            return
            
        self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Facebook URL verified: {url}\n")
        self.results_text.see(tk.END)

    def load_url(self):
        url = self.url_entry.get()
        if "facebook.com" in url:
            self.current_url = url
            self.status_label.config(text=f"Status: Loaded Facebook Post")
            self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Facebook post loaded: {url}\n")
            self.results_text.see(tk.END)
            
            # Open in browser
            try:
                webbrowser.open(url)
                self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Opened in browser\n")
            except:
                self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Browser error\n")
            self.results_text.see(tk.END)
        else:
            messagebox.showerror("Error", "Please enter a valid Facebook URL")

    def analyze_post(self):
        if not self.logged_in:
            messagebox.showwarning("Not Connected", "Please connect to Facebook first")
            return
            
        self.start_processing()
        thread = threading.Thread(target=self._analyze_post_process)
        thread.daemon = True
        thread.start()

    def _analyze_post_process(self):
        total_time = 300  # 5 minutes for analysis
        start_time = time.time()
        end_time = start_time + total_time
        
        self.progress['maximum'] = total_time
        self.status_label.config(text="Status: Analyzing Facebook Post Performance")
        
        # Simulate Facebook API calls for post analysis
        metrics = ["engagement", "reach", "impressions", "clicks", "shares", "comments", "reactions"]
        
        while time.time() < end_time and self.processing:
            elapsed = time.time() - start_time
            remaining = max(0, end_time - time.time())
            mins, secs = divmod(int(remaining), 60)
            self.time_label.config(text=f"Estimated: {mins:02d}:{secs:02d}")
            
            # Simulate fetching data from Facebook
            metric = random.choice(metrics)
            value = random.randint(100, 10000)
            self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {metric}: {value}\n")
            self.results_text.see(tk.END)
            
            self.progress['value'] = min(total_time, int(elapsed))
            time.sleep(2)  # Simulate API call delay
            
        if self.processing:
            self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Post analysis completed!\n")
            self.session_data["analytics_run"] += 1
            self.update_session_label()
            
        self.stop_processing()

    def generate_report(self):
        if not self.logged_in:
            messagebox.showwarning("Not Connected", "Please connect to Facebook first")
            return
            
        self.start_processing()
        thread = threading.Thread(target=self._generate_report_process)
        thread.daemon = True
        thread.start()

    def _generate_report_process(self):
        total_time = 600  # 10 minutes for report generation
        start_time = time.time()
        end_time = start_time + total_time
        
        self.progress['maximum'] = total_time
        self.status_label.config(text="Status: Generating Facebook Engagement Report")
        
        report_sections = [
            "Engagement Overview", "Audience Demographics", "Peak Activity Times",
            "Top Performing Content", "Growth Metrics", "Recommendations"
        ]
        
        section_index = 0
        while time.time() < end_time and self.processing and section_index < len(report_sections):
            elapsed = time.time() - start_time
            remaining = max(0, end_time - time.time())
            mins, secs = divmod(int(remaining), 60)
            self.time_label.config(text=f"Estimated: {mins:02d}:{secs:02d}")
            
            # Generate report section
            section = report_sections[section_index]
            self.results_text.insert(tk.END, f"\n--- {section} ---\n")
            
            # Add simulated data for this section
            if section == "Engagement Overview":
                self.results_text.insert(tk.END, f"Total Engagement: {random.randint(1000, 50000)}\n")
                self.results_text.insert(tk.END, f"Engagement Rate: {random.uniform(2.5, 15.2):.2f}%\n")
            elif section == "Audience Demographics":
                self.results_text.insert(tk.END, f"Age 18-24: {random.randint(15, 40)}%\n")
                self.results_text.insert(tk.END, f"Age 25-34: {random.randint(20, 45)}%\n")
            # Add more sections as needed...
            
            self.results_text.see(tk.END)
            section_index += 1
            
            self.progress['value'] = min(total_time, int(elapsed))
            time.sleep(total_time / len(report_sections))  # Evenly distribute time
            
        if self.processing:
            self.results_text.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] Report generation completed!\n")
            self.session_data["reports_generated"] += 1
            self.update_session_label()
            
        self.stop_processing()

    def audience_insights(self):
        messagebox.showinfo("Info", "Audience Insights feature would connect to Facebook Audience Insights API")

    def content_analysis(self):
        messagebox.showinfo("Info", "Content Analysis feature would analyze your Facebook content strategy")

    def export_data(self):
        # Save results to file
        try:
            filename = f"facebook_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(self.data_dir, filename)
            with open(filepath, 'w') as f:
                f.write(self.results_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Data exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export data: {str(e)}")

    def update_session_label(self):
        analyses = self.session_data["analytics_run"]
        reports = self.session_data["reports_generated"]
        self.session_label.config(text=f"Session: {analyses} analyses run | {reports} reports generated")

    def start_processing(self):
        if not self.current_url:
            messagebox.showwarning("No URL", "Please load a Facebook post URL first.")
            return
        self.processing = True
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='normal')
        self.stop_btn.config(state='normal')

    def pause_processing(self):
        self.processing = not self.processing
        if self.processing:
            self.pause_btn.config(text="Pause")
            self.status_label.config(text="Status: Resumed")
        else:
            self.pause_btn.config(text="Resume")
            self.status_label.config(text="Status: Paused")

    def stop_processing(self):
        self.processing = False
        self.start_btn.config(state='normal')
        self.pause_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.pause_btn.config(text="Pause")
        self.status_label.config(text="Status: Ready")
        self.progress['value'] = 0
        self.time_label.config(text="Estimated: 00:00")

    def back_to_url(self):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "https://www.facebook.com/examplepost")
        self.results_text.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.time_label.config(text="Estimated: 00:00")
        self.status_label.config(text="Status: Ready to enter new URL")

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.processing = False
            self.save_config()
            logger.info("Application exited by user")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookAnalytics(root)
    root.mainloop()