# Include the libraries for socket and system calls
from datetime import datetime
import socket
import sys
import os
import argparse
import re
import time
import calendar
from urllib.parse import urljoin

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the the server socket to a host and port
  serverSocket.bind((proxyHost, proxyPort))
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  #Assumes that the proxy server allows 3 unaccepted connections to queue
  serverSocket.listen(3) 
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

#Defining a redirection flag and location
redirection_flag = 0
redirecting_location = ''
#Creating a flag to keep cacheability in general. 
cache_allowed = True

# continuously accept connections
while True:
  if not redirection_flag:
    print ('Waiting for connection...')
    clientSocket = None

    # Accept connection from client and store in the clientSocket
    try:
      clientSocket, clientAddress = serverSocket.accept()
      #For debugging purposes, added clientAddress
      print ('Received a connection from ',clientAddress)
    except:
      print ('Failed to accept connection')
      sys.exit()

    # Get HTTP request from client
    # and store it in the variable: message_bytes
    try:
      message_bytes = clientSocket.recv(BUFFER_SIZE)
      message = message_bytes.decode('utf-8')
      print ('Received request:')
      print ('< ' + message)
    except:
      print("Failed to get HTTP request from client and store as message")

    # Extract the method, URI and version of the HTTP client request 
    requestParts = message.split()
    method = requestParts[0]
    URI = requestParts[1]
    version = requestParts[2]

    print ('Method:\t\t' + method)
    print ('URI:\t\t' + URI)
    print ('Version:\t' + version)
    print ('')
  
  else:
    #Directly using the redirected location as URI when redirection occurs
    URI = '/' + redirecting_location
      
  # Get the requested resource from URI
  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')

  # Split hostname from resource name
  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0] #hostname:portnumber
  resource = '/'
  
  #Adding the ability to handle origin server ports that are specified in the URL.
  hostname_port = resourceParts[0] #hostname:portnumber or hostname
  if ':' in hostname_port:
    hostname, port = hostname_port.split(':',1)
    port = int(port)
  else:
    hostname = hostname_port
    port = 80
    

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    #Added port number to cache location
    cacheLocation = f'./{hostname}_{port}{resource}'
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)

    fileExists = os.path.isfile(cacheLocation)
    
    #Defining response_is_fresh variable to indicate whether response has expired or not, according to RFC 2616 expiration calculations
    response_is_fresh = True
    
    #Defining the cache meta file path
    cache_control_file_location = cacheLocation + ".meta"
    
    #Checking if the cache file and the cache_control file exists
    if fileExists and os.path.exists(cache_control_file_location):
      #Opening the cache_control file in read mode
      with open (cache_control_file_location, "r") as cache_control_file:
        #Read the file and retrieve cached time and freshness lifetime (max_age) to perform expiration calculations
        meta_data_lines = cache_control_file.readlines()
        #Retrieving the time that the response was cached.
        cached_time = float(meta_data_lines[0].strip())
        #Retrieving max-age as freshness lifetime.
        freshness_lifetime = float(meta_data_lines[1].strip())
        #Calculating current age of the cached file by deducting current time from cached time.
        current_age = time.time()-cached_time
        # The calculation to determine if a response has expired, according to RFC 2616.
        if freshness_lifetime > current_age:
          response_is_fresh = True
          print("Cache file is fresh according to max-age derivative.")
        else:
          response_is_fresh = False
          print("Cache file has expired due to max-age derivative.")
    
    if fileExists:
      
      with open (cacheLocation,"r") as cacheFile:
        
        #Splitting the headers into individual ones.
        cache_headers = cacheFile.read().split('\n')
        #Created a flag to check if max_age header exists in cache.
        max_age_in_cache_file = False
        #Initializing expires date variable
        expires_date = None
        #Iterating through each header in the cache_headers list
        
        for header in cache_headers:
          #Checking if header is a Cache-Control header
          if header.lower().startswith('cache-control'):          
            #If max-age is found, extract the captured group (the digits) and convert it to an integer using int().
            if re.search(r'max-age=(\d+)',header,re.IGNORECASE):
              max_age_in_cache_file = True
          #Checking is header is a Expires header.
          if header.lower().startswith('expires'):
            #Split the Expires header at colon, extract the date value and store in expires date.
            _,expires_date = header.split(':',1)

        #Handling expires date - When max_age is not there, only Expires header exists.
        if max_age_in_cache_file == False and expires_date != None:
          expires_date_tuple = datetime.strptime(expires_date.strip(),"%a, %d %b %Y %H:%M:%S %Z")
          epoch_expires_date = float(calendar.timegm(expires_date_tuple.timetuple()))
          print("Epoch Expires Date and Time in Cache File: ",epoch_expires_date)
          
          if time.time() < epoch_expires_date:
            response_is_fresh = True 
            print("Cache file is fresh according to Expires header.")
          else:
            response_is_fresh = False
            print("Cache file has expired due to Expires header.")
          
      
    #If the cached file has expired
    if not response_is_fresh:
      print("Cache file exists but has expired")
      #Raising error so that the program goes to except block and contacts the origin server
      raise ValueError("Cache Expired")
  
    # Check wether the file is currently in the cache
    cacheFile = open(cacheLocation, "rb")
    cacheData = cacheFile.read()

    print ('Cache hit! Loading from cache file: ' + cacheLocation)
    # ProxyServer finds a cache hit
    # Send back response to client 
    # Used socket.sendall method as it ensures all data is sent unlike send method
    
    #RFC says: The cache MUST attach Warning 113 to any response whose age is more than 24 hours if such warning
    #has not already been added. Therefore, if current age is greater than 24 hours, the warning is added as a headre to the cacheData and sent to the client.
    
    if current_age > 60*60*24:
      print("Warning: 113 Heuristic Expiration")
      warning_header = f'\r\nWarning: 113 {hostname}:80 "Heuristic expiration"'
      cacheData = cacheData.replace(b'\r\n\r\n',warning_header.encode()+b'\r\n\r\n',1)
    clientSocket.sendall(cacheData)
  
    cacheFile.close()
    print ('Sent to the client:')
    print ('> ',cacheData)
  except Exception as e:
    print("_____________Exception__________:", e)
    # cache miss.  Get resource from origin server
    originServerSocket = None
    # Create a socket to connect to origin server
    # and store in originServerSocket
    originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      # Get the IP address for a hostname
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      originServerSocket.connect((address, port))
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers to send
      # and store in originServerRequestHeader and originServerRequest
      # originServerRequest is the first line in the request and
      # originServerRequestHeader is the second line in the request
      originServerRequest = f'{method} {resource} {version}'
      originServerRequestHeader = f'Host: {hostname}'

      # Construct the request to send to the origin server
      request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

      # Request the web resource from origin server
      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode())
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server
      response = originServerSocket.recv(BUFFER_SIZE)
      #Convert the binary response into string while ignoring decode errors.
      response_string = response.decode(errors='ignore')
      
      
      #Detecting if there are redirected web pages in the response
      if "301 moved permanently" in response_string.lower() or "302 found" in response_string.lower():
        print("Redirected Web Pages Detected")
        if "302 found" in response_string.lower():
          #According to RFC, generally 302 responses are not cached unless specified by cache-control header.
          cache_allowed = False
        #Using regx library, searching for the redirected location
        string_match = re.search(r'Location: (.*?)\r\n', response_string, re.IGNORECASE)
        if string_match:
          #Extracting the new location from the returned regx search result
          redirecting_location = string_match.group(1)
          print("Redirecting to: ",redirecting_location)
          #Updating the redirection flag to 1 as redirection is required
          redirection_flag = 1
          #Goes to back to the while loop to process new location
          continue
      else:
        #Updating the redirection flag to 0 for normal behaviour without redirection
        redirection_flag = 0 
      # Send the response to the client
      clientSocket.sendall(response)

      #Extracting the headers from the response and saving them to a list
      response_headers = response.decode(errors='ignore').split('\r\n')
     
      #Creating a variable to store max-age, which helps to determine whether or not to cache, depending on whether the max_age is 0 or not.
      max_age = None
      #Iterating through each header in the response_headers list
      for header in response_headers:
        #Checking if header is a cache-control header
        if header.lower().startswith('cache-control'):          
          #Searching for max-age value and extracting it
          max_age_found = re.search(r'max-age=(\d+)',header,re.IGNORECASE)
          #If max-age is found, extract the captured group (the digits) and convert it to an integer using int().
          if max_age_found:
            max_age = int(max_age_found.group(1))
            #If max_age = 0, then response is not cached.
            if max_age == 0:
              cache_allowed = False
              print("Caching is not allowed")
            else:
              #Caching is allowed if max_age is > 0.
              cache_allowed = True
              print("Max-age for caching is: ", max_age)
      
      if cache_allowed:
        # Create a new file in the cache for the requested file.
        cacheDir, file = os.path.split(cacheLocation)
        print ('cached directory ' + cacheDir)
        if not os.path.exists(cacheDir):
          os.makedirs(cacheDir)
          
        # Save origin server response in the cache file
        # ~~~~ INSERT CODE ~~~~
        with open (cacheLocation, 'wb') as cacheFile:
          cacheFile.write(response)
        # ~~~~ END CODE INSERT ~~~~
        print ('cache file closed')
        
        if max_age == None:
          #RFC says: If max_age does not appear in response, the cache MAY compute a freshness lifetime using a heuristic.
          #Therefore, max_age (freshness lifetime) is set to 2 days when max_age == None.
          max_age = 60*60*24*2
          
        with open (cache_control_file_location, "w") as cache_control_file:
          #Writing the date_value (current time) and freshness lifetime (max_age) to cache control file for expiration calculations according to RFC 2616.
          cache_control_file.write(f'{time.time()}\n{max_age}')
                       
      #Decoding response to string readable format from binary format, to pre-fetch the associated files of the main webpage
      html_content = response.decode(errors='ignore')
      #Search and extract the href and src links
      links = re.findall(r'(?:href|src)=["\'](.*?)["\']',html_content)
      
      for link in links:
        full_url = urljoin(f'http://{hostname}:{port}',link)
        print("------------------>Prefetching: ", full_url)
        try:
          full_url = re.sub('^(/?)http(s?)://', '', full_url, count=1)
          # Remove parent directory changes - security
          full_url = full_url.replace('/..', '')
          # Split hostname from resource name
          prefetch_resourceParts = full_url.split('/', 1)
          prefetch_hostname = prefetch_resourceParts[0]
          prefetch_resource = '/'     
          prefetch_hostname_port = prefetch_resourceParts[0] #hostname:portnumber or hostname
          if ':' in prefetch_hostname_port:
            prefetch_hostname, prefetch_port = prefetch_hostname_port.split(':',1)
            prefetch_port = int(prefetch_port)
          else:
            prefetch_hostname = prefetch_hostname_port
            prefetch_port = 80
    
          if len(prefetch_resourceParts) == 2:
            # Resource is absolute URI with hostname and resource
            prefetch_resource = prefetch_resource + prefetch_resourceParts[1]
          
          #Checks if Cache exists and creates Cache location for Prefetched files
          prefetch_cacheLocation = f'./{prefetch_hostname}_{prefetch_port}{prefetch_resource}'
          if prefetch_cacheLocation.endswith('/'):
              prefetch_cacheLocation = prefetch_cacheLocation + 'default'
          prefetch_fileExists = os.path.isfile(prefetch_cacheLocation)
         
          #Creating prefetch server socket 
          prefetch_ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          # Get the IP address for a prefetch_hostname via DNS server
          prefetch_address = socket.gethostbyname(prefetch_hostname)
          # Connect to the prefetch server
          prefetch_ServerSocket.connect((prefetch_address, prefetch_port))
          print ('Connected to Prefetch Server')
          
          #Repeating the same steps as fetching from origin server for prefetch server for GET request
          prefetch_ServerRequest = ''
          prefetch_ServerRequestHeader = ''
          
          prefetch_ServerRequest = f'GET {prefetch_resource} {version}'
          prefetch_ServerRequestHeader = f'Host: {prefetch_hostname}'

          # Construct the request to send to the prefetch server
          prefetch_request = prefetch_ServerRequest + '\r\n' + prefetch_ServerRequestHeader + '\r\n\r\n'
          prefetch_ServerSocket.sendall(prefetch_request.encode())
          
          print('Request sent to prefetch server\n')

          # Get the response from the prefetch server
          prefetch_response = prefetch_ServerSocket.recv(BUFFER_SIZE)
          #Convert the binary response into string while ignoring decode errors.
          prefetch_response_string = prefetch_response.decode(errors='ignore')
                    
          prefetch_response_headers = prefetch_response.decode(errors='ignore').split('\r\n')
          #Performing caching based on max-age for prefetched files as done previously.
          max_age = None
          prefetch_cache_allowed = True
          prefetch_cache_control_file_location = prefetch_cacheLocation + ".meta"
    
          for header in prefetch_response_headers:
            if header.lower().startswith('cache-control'):          
              max_age_found = re.search(r'max-age=(\d+)',header,re.IGNORECASE)
              if max_age_found:
                max_age = int(max_age_found.group(1))
                if max_age == 0:
                  perefetch_cache_allowed = False
                  print("Caching is not allowed")
                else:
                  prefetch_cache_allowed = True
                  print("Max-age for caching is: ", max_age)
          
          if prefetch_cache_allowed:
            cacheDir, file = os.path.split(prefetch_cacheLocation)
            print ('Prefetch cached directory ' + cacheDir)
            if not os.path.exists(cacheDir):
              os.makedirs(cacheDir)
            
            with open (prefetch_cacheLocation, 'wb') as cacheFile:
              cacheFile.write(prefetch_response)
            print ('Prefetched cache file closed')
            
            if max_age == None:
              max_age = 60*60*24*2
              
            with open (prefetch_cache_control_file_location, "w") as cache_control_file:
              cache_control_file.write(f'{time.time()}\n{max_age}')
          
        except Exception as e:
          print("Failed to prefetch: ", full_url, " Exception: ", e)
        
     # finished communicating with origin server - shutdown socket writes
      print ('origin response received. Closing sockets')
      originServerSocket.close()
       
      clientSocket.shutdown(socket.SHUT_WR)
      print ('client socket shutdown for writing')
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')

  #After handling one request from the user, giving permission to cache in general.
  cache_allowed = True