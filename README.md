# 🧠 Programming Assignment 1: HTTP Web Proxy (Python-Based)

Welcome to my submission for **Programming Assignment 1**, where I implemented a fully functional **HTTP Web Proxy Server** in Python. This proxy can handle caching, redirections, and even prefetching of linked resources — all aligned with **RFC 2616** standards.

---

## 📁 Files Included

- `Proxy.py` – Core implementation of a caching HTTP web proxy 🧱  
- `Proxy-bonus.py` – Extended version with extra features like port parsing, Expires header support, and resource prefetching ⚡

---

## ✨ Features Overview

### 🔹 Base Proxy (`Proxy.py`)
- 📡 Accepts and parses HTTP GET requests from clients.
- 🌐 Connects to the origin server and fetches the requested resource.
- 💾 Implements intelligent **caching** based on:
  - `Cache-Control: max-age`
  - Expiration tracking via `.meta` files (stores timestamp + max-age).
- 🔁 Handles **HTTP redirections** (301, 302):
  - Automatically follows the redirection using the `Location` header.
- ⚠️ Attaches `Warning: 113 Heuristic Expiration` if cache age > 24h.
- 🧹 Cleans up URIs by removing traversal patterns like `/..`.

### 🔸 Bonus Proxy (`Proxy-bonus.py`)
- 🔢 **Handles URLs with custom ports**, e.g. `example.com:8080`
- 📆 Supports both `Cache-Control` and `Expires` headers for freshness evaluation
- 🚀 **Prefetches** embedded content like:
  - Images (`src=...`), stylesheets, and hyperlinks (`href=...`)
  - Parses and sends additional GET requests to cache linked assets.
- 🛠️ Enhanced error handling and diagnostic print statements for better debugging.

---

## ⚙️ How to Run

```bash
python3 Proxy.py <proxy_host> <proxy_port>
# or
python3 Proxy-bonus.py <proxy_host> <proxy_port>
