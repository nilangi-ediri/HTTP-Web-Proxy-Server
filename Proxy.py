# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re
import time

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
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)

    fileExists = os.path.isfile(cacheLocation)
    
    #Defining flag to check if the cache file has been expired or not
    cache_expired = False
    
    #Defining the cache meta file path
    cache_control_file_location = cacheLocation + ".meta"
    
    #Checking if the cache file and the cache_control file exists
    if fileExists and os.path.exists(cache_control_file_location):
      #Opening the cache_control file in read mode
      with open (cache_control_file_location, "r") as cache_control_file:
        #Read the file and retrieve the calculated expiry time
        expiry_time = float(cache_control_file.read().strip())
      
      #Checking if current time is greater than expiry time (If expiry time has passed or not)
      if time.time() > expiry_time:
        cache_expired = True

    if cache_expired:
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
    
    clientSocket.sendall(cacheData)
  
    cacheFile.close()
    print ('Sent to the client:')
    print ('> ',cacheData)
  except:
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
      originServerSocket.connect((address, 80))
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
        #Using regx library, searching for the redirected location
        string_match = re.search(r'Location: (.*?)\r\n', response_string, re.IGNORECASE)
        if string_match:
          #Extracting the new location from the returned regx search result
          redirecting_location = string_match.group(1)
          print("Redirecting to: ",redirecting_location)
          #Updating the redirection flag to 1 as redirection is required
          redirection_flag = 1
          continue
      else:
        #Updating the redirection flag to 0 for normal behaviour without redirection
        redirection_flag = 0 
      # Send the response to the client
      clientSocket.sendall(response)

      #Extracting the headers from the response and saving them to a list
      response_headers = response.decode(errors='ignore').split('\r\n')
     
      #Creating a flag to determine if max-age is 0 or not
      cache_allowed = True
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
