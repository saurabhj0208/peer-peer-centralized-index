import socket
import threading

# global variable
rfc_set = set()
peer_set = set()


class RFCNode:
    def __init__(self, host_name, port_number, rfc_name, rfc_number):
        self.hostname = host_name
        self.port_no = port_number
        self.rfc_name = rfc_name
        self.rfc_no = rfc_number
        self.next = None


class RFCList:
    def __init__(self):
        self.head = None

    def append_node(self, host_name, rfc_name, rfc_number, port_number):
        global rfc_set
        self.node = RFCNode(host_name, port_number, rfc_name, rfc_number)
        self.node.next = self.head
        rfc_set.add(self.node)
        self.head = self.node

    def search_node(self, host_name, rfc_name, rfc_number):
        global rfc_set
        present = 0
        if len(rfc_set) is not 0:
            for node in rfc_set:
                if node.rfc_name == rfc_name and node.hostname == host_name and node.rfc_no == rfc_number:
                    present = 1
                    break
        return present

    def delete_node(self, host_name, port_number):
        global rfc_set
        prev = None
        listhead = self.head

        while listhead is not None:
            if not (listhead.port_no == port_number and listhead.hostname == host_name):
                prev = listhead
                listhead = listhead.next
            else:
                if listhead == self.head:
                    rfc_set.remove(listhead)
                    self.head = listhead.next
                    listhead = None
                    listhead = self.head
                else:
                    rfc_set.remove(listhead)
                    prev.next = listhead.next
                    listhead = None
                    listhead = prev.next


    def add_info(self, reply_list, requested_data):
        node = self.head
        while node is not None:
            if (node.rfc_name == requested_data[len(requested_data) - 1].lstrip('Title: ')) and (
                    node.rfc_no == requested_data[0].lstrip('LOOKUP RFC ').rstrip(' P2P-CI/1.0')):
                reply_list.append_node(node.hostname, node.rfc_name, node.rfc_no, node.port_no)
            node = node.next
        return reply_list
		
		
    def get_data(self, response):
        node = self.head
        while node is not None:
            response = response + "\r\n" + "RFC " + node.rfc_no + " " + node.rfc_name + " " + node.hostname + " " + node.port_no
            node = node.next
        return response


    def isEmpty(self):
        node = self.head
        if node is not None:
            return 0
        else:
            return 1


class PeerNode:
    def __init__(self, host_name, port_number):
        self.port_no = port_number
        self.hostname = host_name
        self.next = None


class PeerList:
    def __init__(self):
        self.head = None

    def append_node(self, host_name, port_number):
        global peer_set
        self.node = PeerNode(host_name, port_number)
        self.node.next = self.head
        peer_set.add(self.node)
        self.head = self.node

    def search_node(self, host_name, port_number):
        global peer_set
        present = 0
        if len(rfc_set) is not 0:
            for node in rfc_set:
                if node.port_no == port_number and node.hostname == host_name:
                    present = 1
                    break
        return present

    def delete_node(self, host_name, port_number):
        global peer_set
        prev = None
        listhead = self.head
        while listhead is not None:
            if listhead.hostname == host_name and listhead.port_no == port_number:
                if listhead is self.head:
                    peer_set.remove(listhead)
                    self.head = listhead.next
                    listhead = None
                else:
                    peer_set.remove(listhead)
                    prev.next = listhead.next
                    listhead = None
            else:
                prev = listhead
                listhead = listhead.next


rfc_record = RFCList()
peer_record = PeerList()


