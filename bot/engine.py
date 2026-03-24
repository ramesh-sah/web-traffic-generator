import os
import random
import time
import csv
import threading
import concurrent.futures
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from curl_cffi import requests
from curl_cffi.requests import BrowserType

from bot.config import TARGET_URL, KEYWORDS, THREADS, OUTPUT_FOLDER, PROXY_ROTATE_INTERVAL
from bot.logger import logger

class SEOBoosterBot:
    def __init__(self):
        self.stats = {
            "visits": 0, "success": 0, "countries": set(), "pages": set(),
            "search_clicks": 0, "analytics_fired": 0, "start_time": None
        }
        self.stats_lock = threading.Lock()
        self.working_proxies = []
        self.proxy_lock = threading.Lock()
        
        self.is_running = False
        self.stop_event = threading.Event()
        self.threads = []
        
        # Init CSV LOG
        log_path = os.path.join(OUTPUT_FOLDER, "traffic_log.csv")
        if not os.path.exists(log_path):
            with open(log_path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["Time", "Type", "Page", "IP", "Country", "Dwell", "Analytics Fired"])

    def get_proxies(self):
        sources = [
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://api.openproxylist.xyz/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/mertguvencli/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",
            "https://raw.githubusercontent.com/My-Proxy-List/main/http.txt",
            "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
            "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
            "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
            "https://cdn.jsdelivr.net/gh/databay-labs/free-proxy-list/http.txt",
            "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&country=all&anonymity=all&timeout=20000&proxy_format=ipport&format=text",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/proxies/http.txt",
            "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/http.txt",
            "https://raw.githubusercontent.com/opsxcq/proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
            "https://raw.githubusercontent.com/proxy-list-org/free/master/proxies/http.txt",
            "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt",
            "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
            "https://www.proxyscan.io/api/proxy?format=txt&type=http",
            "http://pubproxy.com/api/proxy?limit=20&format=txt&type=http",
            "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
            "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
            "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
            "https://cyber-hub.pw/statics/proxy.txt",
            "https://api.proxylist.net/free?format=txt&protocol=http"
        ]
        proxies = set()
        s = requests.Session(impersonate="chrome120")
        for url in sources:
            if self.stop_event.is_set():
                break
            try:
                r = s.get(url, timeout=12)
                for line in r.text.splitlines():
                    line = line.strip()
                    if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", line):
                        proxies.add(f"http://{line}")
            except: 
                pass
        return list(proxies)

    def get_country_from_ip(self, ip):
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5)
            if r.status_code == 200:
                return r.json().get("countryCode", "XX")
        except: pass
        try:
            r = requests.get(f"https://ipapi.co/{ip}/country/", timeout=5)
            if r.status_code == 200:
                return r.text.strip()
        except: pass
        return "XX"

    def test_proxy(self, p):
        if self.stop_event.is_set():
            return None
        try:
            start = time.time()
            r = requests.get("https://httpbin.org/ip", proxies={"http": p, "https": p},
                             timeout=9, impersonate="chrome120")
            if r.status_code == 200:
                latency = (time.time() - start) * 1000
                ip = r.json()["origin"].split(",")[0]
                country = self.get_country_from_ip(ip)
                score = 95 if latency < 300 else 80 if latency < 700 else 65
                return {"proxy": p, "ip": ip, "country": country, "score": score}
        except: pass
        return None

    def build_proxy_pool(self):
        logger.info("Fetching & testing 15,000+ proxies...")
        raw = self.get_proxies()
        
        # Determine number of workers based on how many raw items
        # To not blow up memory, limiting to 1200 workers max.
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(raw) + 1, 1200)) as ex:
            results = list(ex.map(self.test_proxy, raw))
            
        good = [p for p in results if p and p["score"] >= 65]
        good.sort(key=lambda x: x["score"], reverse=True)
        
        with self.proxy_lock:
            self.working_proxies = good[:600]
            
        logger.info(f"[SUCCESS] {len(self.working_proxies)} ELITE PROXIES LOADED & READY!")

    def proxy_refresher(self):
        while not self.stop_event.is_set():
            # Wait for either interval to pass, or stop_event to be set
            if self.stop_event.wait(PROXY_ROTATE_INTERVAL):
                break
            logger.info("[ROTATOR] Refreshing proxy pool...")
            self.build_proxy_pool()

    def fire_analytics(self, sess, url):
        fired = 0
        try:
            html = sess.get(url, timeout=60).text
            soup = BeautifulSoup(html, 'html.parser')
            for script in soup.find_all('script', src=True):
                src = script['src']
                if any(k in src.lower() for k in ['gtag', 'analytics', 'googletagmanager', 'umami', 'plausible', 'collect', 'vercel']):
                    try:
                        sess.get(urljoin(url, src), timeout=15)
                        fired += 2
                    except: pass
            for tag in soup.find_all(['img', 'link', 'source'], src=True):
                try:
                    sess.get(urljoin(url, tag['src']), timeout=10)
                    fired += 0.4
                except: pass
            events = [
                url + "?ref=google",
                url + "?utm_source=google&utm_medium=organic&utm_campaign=seo",
                url + "#contact",
                url + "?t=" + str(int(time.time()*1000)),
                url + "/?loaded=1"
            ]
            for e in events[:3]:
                try:
                    sess.get(e, timeout=12)
                    fired += 0.6
                except: pass
            
            if not self.stop_event.is_set():
                time.sleep(random.uniform(60, 200)) # Changed to sleep directly, this is a deep wait.
        except: pass
        return int(fired)

    def get_session(self, proxy):
        s = requests.Session(impersonate=BrowserType.chrome120, timeout=70)
        s.headers.update({
            "User-Agent": random.choice([
                f"Mozilla/5.0 (Windows NT {random.choice(['10.0','11.0'])}; Win64; x64) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.{random.randint(6700,6999)}.{random.randint(50,400)} Safari/537.36"
                for _ in range(200)
            ]),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.google.com/"
        })
        if proxy and proxy["proxy"]:
            s.proxies = {"http": proxy["proxy"], "https": proxy["proxy"]}
        return s

    def simulate_human(self):
        current = TARGET_URL
        while not self.stop_event.is_set():
            if len(self.working_proxies) < 50:
                self.stop_event.wait(15)
                continue
                
            with self.proxy_lock:
                if not self.working_proxies:
                    # Should not reach here if the above check passed, but just in case
                    self.stop_event.wait(5)
                    continue
                proxy = random.choice(self.working_proxies)
                
            sess = self.get_session(proxy)
            try:
                # 90% GOOGLE ORGANIC PATH
                if random.random() < 0.90:
                    kw = random.choice(KEYWORDS)
                    
                    # REAL TYPING SIMULATION
                    for i in range(1, len(kw) + 1):
                        if self.stop_event.is_set(): break
                        try:
                            sess.get(f"https://www.google.com/search?q={quote(kw[:i])}", timeout=38)
                            time.sleep(random.uniform(0.3, 0.9))
                        except: pass
                    
                    if self.stop_event.is_set(): break
                    sess.get(f"https://www.google.com/search?q={quote(kw)}&num=100", timeout=45)
                    self.stop_event.wait(random.uniform(11, 28))

                    start = time.time()
                    sess.get(TARGET_URL + "?utm_source=google&utm_medium=organic&utm_term=" + quote(kw), timeout=70)
                    
                    # MOUSE + SCROLL SIMULATION
                    for _ in range(random.randint(8, 15)):
                        if self.stop_event.is_set(): break
                        sess.get(TARGET_URL + f"?move={random.randint(180,1720)}x{random.randint(90,980)}", timeout=12)
                        sess.get(TARGET_URL + f"?scroll={random.randint(1800,5200)}", timeout=12)
                        self.stop_event.wait(random.uniform(6, 24))

                    if self.stop_event.is_set(): break

                    dwell = time.time() - start
                    fired = self.fire_analytics(sess, TARGET_URL)
                    logger.info(f"[ORGANIC 90%] '{kw}' → {proxy['ip']} | {dwell:.0f}s | +{fired} EVENTS")
                    
                    with self.stats_lock:
                        self.stats["search_clicks"] += 1
                        self.stats["analytics_fired"] += fired
                    self.log_visit("ORGANIC", "home", proxy["ip"], proxy["country"], dwell, fired)
                    
                    if random.random() < 0.70:
                        self.stop_event.wait(random.uniform(45, 140))
                        continue

                # 10% DEEP CRAWL
                start = time.time()
                r = sess.get(current, timeout=60)
                dwell = time.time() - start
                page = urlparse(current).path.split("/")[-1] or "home"
                fired = self.fire_analytics(sess, current)
                
                logger.info(f"[DEEP 10%] {page} | {proxy['ip']} | {dwell:.0f}s | +{fired} EVENTS")
                self.log_visit("DIRECT", page, proxy["ip"], proxy["country"], dwell, fired)

                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = urljoin(current, a['href'].split('#')[0])
                        if (urlparse(href).netloc == urlparse(TARGET_URL).netloc
                            and not any(href.lower().endswith(ext) for ext in ['.png','.jpg','.js','.css','.pdf','.webp','.svg'])):
                            links.append(href)
                    current = random.choice(links + [TARGET_URL, TARGET_URL + "/about", TARGET_URL + "/contact"]) if links else TARGET_URL
            except:
                self.stop_event.wait(8)

    def log_visit(self, type_, page, ip, country, dwell, fired):
        with self.stats_lock:
            self.stats["visits"] += 1
            self.stats["success"] += 1
            if country != "XX":
                self.stats["countries"].add(country)
            self.stats["pages"].add(page)
            
            with open(f"{OUTPUT_FOLDER}/traffic_log.csv", "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    datetime.now().strftime("%H:%M:%S"), type_, page, ip, country,
                    f"{dwell:.1f}s", fired
                ])

    def get_stats(self):
        with self.stats_lock:
            uptime = 0
            if self.stats["start_time"]:
                uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
            
            # Formatting country string for UI similar to the old terminal logic
            country_counts = {}
            for c in self.stats["countries"]:
                country_counts[c] = country_counts.get(c, 0) + 1
            top_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            country_str = " | ".join([f"{c}" for c, _ in top_countries])
            if len(self.stats["countries"]) > 8:
                country_str += f" +{len(self.stats['countries'])-8} more"
            
            return {
                "visits": self.stats["success"],
                "unique_countries": len(self.stats["countries"]),
                "countries_str": country_str if country_str else "N/A",
                "search_clicks": self.stats["search_clicks"],
                "analytics_fired": int(self.stats["analytics_fired"]),
                "uptime": uptime,
                "is_running": self.is_running,
                "active_proxies": len(self.working_proxies),
                "threads": THREADS,
                "target_url": TARGET_URL
            }

    def start(self):
        if self.is_running:
            return False
            
        logger.info("Starting SEO Booster Bot...")
        self.is_running = True
        self.stop_event.clear()
        
        with self.stats_lock:
            if not self.stats["start_time"]:
                self.stats["start_time"] = datetime.now()
        
        # We start the initialization process in a background thread to not block the caller
        t_init = threading.Thread(target=self._start_internal, daemon=True)
        t_init.start()
        
        return True

    def _start_internal(self):
        # Initial proxy load
        self.build_proxy_pool()
        
        if self.stop_event.is_set():
            return
            
        # Start proxy refresher
        t = threading.Thread(target=self.proxy_refresher, daemon=True)
        t.start()
        self.threads.append(t)
        
        # Start workers
        logger.info(f"[LAUNCH] Starting {THREADS} REAL HUMAN THREADS...")
        for _ in range(THREADS):
            t = threading.Thread(target=self.simulate_human, daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        if not self.is_running:
            return False
            
        logger.info("Stopping SEO Booster Bot... Please wait.")
        self.stop_event.set()
        self.is_running = False
        self.threads = []
        return True

# Global instance
bot = SEOBoosterBot()
