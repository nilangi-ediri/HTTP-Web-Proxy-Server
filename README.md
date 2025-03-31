# 🧠 Programming Assignment 1: HTTP Web Proxy (Python-Based)

Welcome to my submission for **Programming Assignment 1**, where I built a feature-rich **HTTP Web Proxy Server** using Python 🐍. This project demonstrates HTTP request handling, response forwarding, caching mechanisms, redirection logic, and more — following the standards outlined in **RFC 2616**.

---

## 📁 Files Included

- `Proxy.py` 🧱 – Core HTTP proxy implementation with caching and redirection
- `Proxy-bonus.py` ⚡ – Bonus version with support for ports, `Expires` header, and prefetching

---

## 🧩 Core Features (Implemented in Both Versions)

### 🔧 1. Server Initialization
- 🖧 Creates a TCP socket
- 🎯 Binds to the given IP and port
- 📡 Listens for incoming client (browser) requests

### 📥 2. Handling Client Requests
- 📝 Receives and parses HTTP requests
- 🔍 Extracts method, URI, and HTTP version
- ✂️ Cleans URI of protocols and unsafe path references (e.g., `/..`)
- 🌐 Separates hostname and requested resource

### 💾 3. Cache Check
- 🗂️ Constructs a path to the local cache
- 🕵️ Checks for the file and its freshness:
  - ✅ `Proxy.py`: Evaluates `max-age` only
  - ✅ `Proxy-bonus.py`: Considers both `max-age` and `Expires` headers
- ⚠️ Adds `Warning: 113 Heuristic Expiration` for cache older than 24 hours

### 🔄 4. Cache Miss or Expired Cache
- 🌍 Establishes connection to the origin server
- 📤 Forwards the request
- 📥 Retrieves the response from the server

### 🚦 5. Redirection Handling
- 🔁 Detects HTTP `301` and `302` responses
- 📍 Extracts the new `Location` from headers
- 🔄 Re-initiates request using updated URI
- ✅ Caches 301 if allowed, ❌ skips caching 302 unless explicitly permitted

### 💽 6. Cache Storage
- 🧠 Inspects `Cache-Control: max-age`
- 🏠 Saves response in local cache directory
- 🗃️ Creates a `.meta` file to store timestamp and `max-age` for validation

### 🧹 7. Finalization
- 📬 Sends response back to the client
- 🔒 Gracefully shuts down sockets and resets flags

---

## 🌟 Bonus Features in `Proxy-bonus.py`

### 🔢 Port Handling
- 🔧 Extracts non-default ports like `example.com:8080` from URLs
- 🔌 Connects to correct port on origin server

### ⏰ `Expires` Header Support
- 📅 Parses `Expires` date and validates cache freshness accordingly
- 🧠 Falls back to heuristics when no `max-age` or `Expires` is present

### 🚀 Prefetching Resources
- 🔗 Scans HTML content for linked resources (`href`, `src`)
- ⛓️ Sends preemptive GET requests to cache them for faster future access
- 💡 Improves performance by reducing subsequent load times

---

## 🗂️ Directory Structure

```
./<hostname>_<port>/<resource_path>
├── cached response file
└── .meta file (contains cache timestamp and max-age)
```

📝 If the resource path ends with `/`, a file named `default` is created.

---

## ⚙️ How to Run

### ▶️ Basic Proxy:
```bash
python3 Proxy.py <hostname> <port>
```

### 🚀 Bonus Proxy:
```bash
python3 Proxy-bonus.py <hostname> <port>
```

🔧 Set your browser or use `curl` to connect via the proxy using the provided IP and port.

---

## 📚 Learning Outcomes

- 🧠 Learned low-level **socket programming** with TCP in Python
- 🌐 Implemented end-to-end **HTTP request forwarding**
- 💾 Built a **file-based caching** system with freshness validation
- 🔁 Handled redirections using status codes `301` and `302`
- 🧠 Applied **RFC 2616** caching rules (`max-age`, `Expires`, heuristics)
- 🚀 Designed a **prefetching mechanism** to improve perceived performance
- 🔒 Improved security by sanitizing URIs (e.g., blocking `/..` traversal)

---

## ✅ Project Notes

- ✅ Supports only **HTTP GET** requests
- 🚫 Does **not support HTTPS**
- 🗃️ Stores cached files in a local directory structure mimicking request paths
- 📁 Each cached resource includes a `.meta` file for tracking expiration
- 📡 Prefetching is applied only to static resources detected in HTML (`href`, `src`)

---

## 🙌 Acknowledgements

👩‍🏫 **This project was completed as part of COMP SCI 7039 - Computer Networks & Applications.**

A huge thank you to **Dr. Cheryl Pope** and all course instructors for their support, guidance, and knowledge throughout the semester! 💙

---

👨‍💻 Developed by **Nilangi Edirisinghe**  
🎓 University of Adelaide | Semester 1, 2025
