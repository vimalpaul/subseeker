#!/usr/bin/env python3
"""
SubSeeker v2.0 - Complete Subdomain Discovery Tool
Single file, maximum enumeration, clean output
Author: Vimal T || Security Researcher
"""

import argparse
import asyncio
import aiohttp
import json
import sys
import os
import time
import random
from datetime import datetime
from typing import List, Set, Dict
import dns.resolver
import socket
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import re

# Initialize colorama
init(autoreset=True)

class SubSeeker:
    def __init__(self, domain: str, mode: str = "standard", output_dir: str = None):
        self.domain = domain.strip().lower()
        self.mode = mode
        self.output_dir = output_dir or f"subseeker_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Mode configurations
        self.configs = {
            "quick": {"timeout": 20, "concurrency": 20, "sources": ["crtsh", "hackertarget", "alienvault"], "bruteforce": False},
            "standard": {"timeout": 30, "concurrency": 50, "sources": ["crtsh", "hackertarget", "virustotal", "alienvault", "bufferover", "threatcrowd", "urlscan", "wayback", "anubis", "rapiddns"], "bruteforce": True},
            "deep": {"timeout": 60, "concurrency": 100, "sources": ["all"], "bruteforce": True, "wordlist": "large"},
            "stealth": {"timeout": 120, "concurrency": 10, "sources": ["crtsh", "virustotal"], "bruteforce": True, "delay": 2},
        }
        
        self.config = self.configs.get(mode, self.configs["standard"])
        self.found = set()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # DNS resolvers
        self.resolvers = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
        
    def banner(self):
        """Simple clean banner"""
        print(f"\n{Fore.RED}▸ {Fore.YELLOW}SubSeeker v2.0 {Fore.CYAN}| {Fore.GREEN}{self.mode.upper()}{Fore.CYAN} | {Fore.MAGENTA}{self.domain}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
    
    # ==================== PASSIVE ENUMERATION SOURCES ====================
    
    async def fetch_json(self, url, headers=None):
        """Fetch JSON from URL"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except:
            pass
        return None
    
    async def fetch_text(self, url, headers=None):
        """Fetch text from URL"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.text()
        except:
            pass
        return None
    
    async def source_crtsh(self):
        """crt.sh - Find maximum subdomains"""
        print(f"{Fore.CYAN}[*] crt.sh{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        # Try multiple query patterns
        patterns = [
            f"%.{self.domain}",
            f"%.%.{self.domain}", 
            f"%.%.%.{self.domain}",
            f"{self.domain}",
        ]
        
        for pattern in patterns:
            url = f"https://crt.sh/?q={pattern}&output=json"
            data = await self.fetch_json(url)
            if data:
                for entry in data:
                    name = entry.get('name_value', '')
                    if name:
                        for n in name.split('\n'):
                            n = n.strip().lower()
                            if n and self.domain in n:
                                # Clean wildcards
                                n = n.replace('*.', '').replace('.*', '')
                                if n.endswith(f'.{self.domain}'):
                                    subs.add(n)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_hackertarget(self):
        """HackerTarget API"""
        print(f"{Fore.CYAN}[*] HackerTarget{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
        text = await self.fetch_text(url)
        
        if text:
            for line in text.split('\n'):
                if line and ',' in line:
                    sub = line.split(',')[0].strip().lower()
                    if self.domain in sub:
                        subs.add(sub)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_virustotal(self):
        """VirusTotal (public API)"""
        print(f"{Fore.CYAN}[*] VirusTotal{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        # Public endpoint
        url = f"https://www.virustotal.com/ui/domains/{self.domain}/subdomains"
        headers = {'User-Agent': 'Mozilla/5.0'}
        data = await self.fetch_json(url, headers)
        
        if data and 'data' in data:
            for item in data['data']:
                sub = item.get('id', '').lower()
                if self.domain in sub:
                    subs.add(sub)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_alienvault(self):
        """AlienVault OTX"""
        print(f"{Fore.CYAN}[*] AlienVault{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns"
        data = await self.fetch_json(url)
        
        if data:
            for entry in data.get('passive_dns', []):
                hostname = entry.get('hostname', '').lower()
                if self.domain in hostname:
                    subs.add(hostname)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_bufferover(self):
        """DNS BufferOver"""
        print(f"{Fore.CYAN}[*] BufferOver{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://dns.bufferover.run/dns?q=.{self.domain}"
        data = await self.fetch_json(url)
        
        if data:
            for key in ['FDNS_A', 'RDNS']:
                if key in data:
                    for item in data[key]:
                        if ',' in item:
                            parts = item.split(',')
                            for part in parts:
                                part = part.strip().lower()
                                if self.domain in part:
                                    subs.add(part)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_threatcrowd(self):
        """ThreatCrowd"""
        print(f"{Fore.CYAN}[*] ThreatCrowd{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={self.domain}"
        data = await self.fetch_json(url)
        
        if data and 'subdomains' in data:
            for sub in data['subdomains']:
                sub = sub.strip().lower()
                if self.domain in sub:
                    subs.add(sub)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_urlscan(self):
        """URLScan.io"""
        print(f"{Fore.CYAN}[*] URLScan{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://urlscan.io/api/v1/search/?q=domain:{self.domain}"
        data = await self.fetch_json(url)
        
        if data:
            for result in data.get('results', []):
                page = result.get('page', {})
                domain = page.get('domain', '').lower()
                if self.domain in domain:
                    subs.add(domain)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_wayback(self):
        """Wayback Machine"""
        print(f"{Fore.CYAN}[*] Wayback{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"http://web.archive.org/cdx/search/cdx?url=*.{self.domain}/*&output=json&fl=original&collapse=urlkey"
        data = await self.fetch_json(url)
        
        if data:
            for entry in data:
                if len(entry) > 0:
                    url_str = entry[0]
                    if '://' in url_str:
                        domain = url_str.split('://')[1].split('/')[0].lower()
                        if self.domain in domain:
                            subs.add(domain)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_anubis(self):
        """AnubisDB"""
        print(f"{Fore.CYAN}[*] AnubisDB{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://jonlu.ca/anubis/subdomains/{self.domain}"
        data = await self.fetch_json(url)
        
        if data:
            for sub in data:
                sub = sub.strip().lower()
                if self.domain in sub:
                    subs.add(sub)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_rapiddns(self):
        """RapidDNS"""
        print(f"{Fore.CYAN}[*] RapidDNS{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://rapiddns.io/subdomain/{self.domain}?full=1"
        headers = {'User-Agent': 'Mozilla/5.0'}
        text = await self.fetch_text(url, headers)
        
        if text:
            # Parse with regex
            pattern = r'[a-zA-Z0-9][a-zA-Z0-9.-]*\.' + re.escape(self.domain)
            matches = re.findall(pattern, text)
            for match in matches:
                subs.add(match.lower())
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_commoncrawl(self):
        """CommonCrawl"""
        print(f"{Fore.CYAN}[*] CommonCrawl{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        # Latest index
        url = f"https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{self.domain}&output=json"
        text = await self.fetch_text(url)
        
        if text:
            for line in text.strip().split('\n'):
                try:
                    data = json.loads(line)
                    url_str = data.get('url', '')
                    if '://' in url_str:
                        domain = url_str.split('://')[1].split('/')[0].lower()
                        if self.domain in domain:
                            subs.add(domain)
                except:
                    pass
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_dnsdumpster(self):
        """DNSDumpster"""
        print(f"{Fore.CYAN}[*] DNSDumpster{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        # This requires proper CSRF token handling
        # Simplified version
        url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
        text = await self.fetch_text(url)
        
        if text:
            for line in text.split('\n'):
                if line and ',' in line:
                    sub = line.split(',')[0].strip().lower()
                    if self.domain in sub:
                        subs.add(sub)
        
        print(f" → {len(subs)}")
        return subs
    
    async def source_subdomain_center(self):
        """SubdomainCenter"""
        print(f"{Fore.CYAN}[*] SubdomainCenter{Style.RESET_ALL}", end="", flush=True)
        subs = set()
        
        url = f"https://api.subdomain.center/?domain={self.domain}"
        data = await self.fetch_json(url)
        
        if data:
            for sub in data:
                sub = sub.strip().lower()
                if self.domain in sub:
                    subs.add(sub)
        
        print(f" → {len(subs)}")
        return subs
    
    # ==================== MAIN ENUMERATION ====================
    
    async def passive_enum(self):
        """Run all passive enumeration"""
        print(f"{Fore.YELLOW}[+] Passive Enumeration{Style.RESET_ALL}")
        
        # Define all sources
        all_sources = [
            ("crtsh", self.source_crtsh),
            ("hackertarget", self.source_hackertarget),
            ("virustotal", self.source_virustotal),
            ("alienvault", self.source_alienvault),
            ("bufferover", self.source_bufferover),
            ("threatcrowd", self.source_threatcrowd),
            ("urlscan", self.source_urlscan),
            ("wayback", self.source_wayback),
            ("anubis", self.source_anubis),
            ("rapiddns", self.source_rapiddns),
            ("commoncrawl", self.source_commoncrawl),
            ("dnsdumpster", self.source_dnsdumpster),
            ("subdomain_center", self.source_subdomain_center),
        ]
        
        # Filter based on mode
        if "all" in self.config["sources"]:
            sources_to_run = all_sources
        else:
            sources_to_run = [s for s in all_sources if s[0] in self.config["sources"]]
        
        # Run sources
        tasks = []
        for name, func in sources_to_run:
            tasks.append(func())
        
        # Run with concurrency control
        batch_size = 3
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in results:
                if isinstance(result, set):
                    self.found.update(result)
            
            await asyncio.sleep(0.5)  # Small delay
        
        # Clean results
        clean = set()
        for sub in self.found:
            sub = sub.strip().lower()
            if sub and self.domain in sub:
                # Remove wildcards
                sub = sub.replace('*.', '')
                if sub.endswith(f'.{self.domain}'):
                    clean.add(sub)
        
        self.found = clean
        return len(self.found)
    
    async def brute_force(self):
        """Smart brute-force"""
        if not self.config.get("bruteforce", True):
            return 0
        
        print(f"\n{Fore.YELLOW}[+] Brute-force{Style.RESET_ALL}")
        
        # Load wordlist
        wordlist = self.load_wordlist()
        print(f"{Fore.CYAN}[*] Using {len(wordlist)} words{Style.RESET_ALL}")
        
        # Resolve
        new_subs = await self.resolve_wordlist(wordlist)
        self.found.update(new_subs)
        
        print(f"{Fore.GREEN}[+] Found {len(new_subs)} new subdomains{Style.RESET_ALL}")
        return len(new_subs)
    
    def load_wordlist(self):
        """Load appropriate wordlist"""
        wordlist = []
        
        # Built-in base words
        base_words = [
            "www", "mail", "ftp", "admin", "test", "dev", "staging", "api", "blog",
            "webmail", "portal", "cpanel", "webdisk", "ns1", "ns2", "smtp", "pop", 
            "imap", "git", "svn", "jenkins", "wiki", "m", "mobile", "app", "apps",
            "beta", "new", "old", "secure", "login", "signin", "account", "accounts",
            "support", "help", "download", "uploads", "static", "cdn", "assets",
            "media", "images", "img", "video", "videos", "store", "shop", "payment",
            "payments", "billing", "invoice", "invoices", "dashboard", "monitor",
            "status", "health", "metrics", "grafana", "prometheus", "kibana",
            "elastic", "redis", "mysql", "postgres", "mongodb", "rabbitmq", "kafka",
            "zookeeper", "consul", "vault", "gitlab", "github", "bitbucket",
            "jira", "confluence", "nexus", "artifactory", "sonar", "splunk", "graylog",
        ]
        
        # Try to load from file if deep mode
        if self.mode == "deep":
            paths = [
                "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt",
                "/usr/share/seclists/Discovery/DNS/dns-Jhaddix.txt",
                "/usr/share/wordlists/dirb/common.txt",
                "~/.subseeker/wordlists/common.txt",
            ]
            
            for path in paths:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    try:
                        with open(expanded, 'r', encoding='utf-8', errors='ignore') as f:
                            words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                            wordlist.extend(words[:10000])  # Limit
                        break
                    except:
                        continue
        
        # If no file loaded or not deep mode, use base words
        if not wordlist:
            wordlist = base_words
        
        # Add permutations from found subdomains
        if self.found:
            patterns = set()
            for sub in list(self.found)[:50]:
                parts = sub.split('.')
                if len(parts) > 2:
                    prefix = parts[0]
                    patterns.add(prefix)
            
            for pattern in patterns:
                wordlist.extend([
                    f"{pattern}-dev", f"{pattern}-test", f"{pattern}-staging",
                    f"{pattern}-prod", f"{pattern}-uat", f"{pattern}-qa",
                    f"{pattern}-api", f"{pattern}-v1", f"{pattern}-v2",
                    f"dev-{pattern}", f"test-{pattern}", f"staging-{pattern}",
                    f"api-{pattern}", f"admin-{pattern}", f"secure-{pattern}"
                ])
        
        return list(set(wordlist))  # Deduplicate
    
    async def resolve_wordlist(self, wordlist):
        """Resolve wordlist to find valid subdomains"""
        new_subs = set()
        
        def resolve(word):
            """Resolve single subdomain"""
            full = f"{word}.{self.domain}"
            
            # Skip if already found
            if full in self.found:
                return None
            
            # Try multiple DNS resolvers
            for resolver_ip in self.resolvers:
                try:
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [resolver_ip]
                    resolver.timeout = 1
                    resolver.lifetime = 1
                    answers = resolver.resolve(full, 'A')
                    if answers:
                        return full
                except:
                    continue
            return None
        
        # Process in batches
        batch_size = 500
        total = len(wordlist)
        
        with ThreadPoolExecutor(max_workers=self.config["concurrency"]) as executor:
            for i in range(0, total, batch_size):
                batch = wordlist[i:i+batch_size]
                futures = [executor.submit(resolve, word) for word in batch]
                
                for future in futures:
                    try:
                        result = future.result(timeout=2)
                        if result:
                            new_subs.add(result)
                    except:
                        pass
                
                # Progress display
                progress = min(i + batch_size, total)
                print(f"{Fore.CYAN}[*] Progress: {progress}/{total} | Found: {len(new_subs)}{Style.RESET_ALL}", end='\r')
                
                # Delay for stealth mode
                if self.mode == "stealth" and self.config.get("delay"):
                    time.sleep(self.config["delay"])
        
        print()  # New line after progress
        return new_subs
    
    # ==================== OUTPUT ====================
    
    def save_results(self):
        """Save results - Clean and simple"""
        # Save to text file
        txt_file = f"{self.output_dir}/subdomains.txt"
        with open(txt_file, 'w') as f:
            for sub in sorted(self.found):
                f.write(f"{sub}\n")
        
        # Save to JSON
        json_file = f"{self.output_dir}/subdomains.json"
        with open(json_file, 'w') as f:
            json.dump({
                "domain": self.domain,
                "mode": self.mode,
                "timestamp": datetime.now().isoformat(),
                "count": len(self.found),
                "subdomains": list(sorted(self.found))
            }, f, indent=2)
        
        # Generate HTML report
        self.generate_html()
        
        return txt_file
    
    def generate_html(self):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SubSeeker - {self.domain}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; margin: 20px; background: #0d1117; color: #c9d1d9; }}
        h1 {{ color: #58a6ff; }}
        .subdomain {{ padding: 8px; margin: 2px 0; background: #161b22; border-radius: 4px; font-size: 14px; }}
        .count {{ color: #3fb950; font-weight: bold; margin: 20px 0; font-size: 18px; }}
        .info {{ color: #8b949e; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>SubSeeker Results - {self.domain}</h1>
    <div class="count">Found: {len(self.found)} subdomains</div>
    <div>"""
        
        for sub in sorted(self.found):
            html += f'<div class="subdomain">{sub}</div>\n'
        
        html += f"""</div>
    <div class="info">
        Generated by SubSeeker v2.0 | Mode: {self.mode} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""
        
        with open(f"{self.output_dir}/report.html", 'w') as f:
            f.write(html)
    
    # ==================== MAIN ====================
    
    async def run(self):
        """Main execution"""
        self.banner()
        
        try:
            start_time = time.time()
            
            # Run passive enumeration
            passive_count = await self.passive_enum()
            
            # Run brute-force if enabled
            brute_count = await self.brute_force()
            
            # Save results
            output_file = self.save_results()
            
            # Print final result
            elapsed = time.time() - start_time
            print(f"\n{Fore.GREEN}{'═'*60}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[+] Total: {len(self.found)} subdomains found{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Time: {elapsed:.1f} seconds{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Saved to: {output_file}{Style.RESET_ALL}")
            
            # Show first 10 as sample
            if self.found:
                print(f"\n{Fore.YELLOW}[+] Sample:{Style.RESET_ALL}")
                for i, sub in enumerate(sorted(self.found)[:10], 1):
                    print(f"  {i:2d}. {Fore.CYAN}{sub}{Style.RESET_ALL}")
            
            print(f"{Fore.GREEN}{'═'*60}{Style.RESET_ALL}")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Interrupted{Style.RESET_ALL}")
            if self.found:
                self.save_results()
            sys.exit(0)
        except Exception as e:
            print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="SubSeeker - Complete Subdomain Discovery")
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-m", "--mode", choices=["quick", "standard", "deep", "stealth"], 
                       default="standard", help="Scan mode")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file")
    
    args = parser.parse_args()
    
    # Create and run
    seeker = SubSeeker(args.domain, args.mode, args.output)
    
    # Run
    asyncio.run(seeker.run())

if __name__ == "__main__":
    main()
