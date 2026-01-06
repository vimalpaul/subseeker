SubSeeker

SubSeeker is a lightweight, single-file subdomain discovery tool designed for passive reconnaissance and controlled DNS enumeration. It aggregates results from multiple publicly available intelligence sources and optionally performs DNS-based enumeration to assist in asset discovery during authorized security testing.

This project is intended for use in approved environments such as bug bounty programs with a published policy, internal security assessments, and educational research.

Overview

SubSeeker focuses on simplicity, transparency, and portability. The tool is implemented as a single Python file, making it easy to audit, modify, and execute without complex setup or external services.

The primary goal of SubSeeker is to help security practitioners efficiently identify subdomains associated with a target domain using passive techniques, with optional controlled DNS resolution.

Key Capabilities

Single-file Python implementation

Passive subdomain enumeration using public intelligence sources

Optional DNS brute-force enumeration

Multiple execution modes for different reconnaissance needs

Clean command-line output

Generation of text, JSON, and HTML result files

No API keys or authentication required

Data Sources

SubSeeker performs passive enumeration using a combination of public datasets and services, including:

Certificate Transparency logs (crt.sh)

AlienVault OTX

VirusTotal public endpoints

HackerTarget

BufferOver DNS

ThreatCrowd

URLScan.io

Wayback Machine

AnubisDB

RapidDNS

CommonCrawl

Subdomain Center

DNS brute-force enumeration is performed only when explicitly enabled and uses standard DNS resolution techniques.

Execution Modes
Mode	Description
quick	Fast enumeration using a limited set of passive sources
standard	Balanced enumeration combining multiple sources (default)
deep	Extended enumeration using all available sources and larger wordlists
stealth	Reduced request rate and delayed execution to minimize noise
Installation

Clone the repository:

git clone https://github.com/vimalpaul/subseeker.git
cd subseeker


Install required Python dependencies:

pip3 install aiohttp dnspython colorama


An optional installation script is provided for convenience.

Usage

Run a standard enumeration:

python3 subseeker.py -d example.com


Run a deep enumeration:

python3 subseeker.py -d example.com -m deep


Run a quick enumeration:

python3 subseeker.py -d example.com -m quick


Specify a custom output directory:

python3 subseeker.py -d example.com -o results/

Output Files

Each execution generates a timestamped output directory containing:

subdomains.txt
A plain text list of discovered subdomains.

subdomains.json
Structured JSON output containing metadata and results.

report.html
A simple static HTML report for offline review.

Sample Output
SubSeeker v2.0 | STANDARD | example.com
------------------------------------------------------------
Passive Enumeration
crt.sh → 187
AlienVault → 67
VirusTotal → 92
Wayback → 89
RapidDNS → 56

Brute-force Enumeration
Using 4850 words
Found 28 new subdomains

------------------------------------------------------------
Total: 312 subdomains discovered
Execution Time: 42.3 seconds
Output Directory: subseeker_example.com_YYYYMMDD/

Legal and Ethical Notice

This tool must be used only on systems and domains for which you have explicit authorization.

Permitted use cases include:

Bug bounty programs with a published policy

Authorized penetration testing and security assessments

Controlled research and educational environments

Unauthorized scanning of systems may be illegal and unethical. The author assumes no responsibility for misuse of this software.

License

This project is licensed under the MIT License.
