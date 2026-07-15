import sys
import os
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QToolBar, QStatusBar, QLabel
)
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile

class SLASHBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SLASH")
        self.setMinimumSize(1024, 768)
        
        # Set window icon to our generated icon if it exists
        icon_path = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/slash.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # Get absolute path for local home.html
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.home_html_path = os.path.join(self.current_dir, "home.html")
        
        # Central Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)
        
        # Navigation Bar
        self.nav_bar = QToolBar("Navigation")
        self.nav_bar.setIconSize(QSize(18, 18))
        self.addToolBar(self.nav_bar)
        
        # Back Button
        self.back_btn = QPushButton("←")
        self.back_btn.setToolTip("Go Back")
        self.back_btn.clicked.connect(lambda: self.active_browser().back() if self.active_browser() else None)
        self.nav_bar.addWidget(self.back_btn)
        
        # Forward Button
        self.forward_btn = QPushButton("→")
        self.forward_btn.setToolTip("Go Forward")
        self.forward_btn.clicked.connect(lambda: self.active_browser().forward() if self.active_browser() else None)
        self.nav_bar.addWidget(self.forward_btn)
        
        # Reload Button
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setToolTip("Reload Page")
        self.reload_btn.clicked.connect(lambda: self.active_browser().reload() if self.active_browser() else None)
        self.nav_bar.addWidget(self.reload_btn)
        
        # Home Button
        self.home_btn = QPushButton("⌂")
        self.home_btn.setToolTip("Go Home")
        self.home_btn.clicked.connect(self.navigate_home)
        self.nav_bar.addWidget(self.home_btn)
        
        # Address bar (URL or Search Input)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search with DuckDuckGo or enter URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.nav_bar.addWidget(self.url_bar)
        
        # New tab button
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        self.nav_bar.addWidget(self.new_tab_btn)
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        
        # Apply clean dark slate + sky blue Material 3 styling
        self.apply_theme()
        
        # Open default starting tab
        self.add_new_tab(QUrl.fromLocalFile(self.home_html_path), "Home")
        
    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F172A;
            }
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
            QLineEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
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
                padding: 10px 20px;
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
        """)

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
        
        browser.urlChanged.connect(lambda qurl, b=browser: self.update_urlbar(qurl, b))
        browser.loadFinished.connect(lambda _, index=i, b=browser: self.update_tab_title(index, b))
        
    def handle_create_window(self, _type):
        # Dynamically spawn target="_blank" links in a new tab instead of a separate window
        browser = QWebEngineView()
        i = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, b=browser: self.update_urlbar(qurl, b))
        browser.loadFinished.connect(lambda _, index=i, b=browser: self.update_tab_title(index, b))
        return browser
        
    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            # If it's the last tab, reset it back to home instead of leaving empty screen
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
        # Hide absolute path of our local home.html inside the address bar for polish
        if "home.html" in q.toString():
            self.url_bar.setText("")
        else:
            self.url_bar.setText(q.toString())
            
    def update_tab_title(self, index, browser):
        title = browser.page().title()
        if not title:
            title = "Home" if "home.html" in browser.url().toString() else "SLASH"
            
        # Truncate title if it's too long
        if len(title) > 20:
            title = title[:17] + "..."
            
        # Find exact tab index dynamically in case indexing changed
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
            # Auto-append https protocol if user writes a domain like google.com
            if "." in text and " " not in text:
                q = QUrl("https://" + text)
            else:
                # Default search engine redirect (secure query on DuckDuckGo)
                q = QUrl(f"https://duckduckgo.com/?q={text}")
                
        if self.active_browser():
            self.active_browser().setUrl(q)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = SLASHBrowser()
    browser.show()
    sys.exit(app.exec())
