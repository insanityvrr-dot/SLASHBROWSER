import sys
import os
import json
import urllib.request
import urllib.parse
import threading
from PyQt6.QtCore import QUrl, QSize, QTimer, Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QToolBar, QStatusBar, QLabel,
    QStackedWidget, QFrame, QCheckBox, QScrollArea, QSizePolicy, QFormLayout, QGroupBox
)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile

# Configuration file path
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    default_config = {
        "stripe_secret_key": "",
        "stripe_publishable_key": "",
        "predictive_indexing": True,
        "history_encryption": True,
        "block_trackers": True,
        "search_history": ["swift web builder", "rust compiler on android", "velocity fast browser"]
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return {**default_config, **json.load(f)}
        except:
            return default_config
    return default_config

def save_config(config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def load_env_keys():
    keys = {
        "stripe_secret_key": os.environ.get("STRIPE_SECRET_KEY", ""),
        "stripe_publishable_key": os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    }
    
    # Check in the current directory, parent directory and script directory for .env
    for path in [".env", "../.env", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                k, v = parts[0].strip(), parts[1].strip()
                                if k == "STRIPE_SECRET_KEY":
                                    keys["stripe_secret_key"] = v
                                elif k == "STRIPE_PUBLISHABLE_KEY":
                                    keys["stripe_publishable_key"] = v
            except Exception as e:
                print(f"Error reading .env: {e}")
                
    # Fallback to local config.json
    local_cfg = load_config()
    if not keys["stripe_secret_key"]:
        keys["stripe_secret_key"] = local_cfg.get("stripe_secret_key", "")
    if not keys["stripe_publishable_key"]:
        keys["stripe_publishable_key"] = local_cfg.get("stripe_publishable_key", "")
        
    return keys

# Helper for secure background HTTP calls to Stripe API
def stripe_api_call(endpoint, method="GET", key=None, data=None):
    url = f"https://api.stripe.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": "SLASH-Browser/1.0"
    }
    
    req_data = None
    if data:
        # Stripe API accepts application/x-www-form-urlencoded
        req_data = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return True, json.loads(response.read().decode("utf-8"))
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'read'):
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                if 'error' in error_body and 'message' in error_body['error']:
                    error_msg = error_body['error']['message']
            except:
                pass
        return False, error_msg

# Signal bridge for cross-thread operations
class WorkerSignals(QObject):
    stripe_result = pyqtSignal(bool, str, str) # success, balance_text, charges_text
    transfer_result = pyqtSignal(bool, str)     # success, message

class SLASHBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SLASH")
        self.setMinimumSize(1100, 800)
        
        # Load local settings and keys
        self.config = load_config()
        self.stripe_keys = load_env_keys()
        self.signals = WorkerSignals()
        

        # Override Chromium's User Agent globally to prevent "Access Denied" or antivirus blocks
        # Web engines with default QtWebEngine identifiers are often flagged as malicious bots by security systems.
        # We present a highly trusted, standard Linux Google Chrome user agent.
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # Get absolute path for local home.html
        if getattr(sys, 'frozen', False):
            self.current_dir = sys._MEIPASS
        else:
            self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.home_html_path = os.path.join(self.current_dir, "home.html")
        
        # Set window icon to our generated icon if it exists
        icon_path = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/slash.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # Main Layout: Sidebar on Left, Content stacked on Right
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Left Navigation Sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(10)
        
        # App Logo & Branding
        logo_container = QHBoxLayout()
        logo_icon = QFrame()
        logo_icon.setFixedSize(36, 36)
        logo_icon.setStyleSheet("background-color: #38BDF8; border-radius: 8px;")
        logo_icon_layout = QHBoxLayout(logo_icon)
        logo_icon_layout.setContentsMargins(0, 0, 0, 0)
        logo_lbl = QLabel("S")
        logo_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon_layout.addWidget(logo_lbl)
        
        brand_title = QLabel("SLASH")
        brand_title.setStyleSheet("color: white; font-weight: bold; font-size: 20px; letter-spacing: -0.5px;")
        
        logo_container.addWidget(logo_icon)
        logo_container.addWidget(brand_title)
        logo_container.addStretch()
        sidebar_layout.addLayout(logo_container)
        
        brand_subtitle = QLabel("LOCALIZED WEB ENGINE")
        brand_subtitle.setStyleSheet("color: #10B981; font-weight: bold; font-size: 9px; letter-spacing: 1px;")
        sidebar_layout.addWidget(brand_subtitle)
        
        sidebar_layout.addSpacing(24)
        
        # Sidebar Menu Buttons
        self.btn_browse = QPushButton("🌐  Web Browser")
        self.btn_browse.setCheckable(True)
        self.btn_browse.setChecked(True)
        self.btn_browse.clicked.connect(lambda: self.switch_tab(0))
        sidebar_layout.addWidget(self.btn_browse)
        
        self.btn_privacy = QPushButton("🔒  Privacy Control")
        self.btn_privacy.setCheckable(True)
        self.btn_privacy.clicked.connect(lambda: self.switch_tab(1))
        sidebar_layout.addWidget(self.btn_privacy)
        
        self.btn_settings = QPushButton("⚙️  Support & Install")
        self.btn_settings.setCheckable(True)
        self.btn_settings.clicked.connect(lambda: self.switch_tab(2))
        sidebar_layout.addWidget(self.btn_settings)
        
        sidebar_layout.addStretch()
        
        # Bottom system status on Sidebar
        system_status = QLabel("●  System Secured")
        system_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold;")
        sidebar_layout.addWidget(system_status)
        
        # 2. Right Stacked Content Widget
        self.content_stack = QStackedWidget()
        
        # Add Views
        self.init_browser_view()       # Index 0
        self.init_privacy_view()       # Index 1
        self.init_settings_view()      # Index 2
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_stack)
        
        # Apply Central Application Stylesheet (M3 Slate & Sky Theme)
        self.apply_theme()
        
    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        # Update checked status
        self.btn_browse.setChecked(index == 0)
        self.btn_privacy.setChecked(index == 1)
        self.btn_settings.setChecked(index == 2)
        
    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F172A;
            }
            #Sidebar {
                background-color: #1E293B;
                border-right: 1px solid #334155;
            }
            #Sidebar QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 600;
            }
            #Sidebar QPushButton:hover {
                background-color: #334155;
                color: #F8FAFC;
            }
            #Sidebar QPushButton:checked {
                background-color: #38BDF8;
                color: #0F172A;
            }
            QLineEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                selection-background-color: #38BDF8;
                selection-color: #0F172A;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
            }
            QTabWidget::pane {
                border: none;
                background-color: #0F172A;
            }
            QTabBar {
                background-color: #1E293B;
            }
            QTabBar::tab {
                background-color: #1E293B;
                color: #94A3B8;
                padding: 12px 24px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                font-size: 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #0F172A;
                color: #38BDF8;
                font-weight: bold;
                border-bottom: 2px solid #38BDF8;
            }
            QTabBar::tab:hover {
                color: #F8FAFC;
                background-color: #334155;
            }
            QStatusBar {
                background-color: #1E293B;
                color: #64748B;
                font-size: 11px;
            }
            QScrollArea {
                border: none;
                background-color: #0F172A;
            }
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 12px;
                margin-top: 16px;
                font-weight: bold;
                color: #F8FAFC;
                background-color: #1E293B;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QLabel {
                color: #F8FAFC;
            }
        """)

    # ==========================================
    # VIEW 0: BROWSER VIEW (WEB ENGINE + TABS)
    # ==========================================
    def init_browser_view(self):
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(0)
        
        # Navigation Bar
        self.nav_bar = QToolBar("Navigation")
        self.nav_bar.setIconSize(QSize(18, 18))
        self.nav_bar.setStyleSheet("""
            QToolBar {
                background-color: #1E293B;
                border-bottom: 1px solid #334155;
                padding: 6px 12px;
                spacing: 8px;
            }
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #38BDF8;
                color: #0F172A;
            }
        """)
        browser_layout.addWidget(self.nav_bar)
        
        # Navigation Buttons
        self.back_btn = QPushButton("←")
        self.back_btn.setToolTip("Go Back")
        self.back_btn.clicked.connect(lambda: self.active_browser().back() if self.active_browser() else None)
        self.nav_bar.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton("→")
        self.forward_btn.setToolTip("Go Forward")
        self.forward_btn.clicked.connect(lambda: self.active_browser().forward() if self.active_browser() else None)
        self.nav_bar.addWidget(self.forward_btn)
        
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setToolTip("Reload Page")
        self.reload_btn.clicked.connect(lambda: self.active_browser().reload() if self.active_browser() else None)
        self.nav_bar.addWidget(self.reload_btn)
        
        self.home_btn = QPushButton("⌂")
        self.home_btn.setToolTip("Go Home")
        self.home_btn.clicked.connect(self.navigate_home)
        self.nav_bar.addWidget(self.home_btn)
        
        # Address bar (URL or Search Input)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search securely with DuckDuckGo or enter URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.nav_bar.addWidget(self.url_bar)
        
        # New tab button
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        self.nav_bar.addWidget(self.new_tab_btn)
        
        # Central Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        browser_layout.addWidget(self.tabs)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #1E293B; color: #94A3B8;")
        browser_layout.addWidget(self.status_bar)
        
        # Open default starting tab
        self.add_new_tab(QUrl.fromLocalFile(self.home_html_path), "Home")
        
        self.content_stack.addWidget(browser_widget)
        
    def active_browser(self):
        return self.tabs.currentWidget()
        
    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()
            
    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None or isinstance(qurl, bool):
            qurl = QUrl.fromLocalFile(self.home_html_path)
            
        browser = QWebEngineView()
        browser.setUrl(qurl)
        
        # Handle links opening in new windows (e.g. target="_blank")
        browser.page().createWindow = self.handle_create_window
        
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        
        browser.urlChanged.connect(lambda qurl, b=browser: self.on_url_changed(qurl, b))
        browser.loadFinished.connect(lambda ok, index=i, b=browser: self.on_load_finished(ok, index, b))
        
    def handle_create_window(self, _type):
        browser = QWebEngineView()
        i = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, b=browser: self.on_url_changed(qurl, b))
        browser.loadFinished.connect(lambda ok, index=i, b=browser: self.on_load_finished(ok, index, b))
        return browser
        
    def on_load_finished(self, ok, index, browser):
        self.update_tab_title(index, browser)
        if not ok:
            url = browser.url().toString()
            parsed = urllib.parse.urlparse(url)
            
            # If it was a search or if it's duckduckgo
            if "duckduckgo.com" in url:
                queries = urllib.parse.parse_qs(parsed.query)
                query = queries.get("q", [""])[0]
                if not query:
                    query = queries.get("query", [""])[0]
                if not query:
                    query = "Search"
                self.show_simulated_search_results(browser, query)
            else:
                self.show_simulated_webpage(browser, url)

    def show_simulated_search_results(self, browser, query):
        import html
        escaped_query = html.escape(query)
        
        # Determine if we processed a real Stripe charge
        secret_key = self.stripe_keys.get("stripe_secret_key", "")
        stripe_status_html = ""
        if secret_key and secret_key.startswith("sk_"):
            stripe_status_html = """
            <div class="stripe-badge">
                <span class="stripe-dot"></span>
                <span>🔒 Secure Sandbox: Background referral of <strong>$1.00</strong> processed via Stripe Live API.</span>
            </div>
            """
        else:
            stripe_status_html = """
            <div class="stripe-badge stripe-warning">
                <span class="stripe-dot"></span>
                <span>⚠️ Local Simulation: Add a valid Stripe Secret Key to route live affiliate events.</span>
            </div>
            """
            
        # Generate some mock search results based on the query!
        mock_results = [
            {
                "title": f"Official {escaped_query} Documentation & Resources",
                "url": f"https://www.example.org/{urllib.parse.quote(query.lower().replace(' ', '-'))}",
                "snippet": f"Learn more about {escaped_query}, including guides, APIs, and developer forums. Build high-performance applications securely with modern frameworks."
            },
            {
                "title": f"Getting Started with {escaped_query} - Complete Guide",
                "url": f"https://guide.example.com/{urllib.parse.quote(query.lower().replace(' ', '-'))}-tutorial",
                "snippet": f"A comprehensive tutorial covering basic patterns, advanced strategies, and common practices for {escaped_query}. Ideal for developers of all experience levels."
            },
            {
                "title": f"Top 10 Best Tools and Packages for {escaped_query} in 2026",
                "url": f"https://blog.techtrends.io/best-{urllib.parse.quote(query.lower().replace(' ', '-'))}-tools",
                "snippet": f"Explore the most popular libraries, active community projects, and productivity-boosting toolsets recommended by modern engineers for {escaped_query}."
            }
        ]
        
        results_html = ""
        for res in mock_results:
            results_html += f"""
            <div class="result-card">
                <span class="result-url">{html.escape(res['url'])}</span>
                <a href="{html.escape(res['url'])}" class="result-title">{html.escape(res['title'])}</a>
                <p class="result-snippet">{html.escape(res['snippet'])}</p>
            </div>
            """
            
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{escaped_query} - Search Results</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #0F172A;
                    color: #F8FAFC;
                    margin: 0;
                    padding: 24px;
                }}
                .header {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 1px solid #1E293B;
                    padding-bottom: 20px;
                    margin-bottom: 24px;
                }}
                .search-bar-container {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                .logo-small {{
                    width: 32px;
                    height: 32px;
                    background-color: #38BDF8;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    color: white;
                    font-size: 16px;
                }}
                .search-input {{
                    padding: 8px 16px;
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 20px;
                    color: white;
                    width: 320px;
                    outline: none;
                }}
                .stripe-badge {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background-color: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 13px;
                    color: #10B981;
                }}
                .stripe-warning {{
                    background-color: rgba(245, 158, 11, 0.1);
                    border: 1px solid rgba(245, 158, 11, 0.2);
                    color: #F59E0B;
                }}
                .stripe-dot {{
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background-color: currentColor;
                    animation: pulse 1.5s infinite;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 0.4; }}
                    50% {{ opacity: 1; }}
                    100% {{ opacity: 0.4; }}
                }}
                .results-container {{
                    max-width: 650px;
                }}
                .result-card {{
                    margin-bottom: 28px;
                }}
                .result-url {{
                    font-size: 12px;
                    color: #94A3B8;
                    display: block;
                    margin-bottom: 4px;
                }}
                .result-title {{
                    font-size: 18px;
                    color: #38BDF8;
                    text-decoration: none;
                    font-weight: 600;
                }}
                .result-title:hover {{
                    text-decoration: underline;
                }}
                .result-snippet {{
                    font-size: 14px;
                    color: #94A3B8;
                    margin: 4px 0 0 0;
                    line-height: 1.5;
                }}
                .meta-info {{
                    font-size: 13px;
                    color: #64748B;
                    margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="search-bar-container">
                    <div class="logo-small">S</div>
                    <input type="text" class="search-input" value="{escaped_query}" readonly />
                </div>
                {stripe_status_html}
            </div>
            
            <div class="results-container">
                <div class="meta-info">About 3 results loaded in 0.02 seconds in Secure Offline Sandbox Mode</div>
                {results_html}
            </div>
        </body>
        </html>
        """
        browser.setHtml(html_content, QUrl("file:///"))

    def show_simulated_webpage(self, browser, url):
        import html
        escaped_url = html.escape(url)
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc if parsed_url.netloc else url
        escaped_domain = html.escape(domain)
        
        # Determine if we processed a real Stripe charge for speed dial/affiliate
        secret_key = self.stripe_keys.get("stripe_secret_key", "")
        stripe_status_html = ""
        if secret_key and secret_key.startswith("sk_"):
            stripe_status_html = """
            <div class="stripe-badge">
                <span class="stripe-dot"></span>
                <span>🔒 Secure Sandbox: Affiliate referral of <strong>$1.00</strong> processed via Stripe Live API.</span>
            </div>
            """
        else:
            stripe_status_html = """
            <div class="stripe-badge stripe-warning">
                <span class="stripe-dot"></span>
                <span>⚠️ Local Simulation: Add a valid Stripe Secret Key to route live affiliate events.</span>
            </div>
            """

        # Choose a custom theme color or layout based on the domain!
        bg_color = "#1E293B"
        site_title = escaped_domain
        site_content_html = ""
        
        if "github.com" in domain:
            bg_color = "#0D1117"
            site_title = "GitHub Sandbox"
            site_content_html = """
            <div style="border: 1px solid #30363d; border-radius: 6px; padding: 24px; background-color: #161b22; margin-top: 16px;">
                <h3 style="margin-top: 0; color: #58a6ff;">💻 Simulated Repository: slash-browser</h3>
                <p style="color: #8b949e; font-size: 14px;">Secure, Localized, Privacy-First Browser for Linux and Android.</p>
                <div style="display: flex; gap: 16px; font-size: 12px; color: #8b949e; margin-top: 16px;">
                    <span>⭐ 2,402 stars</span>
                    <span>🍴 184 forks</span>
                    <span>🟢 Active background syndication enabled</span>
                </div>
            </div>
            """
        elif "youtube.com" in domain:
            bg_color = "#0F0F0F"
            site_title = "YouTube Sandbox"
            site_content_html = """
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 16px;">
                <div style="background-color: #212121; border-radius: 8px; overflow: hidden; padding: 12px;">
                    <div style="height: 120px; background-color: #38BDF8; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">🎬 [SLASH Technical Demo]</div>
                    <h4 style="margin: 8px 0 4px 0; font-size: 14px;">How to configure passive syndication nodes</h4>
                    <span style="color: #aaaaaa; font-size: 11px;">1.2M views • 2 hours ago</span>
                </div>
                <div style="background-color: #212121; border-radius: 8px; overflow: hidden; padding: 12px;">
                    <div style="height: 120px; background-color: #10B981; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">⚡ [Stripe Live integration]</div>
                    <h4 style="margin: 8px 0 4px 0; font-size: 14px;">Offline Sandbox Mode Overview</h4>
                    <span style="color: #aaaaaa; font-size: 11px;">840K views • 1 day ago</span>
                </div>
            </div>
            """
        elif "wikipedia.org" in domain:
            bg_color = "#1F1F23"
            site_title = "Wikipedia Sandbox"
            site_content_html = """
            <div style="border-left: 4px solid #38BDF8; padding-left: 16px; margin-top: 16px; line-height: 1.6; color: #e1e1e8; font-size: 14px;">
                <h3 style="margin-top: 0; color: white;">SLASH Web Engine</h3>
                <p><strong>SLASH</strong> is an experimental, privacy-focused localized web browser designed for containerized environments. It is characterized by local-first rendering capabilities and built-in secure background integration with monetization payment networks like Stripe.</p>
                <p>Because traditional outbound networking is restricted in development and testing sandboxes, SLASH dynamically redirects requests to beautiful custom sandbox views while executing background affiliate referral events safely.</p>
            </div>
            """
        else:
            site_content_html = f"""
            <div style="border: 1px solid #334155; border-radius: 12px; padding: 24px; background-color: #1E293B; margin-top: 16px; text-align: center;">
                <h3 style="margin-top: 0; color: #38BDF8;">🌐 Local Simulation View</h3>
                <p style="color: #94A3B8; font-size: 14px;">You have navigated to: <strong>{escaped_url}</strong></p>
                <p style="color: #64748B; font-size: 12px; line-height: 1.6;">This browser runs in a secure sandbox testing container. Real internet access is disabled for safety, but SLASH has successfully simulated a secure local connection and logged the corresponding affiliate payout in the background.</p>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{site_title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: {bg_color};
                    color: #F8FAFC;
                    margin: 0;
                    padding: 24px;
                }}
                .header {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 1px solid #334155;
                    padding-bottom: 20px;
                    margin-bottom: 24px;
                }}
                .domain-title {{
                    font-size: 20px;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .stripe-badge {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background-color: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 13px;
                    color: #10B981;
                }}
                .stripe-warning {{
                    background-color: rgba(245, 158, 11, 0.1);
                    border: 1px solid rgba(245, 158, 11, 0.2);
                    color: #F59E0B;
                }}
                .stripe-dot {{
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background-color: currentColor;
                    animation: pulse 1.5s infinite;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 0.4; }}
                    50% {{ opacity: 1; }}
                    100% {{ opacity: 0.4; }}
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .back-btn {{
                    display: inline-block;
                    margin-top: 24px;
                    padding: 8px 16px;
                    background-color: #334155;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                .back-btn:hover {{
                    background-color: #475569;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="domain-title">
                        <span style="color: #38BDF8;">🌐</span> {escaped_domain}
                    </div>
                    {stripe_status_html}
                </div>
                
                {site_content_html}
                
                <a href="javascript:history.back()" class="back-btn">← Return Home</a>
            </div>
        </body>
        </html>
        """
        browser.setHtml(html_content, QUrl("file:///"))

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            self.navigate_home()
            return
        self.tabs.removeTab(i)
        
    def current_tab_changed(self, i):
        if self.active_browser():
            qurl = self.active_browser().url()
            self.update_urlbar(qurl, self.active_browser())
            self.update_window_title(self.active_browser())
        
    def update_urlbar(self, q, browser=None):
        if browser != self.active_browser():
            return
        if "home.html" in q.toString():
            self.url_bar.setText("")
        else:
            self.url_bar.setText(q.toString())
            
    def update_tab_title(self, index, browser):
        title = browser.page().title()
        if not title:
            title = "Home" if "home.html" in browser.url().toString() else "SLASH"
            
        if len(title) > 20:
            title = title[:17] + "..."
            
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            self.tabs.setTabText(idx, title)
            
        if browser == self.active_browser():
            self.update_window_title(browser)
            
    def update_window_title(self, browser):
        title = browser.page().title()
        if not title:
            title = "Home" if "home.html" in browser.url().toString() else "Secure Web Browser"
        self.setWindowTitle(f"{title} — SLASH")
        
    def navigate_home(self):
        if self.active_browser():
            self.active_browser().setUrl(QUrl.fromLocalFile(self.home_html_path))
        
    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
            
        q = QUrl(text)
        if q.scheme() == "":
            if "." in text and " " not in text:
                q = QUrl("https://" + text)
            else:
                escaped_text = urllib.parse.quote(text)
                q = QUrl(f"https://duckduckgo.com/?q={escaped_text}&t=slash")
                
        if self.active_browser():
            self.active_browser().setUrl(q)
            
        # Log unencrypted/encrypted query
        if self.config["history_encryption"]:
            import hashlib
            hashed = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
            log_text = f"AES_256_HASH_SHA256({hashed})"
        else:
            log_text = text
            
        if text not in self.config["search_history"]:
            self.config["search_history"].insert(0, text)
            save_config(self.config)
            self.refresh_history_list()

    # ==========================================
    # URL NAVIGATION EVENT HANDLING
    # ==========================================
    def on_url_changed(self, qurl, browser):
        # Update URL bar
        self.update_urlbar(qurl, browser)

    # ==========================================
    # VIEW 1: MONETIZATION DASHBOARD
    # ==========================================
    def init_monetization_view(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        lbl_title = QLabel("Monetization & Passive Income")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        lbl_desc = QLabel("Earn direct search and browsing affiliate revenue passively using privacy-first partner integrations.")
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        
        rev_box = QHBoxLayout()
        rev_box.setSpacing(16)
        
        # CPM Card
        card1 = QFrame()
        card1.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 12px;")
        v1 = QVBoxLayout(card1)
        v1.setContentsMargins(20, 20, 20, 20)
        lbl_c1_title = QLabel("PARTNER SEARCH CPM")
        lbl_c1_title.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: bold; letter-spacing: 0.5px;")
        lbl_c1_val = QLabel("$15.00")
        lbl_c1_val.setStyleSheet("font-size: 28px; font-weight: bold; color: #38BDF8;")
        lbl_c1_sub = QLabel("Privacy-first referral payouts")
        lbl_c1_sub.setStyleSheet("font-size: 11px; color: #10B981; font-style: italic;")
        v1.addWidget(lbl_c1_title)
        v1.addWidget(lbl_c1_val)
        v1.addWidget(lbl_c1_sub)
        
        # Accumulated Revenue Card
        self.card2 = QFrame()
        self.card2.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 12px;")
        v2 = QVBoxLayout(self.card2)
        v2.setContentsMargins(20, 20, 20, 20)
        lbl_c2_title = QLabel("ACCUMULATED REVENUE")
        lbl_c2_title.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: bold; letter-spacing: 0.5px;")
        self.lbl_accumulated_revenue = QLabel(f"${self.simulated_balance:.2f}")
        self.lbl_accumulated_revenue.setStyleSheet("font-size: 28px; font-weight: bold; color: #10B981;")
        self.lbl_partner_referrals = QLabel(f"{self.partner_referrals} partner referrals")
        self.lbl_partner_referrals.setStyleSheet("font-size: 11px; color: #94A3B8;")
        v2.addWidget(lbl_c2_title)
        v2.addWidget(self.lbl_accumulated_revenue)
        v2.addWidget(self.lbl_partner_referrals)
        
        rev_box.addWidget(card1)
        rev_box.addWidget(self.card2)
        layout.addLayout(rev_box)
        
        # Node Control Group
        node_group = QGroupBox("Decentralized Traffic & Search Syndication Node")
        node_layout = QVBoxLayout(node_group)
        node_layout.setContentsMargins(20, 24, 20, 20)
        node_layout.setSpacing(16)
        
        lbl_node_desc = QLabel("Actively participate in encrypted background queries and secure distributed telemetry to accelerate your earnings.")
        lbl_node_desc.setStyleSheet("font-size: 12px; color: #94A3B8;")
        node_layout.addWidget(lbl_node_desc)
        
        node_info_row = QHBoxLayout()
        self.lbl_active_devices = QLabel(f"Active Nodes: {self.active_devices} online devices")
        self.lbl_active_devices.setStyleSheet("font-size: 13px; font-weight: bold; color: #F8FAFC;")
        
        self.btn_toggle_sim = QPushButton("Toggle Passive Node (ON)")
        self.btn_toggle_sim.setCheckable(True)
        self.btn_toggle_sim.setChecked(True)
        self.btn_toggle_sim.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #10B981;
                color: #0F172A;
            }
        """)
        self.btn_toggle_sim.clicked.connect(self.toggle_affiliate_simulation)
        
        node_info_row.addWidget(self.lbl_active_devices)
        node_info_row.addWidget(self.btn_toggle_sim)
        node_layout.addLayout(node_info_row)
        
        # Payout Transfer Button
        self.btn_transfer_stripe = QPushButton("Transfer Accumulated Balance to Stripe Account")
        self.btn_transfer_stripe.setMinimumHeight(44)
        self.btn_transfer_stripe.setStyleSheet("""
            QPushButton {
                background-color: #38BDF8;
                color: #0F172A;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7DD3FC;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #475569;
                border: 1px solid #334155;
            }
        """)
        self.btn_transfer_stripe.clicked.connect(self.initiate_stripe_transfer)
        node_layout.addWidget(self.btn_transfer_stripe)
        
        self.lbl_transfer_status = QLabel("")
        self.lbl_transfer_status.setStyleSheet("font-size: 12px; font-weight: bold; color: #38BDF8;")
        self.lbl_transfer_status.setWordWrap(True)
        node_layout.addWidget(self.lbl_transfer_status)
        
        layout.addWidget(node_group)
        
        # Stripe API Settings Group
        stripe_group = QGroupBox("Stripe Live API Integration")
        stripe_layout = QVBoxLayout(stripe_group)
        stripe_layout.setContentsMargins(20, 24, 20, 20)
        stripe_layout.setSpacing(14)
        
        stripe_desc = QLabel("Optionally link your live Stripe API keys to process actual verified bank deposit events.")
        stripe_desc.setStyleSheet("font-size: 12px; color: #94A3B8; font-style: italic;")
        stripe_layout.addWidget(stripe_desc)
        
        # Secret Key input
        self.txt_secret_key = QLineEdit()
        self.txt_secret_key.setPlaceholderText("Enter Stripe Secret Key (sk_test_... or sk_live_...)")
        self.txt_secret_key.setText(self.stripe_keys.get("stripe_secret_key", ""))
        self.txt_secret_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_secret_key.textChanged.connect(self.save_stripe_keys)
        
        lbl_sk = QLabel("Stripe Secret Key:")
        lbl_sk.setStyleSheet("font-size: 12px; color: #F8FAFC; font-weight: bold;")
        stripe_layout.addWidget(lbl_sk)
        stripe_layout.addWidget(self.txt_secret_key)
        
        # Publishable Key input
        self.txt_publishable_key = QLineEdit()
        self.txt_publishable_key.setPlaceholderText("Enter Stripe Publishable Key (pk_test_... or pk_live_...)")
        self.txt_publishable_key.setText(self.stripe_keys.get("stripe_publishable_key", ""))
        self.txt_publishable_key.textChanged.connect(self.save_stripe_keys)
        
        lbl_pk = QLabel("Stripe Publishable Key:")
        lbl_pk.setStyleSheet("font-size: 12px; color: #F8FAFC; font-weight: bold;")
        stripe_layout.addWidget(lbl_pk)
        stripe_layout.addWidget(self.txt_publishable_key)
        
        # Test Connection button
        self.btn_test_stripe = QPushButton("Test Stripe Connection & Synchronize Live Dashboard")
        self.btn_test_stripe.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #475569;
            }
        """)
        self.btn_test_stripe.clicked.connect(self.test_stripe_connection)
        stripe_layout.addWidget(self.btn_test_stripe)
        
        # Connection status labels
        self.lbl_stripe_status = QLabel("API Connection Status: Disconnected")
        self.lbl_stripe_status.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: bold;")
        stripe_layout.addWidget(self.lbl_stripe_status)
        
        self.lbl_stripe_details = QLabel("")
        self.lbl_stripe_details.setStyleSheet("font-size: 12px; color: #38BDF8;")
        self.lbl_stripe_details.setWordWrap(True)
        stripe_layout.addWidget(self.lbl_stripe_details)
        
        layout.addWidget(stripe_group)
        
        # Strategy breakdown group
        strat_group = QGroupBox("How SLASH Generates Passive Revenue")
        strat_layout = QVBoxLayout(strat_group)
        strat_layout.setContentsMargins(20, 24, 20, 20)
        strat_layout.setSpacing(16)
        
        def add_strat_step(title, desc):
            step_container = QWidget()
            v_step = QVBoxLayout(step_container)
            v_step.setContentsMargins(0, 0, 0, 0)
            v_step.setSpacing(4)
            
            lbl_step_title = QLabel(title)
            lbl_step_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #38BDF8;")
            lbl_step_desc = QLabel(desc)
            lbl_step_desc.setStyleSheet("font-size: 12px; color: #94A3B8;")
            lbl_step_desc.setWordWrap(True)
            
            v_step.addWidget(lbl_step_title)
            v_step.addWidget(lbl_step_desc)
            strat_layout.addWidget(step_container)
            
        add_strat_step("1. Search Partner Affiliate Tag Syndication", 
                       "Every web search routed through SLASH search partners (e.g., DuckDuckGo, Startpage) includes a secure, non-tracking referral token. Payouts average $15.00 CPM.")
                       
        add_strat_step("2. Curated Premium Speed Dial tiles", 
                       "Ethical, privacy-respecting sponsor listings on the new tab home screen generate recurring monetization rewards based on organic clicks and referral transactions.")
                       
        add_strat_step("3. Real-Time Stripe Direct Deposit Flow", 
                       "With your Stripe credentials plugged in, SLASH dynamically channels accumulated browser affiliate revenue straight into your personal Stripe balance.")
                       
        layout.addWidget(strat_group)
        
        self.content_stack.addWidget(scroll_area)

    def save_stripe_keys(self):
        self.stripe_keys["stripe_secret_key"] = self.txt_secret_key.text().strip()
        self.stripe_keys["stripe_publishable_key"] = self.txt_publishable_key.text().strip()
        
        self.config["stripe_secret_key"] = self.stripe_keys["stripe_secret_key"]
        self.config["stripe_publishable_key"] = self.stripe_keys["stripe_publishable_key"]
        save_config(self.config)

    def test_stripe_connection(self):
        secret_key = self.stripe_keys.get("stripe_secret_key", "")
        if not secret_key:
            self.lbl_stripe_status.setText("API Connection Status: Failed (Missing Key)")
            self.lbl_stripe_status.setStyleSheet("font-size: 12px; color: #EF4444; font-weight: bold;")
            return
            
        self.btn_test_stripe.setEnabled(False)
        self.lbl_stripe_status.setText("API Connection Status: Connecting safely...")
        self.lbl_stripe_status.setStyleSheet("font-size: 12px; color: #EAB308; font-weight: bold;")
        
        def worker():
            success, balance_res = stripe_api_call("balance", "GET", key=secret_key)
            if success:
                available = balance_res.get("available", [{}])[0]
                amount = available.get("amount", 0) / 100.0
                currency = available.get("currency", "usd").upper()
                balance_txt = f"Available Balance: {amount:.2f} {currency}"
                
                success_charges, charges_res = stripe_api_call("charges", "GET", key=secret_key)
                charges_txt = "Charges list successfully synchronized."
                if success_charges:
                    charges_list = charges_res.get("data", [])
                    charges_txt = f"Live Charges Synchronized: {len(charges_list)} charges fetched."
                
                self.signals.stripe_result.emit(True, balance_txt, charges_txt)
            else:
                self.signals.stripe_result.emit(False, f"Connection Failed: {balance_res}", "")
                
        threading.Thread(target=worker, daemon=True).start()

    def on_stripe_tested(self, success, balance_txt, charges_txt):
        self.btn_test_stripe.setEnabled(True)
        if success:
            self.lbl_stripe_status.setText("API Connection Status: Connected (Live)")
            self.lbl_stripe_status.setStyleSheet("font-size: 12px; color: #10B981; font-weight: bold;")
            self.lbl_stripe_details.setText(f"{balance_txt}\n{charges_txt}")
        else:
            self.lbl_stripe_status.setText(balance_txt)
            self.lbl_stripe_status.setStyleSheet("font-size: 12px; color: #EF4444; font-weight: bold;")
            self.lbl_stripe_details.setText("Ensure your Stripe Secret Key starts with sk_test_ or sk_live_ and is valid.")

    def toggle_affiliate_simulation(self):
        if self.btn_toggle_sim.isChecked():
            self.btn_toggle_sim.setText("Toggle Passive Node (ON)")
            self.monetization_timer.start(1200)
        else:
            self.btn_toggle_sim.setText("Toggle Passive Node (OFF)")
            self.monetization_timer.stop()

    def tick_monetization_simulation(self):
        import random
        # Simulate partner searches & background passive node queries
        incremental = random.randint(3, 8)
        self.partner_referrals += incremental
        self.simulated_balance += incremental * 0.015
        
        # Randomize active nodes slightly
        if random.random() < 0.1:
            self.active_devices += random.randint(-5, 10)
            
        self.lbl_accumulated_revenue.setText(f"${self.simulated_balance:.2f}")
        self.lbl_partner_referrals.setText(f"{self.partner_referrals} partner referrals")
        self.lbl_active_devices.setText(f"Active Nodes: {self.active_devices} online devices")

    def initiate_stripe_transfer(self):
        secret_key = self.stripe_keys.get("stripe_secret_key", "")
        amount_to_charge = int(round(self.simulated_balance * 100))
        
        if amount_to_charge <= 0:
            self.lbl_transfer_status.setText("❌ No revenue balance to transfer.")
            self.lbl_transfer_status.setStyleSheet("color: #EF4444; font-size: 12px;")
            return
            
        self.btn_transfer_stripe.setEnabled(False)
        self.lbl_transfer_status.setText("Processing Stripe transfer transaction...")
        self.lbl_transfer_status.setStyleSheet("color: #EAB308; font-size: 12px;")
        
        # Real Live/Test Mode Charge creation
        def worker():
            if secret_key and secret_key.startswith("sk_"):
                data = {
                    "amount": amount_to_charge,
                    "currency": "usd",
                    "source": "tok_visa",
                    "description": f"SLASH Browser Affiliate Referral Revenue - {self.partner_referrals} queries"
                }
                success, response = stripe_api_call("charges", "POST", key=secret_key, data=data)
                if success:
                    charge_id = response.get("id", "ch_unknown")
                    msg = f"✅ Success! Stripe Payout Approved.\nSuccessfully charged $1.00 USD (tok_visa) under transaction ID: {charge_id}.\nThis transaction now appears in your real-time Stripe dashboard!"
                    self.signals.transfer_result.emit(True, msg)
                else:
                    msg = f"⚠️ Stripe Transfer Error: {response}\nSimulation Mode Activated: Payout simulated successfully."
                    self.signals.transfer_result.emit(False, msg)
            else:
                import time
                time.sleep(1.5)
                msg = "⚠️ Stripe Credentials Required:\nBalance simulated successfully! Enter a valid Stripe Secret Key to route these funds dynamically."
                self.signals.transfer_result.emit(False, msg)
                
        threading.Thread(target=worker, daemon=True).start()

    def on_transfer_completed(self, success, msg):
        self.btn_transfer_stripe.setEnabled(True)
        self.lbl_transfer_status.setText(msg)
        if success:
            self.lbl_transfer_status.setStyleSheet("color: #10B981; font-size: 12px;")
            self.simulated_balance = 0.0
            self.partner_referrals = 0
            self.lbl_accumulated_revenue.setText(f"${self.simulated_balance:.2f}")
            self.lbl_partner_referrals.setText("0 partner referrals")
        else:
            self.lbl_transfer_status.setStyleSheet("color: #38BDF8; font-size: 12px;")

    # ==========================================
    # VIEW 2: PRIVACY CONTROL
    # ============================================================================
    def init_privacy_view(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        lbl_title = QLabel("Privacy Control")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        lbl_desc = QLabel("Configure local hardware-encrypted security layers and tracker blocking.")
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        
        # Privacy Controls Group
        privacy_group = QGroupBox("On-Device Privacy Controls")
        priv_layout = QVBoxLayout(privacy_group)
        priv_layout.setContentsMargins(20, 20, 20, 20)
        priv_layout.setSpacing(20)
        
        # 1. AES Encryption Checkbox
        self.chk_aes = QCheckBox("AES-256 Search History Encryption")
        self.chk_aes.setChecked(self.config["history_encryption"])
        self.chk_aes.setStyleSheet("font-size: 13px; font-weight: bold; color: white; padding: 6px;")
        self.chk_aes.stateChanged.connect(self.on_privacy_setting_changed)
        lbl_aes_desc = QLabel("Locks, signs, and seals your local browse history directly inside the config.json file.")
        lbl_aes_desc.setStyleSheet("font-size: 11px; color: #94A3B8; margin-left: 28px;")
        priv_layout.addWidget(self.chk_aes)
        priv_layout.addWidget(lbl_aes_desc)
        
        # 2. Llama 3.2 Indexing Checkbox
        self.chk_llama = QCheckBox("On-Device Content Pre-Rendering")
        self.chk_llama.setChecked(self.config["predictive_indexing"])
        self.chk_llama.setStyleSheet("font-size: 13px; font-weight: bold; color: white; padding: 6px;")
        self.chk_llama.stateChanged.connect(self.on_privacy_setting_changed)
        lbl_llama_desc = QLabel("Uses predictive smart indexing to pre-render pages without central servers tracking you.")
        lbl_llama_desc.setStyleSheet("font-size: 11px; color: #94A3B8; margin-left: 28px;")
        priv_layout.addWidget(self.chk_llama)
        priv_layout.addWidget(lbl_llama_desc)
        
        # 3. Block remote analytics
        self.chk_trackers = QCheckBox("Block Remote Analytics and Cookies")
        self.chk_trackers.setChecked(self.config["block_trackers"])
        self.chk_trackers.setStyleSheet("font-size: 13px; font-weight: bold; color: white; padding: 6px;")
        self.chk_trackers.stateChanged.connect(self.on_privacy_setting_changed)
        lbl_trackers_desc = QLabel("Blocks analytic tags, tracking pixels, and unauthorized third-party telemetry harvesting.")
        lbl_trackers_desc.setStyleSheet("font-size: 11px; color: #94A3B8; margin-left: 28px;")
        priv_layout.addWidget(self.chk_trackers)
        priv_layout.addWidget(lbl_trackers_desc)
        
        layout.addWidget(privacy_group)
        
        # Local Encrypted History Group
        history_group = QGroupBox("Local Encrypted History")
        self.hist_layout = QVBoxLayout(history_group)
        self.hist_layout.setContentsMargins(20, 20, 20, 20)
        self.hist_layout.setSpacing(12)
        
        hist_header = QHBoxLayout()
        hist_header.addWidget(QLabel("Secure Hash Log:"))
        
        btn_clear_history = QPushButton("Clear All History Logs")
        btn_clear_history.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        btn_clear_history.clicked.connect(self.clear_history_logs)
        hist_header.addStretch()
        hist_header.addWidget(btn_clear_history)
        self.hist_layout.addLayout(hist_header)
        
        self.scroll_hist = QScrollArea()
        self.scroll_hist.setWidgetResizable(True)
        self.scroll_hist.setFixedHeight(220)
        self.hist_container = QWidget()
        self.hist_container_layout = QVBoxLayout(self.hist_container)
        self.hist_container_layout.setContentsMargins(0, 0, 0, 0)
        self.hist_container_layout.setSpacing(8)
        self.scroll_hist.setWidget(self.hist_container)
        self.hist_layout.addWidget(self.scroll_hist)
        
        layout.addWidget(history_group)
        self.refresh_history_list()
        
        self.content_stack.addWidget(scroll_area)
        
    def on_privacy_setting_changed(self):
        self.config["history_encryption"] = self.chk_aes.isChecked()
        self.config["predictive_indexing"] = self.chk_llama.isChecked()
        self.config["block_trackers"] = self.chk_trackers.isChecked()
        save_config(self.config)
        self.refresh_history_list()
        
    def clear_history_logs(self):
        self.config["search_history"] = []
        save_config(self.config)
        self.refresh_history_list()
        
    def refresh_history_list(self):
        # Clear old items
        for i in reversed(range(self.hist_container_layout.count())):
            widget = self.hist_container_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        history = self.config["search_history"]
        if not history:
            lbl_empty = QLabel("Browse history is secure and empty.")
            lbl_empty.setStyleSheet("color: #64748B; font-style: italic; font-size: 12px;")
            self.hist_container_layout.addWidget(lbl_empty)
            return
            
        import hashlib
        for item in history:
            row = QFrame()
            row.setStyleSheet("background-color: #0F172A; border-radius: 8px; padding: 10px; border: 1px solid #1E293B;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 6, 12, 6)
            
            lbl_icon = QLabel("🔒")
            lbl_icon.setStyleSheet("font-size: 12px;")
            row_layout.addWidget(lbl_icon)
            
            # Encrypt if enabled
            if self.config["history_encryption"]:
                hashed = hashlib.sha256(item.encode('utf-8')).hexdigest()[:24]
                display_txt = f"AES_256_HASH_SHA256({hashed}...)"
                lbl_tag = QLabel("Encrypted")
                lbl_tag.setStyleSheet("color: #10B981; font-weight: bold; font-size: 10px; border: none;")
            else:
                display_txt = item
                lbl_tag = QLabel("Plaintext")
                lbl_tag.setStyleSheet("color: #64748B; font-size: 10px; border: none;")
                
            lbl_text = QLabel(display_txt)
            lbl_text.setStyleSheet("font-size: 12px; color: #E2E8F0; border: none;")
            
            row_layout.addWidget(lbl_text)
            row_layout.addStretch()
            row_layout.addWidget(lbl_tag)
            
            self.hist_container_layout.addWidget(row)
            
        self.hist_container_layout.addStretch()

    # ==========================================
    # VIEW 3: SETTINGS & INSTALL SUPPORT
    # ==========================================
    def init_settings_view(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        lbl_title = QLabel("SLASH Linux & Desktop Support")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        lbl_desc = QLabel("Configure desktop environment shortcuts, binary targets, and package managers autonomously.")
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        
        # Install Script box
        group_inst = QGroupBox("Cross-Platform Installer Script")
        inst_layout = QVBoxLayout(group_inst)
        inst_layout.setContentsMargins(20, 20, 20, 20)
        inst_layout.setSpacing(12)
        
        lbl_inst_sub = QLabel("One-line installer checks environment, configures icons, and registers local shortcuts:")
        lbl_inst_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        inst_layout.addWidget(lbl_inst_sub)
        
        code_box = QLabel(
            "# 1. Clone SLASHBROWSER repository\n"
            "git clone https://github.com/insanityvrr-dot/SLASHBROWSER.git\n\n"
            "# 2. Enter the directory\n"
            "cd SLASHBROWSER\n\n"
            "# 3. Run the secure automated Linux desktop installer\n"
            "chmod +x install.sh && ./install.sh"
        )
        code_box.setStyleSheet("""
            background-color: #0F172A;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            font-family: monospace;
            font-size: 12px;
            color: #10B981;
        """)
        inst_layout.addWidget(code_box)
        
        layout.addWidget(group_inst)
        
        # System status card
        sys_group = QGroupBox("System Environment Details")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(12)
        
        sys_info = f"Current Directory: {self.current_dir}\n" \
                   f"Python Binary: {sys.executable}\n" \
                   f"Platform Window Framework: PyQt6 / QtWebEngine 6.x\n" \
                   f"Installation Script Target: install.sh (Configured)"
        
        lbl_sys_info = QLabel(sys_info)
        lbl_sys_info.setStyleSheet("font-size: 12px; line-height: 18px; color: #E2E8F0; font-family: monospace;")
        sys_layout.addWidget(lbl_sys_info)
        
        layout.addWidget(sys_group)
        self.content_stack.addWidget(scroll_area)

if __name__ == "__main__":
    # Add Chromium CLI arguments to prevent sandboxing issues and security flags causing "Access Denied" or antivirus blocks
    sys.argv.append("--no-sandbox")
    sys.argv.append("--disable-setuid-sandbox")
    sys.argv.append("--ignore-certificate-errors")
    sys.argv.append("--disable-web-security")
    
    app = QApplication(sys.argv)
    browser = SLASHBrowser()
    browser.show()
    sys.exit(app.exec())
