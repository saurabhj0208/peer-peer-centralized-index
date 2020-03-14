import os.path
import sys
import threading
import datetime
import platform
import time
from socket import *

# global variables
close_connection = 0


class PeerToServer(threading.Thread):
    def __init__(self, port_number):
        threading.Thread.__init__(self)
        self.port_number = port_number
        self.host = gethostname()

    def run(self):
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect(('127.0.0.1', 7734))
        self.getuserpreference()

    def getuserpreference(self):
        print("Select the operation your want to perform from the following:\n 1. ADD\n 2. LIST\n 3. LOOKUP\n "
              "4. DOWNLOAD RFC\n 5. CLOSE CONNECTION \n")
        user_preference = input()
        if user_preference == '1':
            self.add_RFC()
        elif user_preference == '2':
            self.list_RFC()
        elif user_preference == '3':
            self.lookup_RFC()
        elif user_preference == '4':
            self.download_RFC()
        elif user_preference == '5':
            self.close_RFC()
        else:
            print("Invalid Request!\n")
            self.getuserpreference()

    def add_RFC(self):
        print("Enter a valid RFC number:")
        rfc_no = input()
        while True:
            if rfc_no.isnumeric():
                rfc_no = int(rfc_no)
                break
            else:
                print("Invalid! Enter a valid RFC number:")
                rfc_no = input()

        print("Enter a valid RFC title:")
        title = input()
        while True:
            if title != "" and title.isspace() is not True:
                break
            else:
                print("Invalid! Enter a valid RFC title:")
                title = input()

        number = rfc_no
        file_name = "RFC " + str(number) + ".txt"

        if file_name in os.listdir("."):
            response_message = self.request_handler("ADD", self.port_number, self.host, title, number)
            print("ADD request sent by peer:")
            print(response_message + "\n")
            response_message = bytes(response_message, 'utf-8')
            self.clientSocket.send(response_message)
            data = self.clientSocket.recv(4096)
            data = data.decode()
            print("Response received:")
            print(data + "\n")
        else:
            print("404 Not Found \n")
        self.getuserpreference()

    def list_RFC(self):
        response_message = self.list_request_handler(self.port_number, self.host)
        print("LIST request sent by peer:")
        print(response_message + "\n")
        response_message = bytes(response_message, 'utf-8')
        self.clientSocket.send(response_message)
        data = self.clientSocket.recv(4096)
        data = data.decode()
        print("Response received:")
        print(data + "\n")
        self.getuserpreference()

    def lookup_RFC(self):
        print("Enter a valid RFC number:")
        rfc_no = input()
        while True:
            if rfc_no.isnumeric():
                rfc_no = int(rfc_no)
                break
            else:
                print("Invalid! Enter a valid RFC number:")
                rfc_no = input()

        print("Enter a valid RFC title:")
        title = input()
        while True:
            if title != "" and title.isspace() is not True:
                break
            else:
                print("Invalid! Enter a valid RFC title:")
                title = input()

        number = rfc_no
        response_message = self.request_handler("LOOKUP", self.port_number, self.host, title, number)
        print("LOOKUP request sent by peer:")
        print(response_message + "\n")
        response_message = bytes(response_message, 'utf-8')
        self.clientSocket.send(response_message)
        data = self.clientSocket.recv(4096)
        data = data.decode()
        print("Response received:")
        print(data + "\n")
        self.getuserpreference()

    def download_RFC(self):
        print("Enter a valid RFC number:")
        rfc_no = input()
        while True:
            if rfc_no.isnumeric():
                rfc_no = int(rfc_no)
                break
            else:
                print("Invalid! Enter a valid RFC number:")
                rfc_no = input()

        print("Enter a valid RFC title:")
        title = input()
        while True:
            if title != "" and title.isspace() is not True:
                break
            else:
                print("Invalid! Enter a valid RFC title:")
                title = input()

        number = rfc_no
        response_message = self.request_handler("LOOKUP", self.port_number, self.host, title, number)
        response_message = bytes(response_message, 'utf-8')
        self.clientSocket.send(response_message)

        reply = self.clientSocket.recv(4096)
        reply = reply.decode()
        response_data = reply.split("\r\n")
        if "OK" not in response_data[0]:
            print(reply + "\r\n")
        else:
            peer_info = response_data[1].lstrip("RFC " + str(number) + " " + title)
            peer_port_number = peer_info.split(" ")[1]
            peer_host_name = gethostbyname(peer_info.split(" ")[0])
            peer_address = gethostbyaddr(peer_host_name)

            response_message = "GET RFC " + str(number) + " " + "P2P-CI/1.0\r\n" + "Host: " + str(
                peer_address) + "\r\n" + "OS: " + os.name + " " + platform.release() + "\r\n"
            response_message = bytes(response_message, 'utf-8')

            self.peerSocket = socket(AF_INET, SOCK_STREAM)
            self.peerSocket.connect((peer_host_name, int(peer_port_number)))

            print("Connection established!")
            self.peerSocket.send(response_message)

            end = False
            while not end:
                response_Data = self.peerSocket.recv(4096)
                response_Data = response_Data.decode()

                if response_Data[-13:] == "END OF FILE!!":
                    end = True
                print(response_Data + "\n")

                response_message = self.request_handler("ADD", self.port_number, self.host, title, number)
                RFC_file_name = "RFC " + str(number) + ".txt"
                with open(RFC_file_name, "ab") as f:
                    response_Data = bytes(response_Data, 'utf-8')
                    f.write(response_Data)

            print('DOWNLOADING COMPLETED!!\n')
            self.peerSocket.close()
            response_message = bytes(response_message, 'utf-8')
            self.clientSocket.send(response_message)
            response_received = self.clientSocket.recv(4096)
            response_received = response_received.decode()
            print(response_received)
        self.getuserpreference()

    def close_RFC(self):
        global close_connection
        response_message = "EXIT: " + str(self.port_number)
        print("Close connection request sent by peer:")
        print(response_message + "\n")
        response_message = bytes(response_message, 'utf-8')
        self.clientSocket.send(response_message)
        self.clientSocket.close()
        print("Connection Closed!")
        close_connection = 1
        return

    def request_handler(self, method, port_number, host, RFC_title, RFC_number):
        response_message = method + " " + "RFC " + str(
            RFC_number) + " " + "P2P-CI/1.0" + "\r\n" + "Host: " + host + "\r\n" + "Port: " + str(
            port_number) + "\r\n" + "Title: " + RFC_title
        return response_message

    def list_request_handler(self, port_number, host):
        response_message = "LIST" + " " + "P2P-CI/1.0" + "\r\n" + "Host: " + host + "\r\n" + "Port: " + str(
            port_number)
        return response_message