class PeerToServer(threading.Thread):
    def __init__(self, downloadSocket, downloadAddress):
        threading.Thread.__init__(self)
        self.connection = downloadSocket
        self.address = downloadAddress

    def run(self):
        while True:
            request_received = self.connection.recv(4096)
            request_received = request_received.decode("utf-8")
            if not request_received:
                break
            if request_received.startswith("EXIT"):
                break
            self.check_request(request_received)
            self.extract_data(request_received)
        self.remove_entry(request_received)

    def check_request(self, data):
        self.status_message = ""
        self.status_code = 0
        request_received = data.split('\r\n')

        if ((request_received[0].startswith("ADD") or
             request_received[0].startswith("LIST") or request_received[0].startswith("LOOKUP")) and (
                request_received[1].startswith("Host: ") and request_received[2].startswith("Port: "))):
            if "P2P-CI/1.0" in request_received[0]:
                self.status_message = "OK"
                self.status_code = 200
            else:
                self.status_message = "P2P-CI Version Not Supported"
                self.status_code = 505
        elif not request_received[0].startswith("LIST"):
            if not request_received[len(request_received) - 1].startswith("Title: "):
                self.status_message = "Bad Request"
                self.status_code = 400
            else:
                self.status_message = "OK"
                self.status_code = 200
        else:
            self.status_message = "Bad Request"
            self.status_code = 400

    def extract_data(self, data):
        if self.status_code != 200:
            reply = "P2P-CI/1.0 " + str(self.status_code) + " " + self.status_message
            reply = bytes(reply, 'utf-8')
            self.connection.send(reply)
        else:
            request_received = data.split('\r\n')
            if not (peer_record.search_node(request_received[1].lstrip('Host: '),
                                            request_received[2].lstrip('Port: '))):
                peer_record.append_node(request_received[1].lstrip('Host: '), request_received[2].lstrip('Port: '))
            if data.startswith('ADD'):
                self.add_rfc(data)
            self.send_response(data)

    def add_rfc(self, data):
        request_received = data.split('\r\n')
        if rfc_record.search_node(request_received[1].lstrip('Host: '),
                                  request_received[len(request_received) - 1].lstrip('Title: '),
                                  request_received[0].lstrip('ADD RFC ').rstrip(' P2P-CI/1.0')):
            return
        else:
            rfc_record.append_node(request_received[1].lstrip('Host: '),
                                   request_received[len(request_received) - 1].lstrip('Title: '),
                                   request_received[0].lstrip('ADD RFC ').rstrip(' P2P-CI/1.0'),
                                   request_received[2].lstrip('Port: '))

    def send_response(self, data):
        request_received = data.split('\r\n')
        reply = ""
        if request_received[0].startswith('LOOKUP'):
            response_list = RFCList()
            response_list = rfc_record.add_info(response_list, request_received)
            if not response_list.isEmpty():
                reply = reply + "P2P-CI/1.0 " + str(self.status_code) + " " + self.status_message
                reply = response_list.get_data(reply)
            else:
                self.status_message = "Not Found"
                self.status_code = 404
                reply = reply + "P2P-CI/1.0 " + str(self.status_code) + " " + self.status_message
        elif request_received[0].startswith('LIST'):
            reply = reply + "P2P-CI/1.0 " + str(self.status_code) + " " + self.status_message
            reply = rfc_record.get_data(reply)
        elif request_received[0].startswith('ADD'):
            reply = reply + "P2P-CI/1.0 " + str(self.status_code) + " " + self.status_message
            reply = reply + "\r\n" + request_received[0].lstrip('ADD ').rstrip('P2P-CI/1.0') + \
                    request_received[len(request_received) - 1].lstrip('Title: ') + request_received[
                        1].lstrip('Host:') + request_received[2].lstrip('Port:')
        reply = bytes(reply, 'utf-8')
        self.connection.send(reply)

    def remove_entry(self, data):
        remove = data.lstrip("EXIT: ")
        peer = self.address[0].lstrip("'").rstrip("'")
        remove_host = socket.getfqdn(peer)
        print("No longer connected to Host " + remove_host + " with Port number " + remove)
        peer_record.delete_node(remove_host, remove)
        rfc_record.delete_node(remove_host, remove)
        self.connection.close()


if __name__ == "__main__":
    print("Ready to connect!")
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('127.0.0.1', 7734))
    serverSocket.listen(15)
    while True:
        try:
            downloadSocket, downloadAddress = serverSocket.accept()
            server = PeerToServer(downloadSocket, downloadAddress)
        except:
            print("Connection error!\n")
        server.start()
