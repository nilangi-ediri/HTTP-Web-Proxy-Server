# 🧠 Programming Assignment 1: HTTP Web Proxy (Python-Based)

Welcome to my submission for **Programming Assignment 1**, where I implemented a fully functional **HTTP Web Proxy Server** in Python. This proxy can handle caching, redirections, and even prefetching of linked resources — all aligned with **RFC 2616** standards.

---

## 📁 Files Included

- `Proxy.py` – Core implementation of a caching HTTP web proxy 🧱  
- `Proxy-bonus.py` – Extended version with extra features like port parsing, Expires header support, and resource prefetching ⚡

---

## 🧩 Core Functionality (Common to Both Versions)

### 1. Server Initialization
- Sets up a TCP socket that listens for client (browser) connections on a specified host and port.

### 2. Handling Client Requests
- Receives the HTTP request.
- Parses the method, URI, and HTTP version.
- Strips protocol and parent directory changes from the URI.
- Extracts hostname and resource path.

### 3. Cache Check
- Generates a local file path to check for cached response.
- If found, it checks whether the response is still fresh:
  - In `Proxy.py`: only `max-age` is used.
  - In `Proxy-bonus.py`: both `max-age` and `Expires` headers are considered.
- If fresh, returns cached response to the client.
- Adds warning `113 Heuristic Expiration` if cache age > 24 hours.

### 4. Cache Miss or Expired Cache
- Connects to the origin server.
- Sends the original request.
- Receives the response.

### 5. Redirection Handling
- Detects `301 Moved Permanently` or `302 Found`.
- Extracts the `Location` header.
- Updates URI and restarts request process.
- In the implementation:
  - **301 responses** are cached if allowed by the cache-control header.
  - **302 responses** are *not* cached by default, unless explicitly allowed.

### 6. Cache Storage
- Checks if `Cache-Control: max-age` is available.
- If caching is allowed:
  - Stores the response in a file.
  - Writes a `.meta` file containing cache timestamp and `max-age`.

### 7. Finalize
- Sends the response to the client.
- Closes sockets and resets flags for the next connection.

---

## 🔧 Additional Features in `Proxy-bonus.py`

### 1. Port Handling
- Supports URLs with non-default ports like `example.com:8080`.

### 2. `Expires` Header Support
- Parses and validates cached responses using the `Expires` header.

### 3. Prefetching
- Parses HTML content to find `href` and `src` attributes.
- Sends requests for these linked resources.
- Caches their responses for future use.

---

## 📂 Directory Structure

```
./<hostname>_<port>/<resource_path>
├── cached response file
└── .meta file (contains cache timestamp and max-age)
```

If the resource path ends with a `/`, a `default` file is created.

---

## ⚙️ How to Run

### Basic Proxy:
```bash
python3 Proxy.py <hostname> <port>
```

### Bonus Proxy:
```bash
python3 Proxy-bonus.py <hostname> <port>
```

Set your browser or curl to use `localhost:<port>` as HTTP proxy.

---

## 📚 Learning Outcomes

- Implemented a full-fledged HTTP proxy server with **socket programming** in Python.
- Learned to parse and forward HTTP requests and handle server responses.
- Gained practical insights into **HTTP caching mechanisms** and the usage of:
  - `max-age`
  - `Expires`
  - Heuristic freshness validation
- Understood how to work with **HTTP status codes**, especially `301`, `302`, and `200`.
- Explored **resource prefetching** strategies for performance enhancement.

---

## ✅ Notes

- This proxy server supports **only HTTP GET** requests.
- HTTPS is **not** supported in this assignment.
- Cached responses are stored in a directory structure mimicking the request URL path.
- A `.meta` file is created per cached resource for freshness calculations.
- Prefetching works only for statically linked resources (found in `href` and `src`).

---

## 🙌 Credits

Developed by **Nilangi Edirisinghe**  
University of Adelaide | COMP SCI - Programming Assignment 1  
📅 Semester 1, 2025