class p2pClient(threading.Thread):
    def __init__(self, downloadSocket, downloadAddress):
        threading.Thread.__init__(self)
        self.address = downloadAddress
        self.link = downloadSocket

    def run(self):
        connection_request = self.link.recv(4096)
        connection_request = connection_request.decode()
        self.status_code = 0
        self.status_message = ""
        request = connection_request.split('\r\n')
        if len(request) == 4 and ((request[0].startswith("GET")) and (
                request[1].startswith("Host: ") and request[2].startswith("OS: "))):
            if "P2P-CI/1.0" in request[0]:
                self.current_rfc = request[0].lstrip("GET ").rstrip(" P2P-CI/1.0") + ".txt"
                for file in os.listdir("."):
                    if file == self.current_rfc:
                        self.status_code = 200
                        self.status_message = "OK"
                        break
                    else:
                        self.status_code = 404
                        self.status_message = "Not found"
            else:
                self.status_code = 505
                self.status_message = "P2P-CI Version Not Supported"
        else:
            self.status_code = 400
            self.status_message = "Bad Request"

        current_path = os.name + " " + platform.release()
        current_time = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        message = "P2P-CI/1.0 " + str(
            self.status_code) + " " + self.status_message + "\r\n" + "Date: " + current_time + "\r\n" + "OS: " + current_path + "\r\n"
        if self.status_code == 200:
            response_data = self.buffer(self.current_rfc)
            latest_modification = str(time.ctime(os.path.getmtime(self.current_rfc)))
            content_length = str(os.stat(self.current_rfc).st_size)
            message = message + "Last-Modified: " + latest_modification + "\r\n" + "Content-Length: " + content_length + "\r\n" + "Content-Type: text/plain" + "\r\n"
            message = bytes(message, 'utf-8')
            self.link.send(message)
            for pkt in response_data:
                pkt = bytes(pkt, 'utf-8')
                self.link.send(pkt)

    def buffer(self, name):
        response_data = list()
        with open(name) as binary_file:
            content = binary_file.read()
            idx = 0
            size = sys.getsizeof(content)
            while idx <= size:
                binary_file.seek(idx)
                pkt_limit = binary_file.read(4096)
                response_data.append(pkt_limit)
                idx += 4096
            response_data.append("END OF FILE!!")
        return response_data


class PeerToPeer(threading.Thread):
    def __init__(self, port_number):
        threading.Thread.__init__(self)
        self.hostname = gethostname()
        self.serverName = gethostbyname(self.hostname)
        self.port_up = port_number

    def run(self):
        global close_connection
        requestPeerSocket = socket(AF_INET, SOCK_STREAM)
        requestPeerSocket.bind((self.serverName, self.port_up))
        requestPeerSocket.listen(15)
        while not close_connection:
            try:
                downloadSocket, downloadAddress = requestPeerSocket.accept()
                p2p_provider = p2pClient(downloadSocket, downloadAddress)
            except:
                print("Connection error!\n")
            p2p_provider.start()
        exit()


if __name__ == "__main__":
    while True:
        try:
            clientPort = input("Enter the port number for peer:  ")
            clientPort = int(clientPort)
            break
        except ValueError:
            print("Enter valid port number!")

    p2s = PeerToServer(clientPort)
    p2p = PeerToPeer(clientPort)
    p2s.start()
    p2p.start()
