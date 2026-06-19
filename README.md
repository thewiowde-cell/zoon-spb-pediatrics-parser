# Zoon Medical Clinics Scraper

A high-performance, automated Python web scraper built on top of Playwright (`cloakbrowser`). It is specifically designed to extract comprehensive contact, marketing, and reputation data for medical institutions from the Zoon directory.

## 🚀 Key Features

* **Dynamic Page Calculation:** Automatically calculates the exact number of catalog pages by extracting the total clinic count and dividing it by the number of active cards per page.
* **Hidden & Secondary Phone Extraction:** Extracts full phone numbers directly from dynamic container attributes (`data-number`), completely bypassing the need to click "Show Phone". It also captures additional phone numbers listed inside the business description.
* **Smart Data Normalization:**
  * Standardizes all extracted phone numbers into a unified format (`+7...`) to seamlessly eliminate duplicates.
  * Detects and decodes internal Zoon redirect paths (`/redirect/?to=...`) to retrieve clean, direct external website URLs.
* **Universal Social Media & Messenger Parsing:** Scans pages using robust signature tracking to harvest clean links for Telegram, VK, WhatsApp, and other networks while stripping away welcome text and tracking parameters (e.g., `?text=...`).
* **Bot-Detection Bypass & Resource Optimization:**
  * Intercepts network requests (`page.route`) to block heavy media files (images, videos, web fonts), resulting in massive speed gains and lower bandwidth usage.
  * Implements randomized human-like delays (`random.uniform`) to mimic real user behavior.
  * Restricts locator searches to the primary organization card, preventing cross-contamination from recommended listings or platform support numbers in the footer.

## 🛠️ Tech Stack

* **Programming Language:** Python 3
* **Automation Engine:** Playwright (`cloakbrowser`)
* **Data Processing & Cleaning:** Regular Expressions (`re`), `urllib.parse`
* **Output Format:** Structured JSON

## 📂 Extracted Data Structure

Each entry in the generated `result.json` file contains the following fields:
* `clinic name` — Cleaned clinic title, stripped of raw whitespaces.
* `clinic url` — Direct link to the clinic's profile page on Zoon.
* `clinic phone list` — A list of unique, verified phone numbers.
* `clinic address` — Physical street address of the facility.
* `clinic site` — Direct official website URL.
* `social network` — A key-value dictionary of discovered social handles or a `"not found"` status.
* `clinic rating` — The current platform rating of the clinic.
* `clinic reviews` — Total review and rating count.
