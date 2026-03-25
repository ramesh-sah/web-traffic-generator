import os
import random
import time
import csv
import threading
import concurrent.futures
import re
import json
from datetime import datetime
from typing import Optional, Set
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from curl_cffi import requests
from curl_cffi.requests import BrowserType

from bot.config import (
    TARGET_URL, KEYWORDS, THREADS, OUTPUT_FOLDER, 
    PROXY_ROTATE_INTERVAL, PREMIUM_PROXIES,
    DWELL_MIN, DWELL_MAX, GOOGLE_WAIT_MIN, GOOGLE_WAIT_MAX
)
from bot.logger import logger

class SEOBoosterBot:
    def __init__(self):
        # Stats Initialization - Individual attributes with type hints
        self.total_visits: int = 0
        self.successful_visits: int = 0
        self.search_clicks: int = 0
        self.analytics_fired_count: int = 0
        self.unique_countries: set = set()
        self.unique_pages: set = set()
        self.start_time: Optional[datetime] = None
        self.stats_lock = threading.Lock()
        
        self.working_proxies = []
        self.proxy_lock = threading.Lock()
        
        self.is_running = False
        self.stop_event = threading.Event()
        self.threads = []
        
        # Init CSV LOG
        self.log_path = os.path.join(OUTPUT_FOLDER, "traffic_log.csv")
        if not os.path.exists(self.log_path):
            try:
                with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow(["Time", "Type", "Page", "IP", "Country", "Dwell", "Analytics Fired"])
            except Exception as e:
                logger.error(f"Failed to initialize log file: {e}")

    def get_proxies(self):
        """Scrape free proxies from various sources."""
        sources = [
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&proxy_format=ipport&format=text",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/proxies/http.txt",
            "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
        ]
        proxies = set()
        s = requests.Session(impersonate="chrome120")
        for url in sources:
            if self.stop_event.is_set():
                break
            try:
                r = s.get(url, timeout=10)
                if r.status_code == 200:
                    for line in r.text.splitlines():
                        line = line.strip()
                        if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", line):
                            proxies.add(f"http://{line}")
            except Exception as e:
                logger.debug(f"Failed to fetch proxies from {url}: {e}")
        return list(proxies)

    def get_country_from_ip(self, ip):
        """Estimate country from IP."""
        if ip == "PREMIUM": return "US"
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5)
            if r.status_code == 200:
                return r.json().get("countryCode", "XX")
        except: pass
        return "XX"

    def test_proxy(self, p_url):
        """Test proxy speed and anonymity."""
        if self.stop_event.is_set():
            return None
        try:
            start = time.time()
            proxies = {"http": p_url, "https": p_url}
            r = requests.get("https://httpbin.org/ip", proxies=proxies,
                             timeout=10, impersonate="chrome120")
            if r.status_code == 200:
                latency = (time.time() - start) * 1000
                ip = r.json()["origin"].split(",")[0]
                country = self.get_country_from_ip(ip)
                score = 100 if latency < 200 else 85 if latency < 500 else 70
                return {"proxy": p_url, "ip": ip, "country": country, "score": score}
        except: pass
        return None

    def build_proxy_pool(self):
        """Refresh the proxy pool with both premium and tested free proxies."""
        logger.info("Initializing Proxy Pool...")
        
        pool = []
        for p in PREMIUM_PROXIES:
            pool.append({"proxy": p, "ip": "PREMIUM", "country": "US", "score": 100})
            
        raw_list = self.get_proxies()
        if raw_list:
            logger.info(f"Scraped {len(raw_list)} raw proxies. Testing...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(raw_list) + 1, 100)) as ex:
                results = list(ex.map(self.test_proxy, raw_list))
            
            good_free = [p for p in results if p and p.get("score", 0) >= 70]
            good_free.sort(key=lambda x: x.get("score", 0), reverse=True)
            pool.extend(good_free[:500])
        
        with self.proxy_lock:
            self.working_proxies = pool
            
        logger.info(f"[PROXY] Pool refreshed. Total: {len(self.working_proxies)} (Premium: {len(PREMIUM_PROXIES)})")

    def proxy_refresher(self):
        while not self.stop_event.is_set():
            if self.stop_event.wait(PROXY_ROTATE_INTERVAL):
                break
            self.build_proxy_pool()

    def fire_analytics(self, sess, url, client_id):
        """Simulate ultra-realistic GA4 collection requests."""
        count = 0
        try:
            # 1. Get the page content
            r = sess.get(url, timeout=30)
            if r.status_code != 200: return 0
            
            # Extract tracking ID
            tid_match = re.search(r'G-([A-Z0-9]{10})', r.text)
            tid = tid_match.group(0) if tid_match else "G-DUMMY12345"
            
            # Extract title dynamically
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.title.string if soup.title else "Biznex Cloud"
            
            # 2. Authentic GA4 Parameters
            sid = str(random.randint(1000000000, 9999999999))
            res = random.choice(["1920x1080", "1440x900", "1366x768", "1536x864", "1280x720"])
            
            collect_base = "https://www.google-analytics.com/g/collect"
            params = (f"?v=2&tid={tid}&cid={client_id}&_sid={sid}&_sct=1&_seg=1"
                      f"&dl={quote(url)}&dt={quote(title)}&sr={res}&ul=en-us")
            
            # Fire page_view
            sess.get(collect_base + params + "&en=page_view", timeout=10)
            count += 1
            
            # 3. Engagement signal (Crucial for SEO metrics)
            if random.random() < 0.8:
                time.sleep(random.uniform(10, 20))
                engagement_time = random.randint(15000, 45000) # 15-45s of active engagement
                sess.get(collect_base + params + f"&en=user_engagement&_et={engagement_time}", timeout=10)
                count += 1
        except Exception as e:
            logger.debug(f"GA4 signal failed: {e}")
        return count

    def get_session(self, proxy_data):
        """Create a session with realistic browser headers."""
        # impersonate chrome120 handles most fingerprint headers automatically
        s = requests.Session(impersonate=BrowserType.chrome120, timeout=60)
        
        # Professional User-Agent rotation
        chrome_ver = random.randint(120, 131)
        version = f"{chrome_ver}.0.{random.randint(6000, 7000)}.{random.randint(10, 200)}"
        ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        
        s.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": f'"Not_A Brand";v="8", "Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })
        
        if proxy_data and proxy_data.get("proxy"):
            p = proxy_data["proxy"]
            s.proxies = {"http": p, "https": p}
        return s

    def simulate_human(self):
        """Main bot loop with human-like behavior."""
        while not self.stop_event.is_set():
            with self.proxy_lock:
                if not self.working_proxies:
                    self.stop_event.wait(5)
                    continue
                proxy = random.choice(self.working_proxies)
                
            sess = self.get_session(proxy)
            # Consistent GA4 Client ID for the entire lifecycle of this "user"
            client_id = f"{random.randint(100000000, 999999999)}.{random.randint(1000000000, 2147483647)}"
            
            try:
                # 85% Organic Search Path, 15% Social/Direct Referrer Path
                if random.random() < 0.85:
                    kw = random.choice(KEYWORDS)
                    logger.info(f"[SEARCH] Routing through Google for: {kw}")
                    sess.headers.update({"Referer": "https://www.google.com/"})
                    
                    # 1. Simulate Google Search Action
                    sess.get(f"https://www.google.com/search?q={quote(kw)}&sourceid=chrome&ie=UTF-8", timeout=40)
                    self.stop_event.wait(random.uniform(GOOGLE_WAIT_MIN, GOOGLE_WAIT_MAX))
                    
                    # 2. Click result with UTM parameters for tracking
                    target_entry = f"{TARGET_URL}/?utm_source=google&utm_medium=organic&utm_campaign=seo&utm_term={quote(kw)}"
                    dwell_time = random.uniform(DWELL_MIN, DWELL_MAX)
                    end_time = time.time() + dwell_time
                    
                    events = self.fire_analytics(sess, target_entry, client_id)
                    
                    # 3. Simulate page interaction (Scroll)
                    while time.time() < end_time and not self.stop_event.is_set():
                        # Random scroll events to trigger HEATMAPS and behavior trackers
                        sess.get(f"{TARGET_URL}/?action=scroll&pos={random.randint(500, 5000)}", timeout=10)
                        if random.random() < 0.15:
                            events += self.fire_analytics(sess, target_entry, client_id)
                        self.stop_event.wait(random.uniform(15, 45))

                    self.log_visit("ORGANIC", "home", proxy.get("ip", "0.0.0.0"), proxy.get("country", "XX"), dwell_time, events)
                    with self.stats_lock:
                        self.search_clicks += 1
                        self.analytics_fired_count += events
                else:
                    # Diversified Referrers for "Direct" traffic
                    referrers = ["https://www.facebook.com/", "https://t.co/", "https://www.linkedin.com/", ""]
                    ref = random.choice(referrers)
                    if ref: sess.headers.update({"Referer": ref})
                    
                    events = self.fire_analytics(sess, TARGET_URL, client_id)
                    self.log_visit("DIRECT/SOCIAL", "home", proxy.get("ip", "0.0.0.0"), proxy.get("country", "XX"), 45, events)
                    with self.stats_lock:
                        self.analytics_fired_count += events
                        
            except Exception as e:
                logger.debug(f"Worker iteration failed: {e}")
                self.stop_event.wait(5)

    def log_visit(self, type_, page, ip, country, dwell, fired):
        with self.stats_lock:
            self.total_visits += 1
            self.successful_visits += 1
            if country != "XX":
                self.unique_countries.add(country)
            self.unique_pages.add(page)
            
            try:
                with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type_, page, ip, country,
                        f"{dwell:.1f}s", fired
                    ])
            except Exception as e:
                logger.error(f"Failed to log visit: {e}")

    def get_stats(self):
        with self.stats_lock:
            uptime = 0
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
            
            countries = list(self.unique_countries)
            top_countries = countries[:5]
            country_str = ", ".join(top_countries) if top_countries else "N/A"
            
            return {
                "visits": self.successful_visits,
                "unique_countries": len(countries),
                "countries_str": country_str,
                "search_clicks": self.search_clicks,
                "analytics_fired": int(self.analytics_fired_count),
                "uptime": uptime,
                "is_running": self.is_running,
                "active_proxies": len(self.working_proxies),
                "threads": THREADS,
                "target_url": TARGET_URL
            }

    def start(self):
        if self.is_running: return False
        logger.info("Starting SEO Booster Engine...")
        self.is_running = True
        self.stop_event.clear()
        with self.stats_lock:
            if not self.start_time:
                self.start_time = datetime.now()
        t_init = threading.Thread(target=self._start_internal, daemon=True)
        t_init.start()
        return True

    def _start_internal(self):
        self.build_proxy_pool()
        if self.stop_event.is_set(): return
        t_rot = threading.Thread(target=self.proxy_refresher, daemon=True)
        t_rot.start()
        self.threads.append(t_rot)
        for _ in range(THREADS):
            t = threading.Thread(target=self.simulate_human, daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        if not self.is_running: return False
        logger.info("Stopping Engine... Finishing active sessions.")
        self.stop_event.set()
        self.is_running = False
        self.threads = []
        return True

bot = SEOBoosterBot()
