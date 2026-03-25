import os
from pathlib import Path

# ==================== CONFIG ====================

# Target Website
TARGET_URL = "https://rameshkumarsah.com.np"

# Proxy Settings
# Support for authenticated proxies: "http://user:pass@host:port" or "socks5://user:pass@host:port"
# Leave empty to only use free scraped proxies
PREMIUM_PROXIES = [] 

# Keywords for SEO (2026 Optimized)
KEYWORDS = [
    "biznex cloud", "biznexcloud",
    "software company nepal", "it company nepal", "best software company in nepal",
    "software development nepal", "custom software development nepal", 
    "web development nepal", "custom web development nepal",
    "digital transformation nepal", "digital transformation company nepal",
    "erp software nepal", "best erp in nepal", "erp system nepal", 
    "erp for small business nepal", "ai erp nepal", "ai powered erp nepal",
    "custom erp development nepal", "erp development nepal",
    "crm software nepal", "best crm nepal", "crm system nepal", 
    "crm development nepal", "crm for business nepal",
    "hrms software nepal", "hr management system nepal", "hrms in nepal", 
    "payroll software nepal",
    "hospital management system nepal", "healthcare management system nepal", 
    "hospital software nepal", "hospital erp nepal",
    "lms nepal", "learning management system nepal", "lms software nepal", 
    "online lms nepal",
    "ecommerce development nepal", "ecommerce website nepal", 
    "ecommerce platform nepal",
    "cloud solutions nepal", "cloud erp nepal", 
    "business automation nepal", "automation solutions nepal", "ai automation nepal",
    "ai chatbot nepal", "chatbot development nepal", "ai chatbot development nepal",
    "custom chatbot nepal", "intelligent chatbot nepal", "business chatbot nepal",
    "whatsapp chatbot nepal", "ai powered chatbot nepal", "chatbot for business nepal",
    "ai chatbot company nepal",
    "machine learning nepal", "ml development nepal", "machine learning solutions nepal",
    "ai ml company nepal", "ai ml development nepal",
    "artificial intelligence nepal", "ai development nepal", "ai consulting nepal",
    "machine learning software nepal", "predictive analytics nepal",
    "generative ai nepal", "generative ai solutions nepal", "generative ai development nepal",
    "agentic ai nepal", "agentic ai development nepal", "agentic ai solutions nepal", 
    "ai agents nepal", "autonomous ai agents nepal", 
    "agentic ai software company nepal", "intelligent automation nepal", 
    "ai software company nepal",
    "software company lalitpur", "it company lalitpur", "it solutions kathmandu",
    "software solutions lalitpur", "software development lalitpur", 
    "it company kathmandu", "best software company in lalitpur",
    "affordable erp nepal", "scalable software nepal", 
    "secure software development nepal",
    "inventory management software nepal", "school management system nepal", 
    "school erp nepal",
    "best it company in nepal", "digital solutions nepal", "business software nepal",
    "enterprise software solutions nepal", "it consulting nepal"
]

# Threading & Performance
THREADS = 20
PROXY_ROTATE_INTERVAL = 600  # 10 minutes
PORT = 5000

# Behavior Timing (seconds)
DWELL_MIN = 60
DWELL_MAX = 180
GOOGLE_WAIT_MIN = 10
GOOGLE_WAIT_MAX = 30

OUTPUT_FOLDER = "SEO_BOOSTER_2025"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "Ramesh@5611"