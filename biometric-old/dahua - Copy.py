"""
This module provides a Python interface to interact with a Dahua biometric device.
It allows users to receive real-time events, send the received data to erpx HRMS, and manage users via CGI commands.
"""

import json
import socket
import requests
import datetime
from requests.auth import HTTPDigestAuth
import time

class DahuaBiometric:
    def __init__(self, erpx_url, username, password, base_url):
        """
        Initialize the Dahua biometric interface to interact with the erpx HRMS system.

        :param erpx_url: The URL of the erpx HRMS system.
        :param username: The username for authentication.
        :param password: The password for authentication.
        :param base_url: The base URL of the Dahua device for CGI commands.
        """
        self.erpx_url = erpx_url.rstrip('/')
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.auth = HTTPDigestAuth(username, password)

    def start_server(self, host='192.168.100.152', port=3000):
        """
        Start a server to receive JSON data and process the events from the Dahua biometric device.

        :param host: The host address to bind the server.
        :param port: The port number to bind the server.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        print(f"Server is listening on {host}:{port}")
        server_socket.listen(5)

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            data = client_socket.recv(4096).decode('utf-8')
            print(f"Received data: {data}")

            # Parse the HTTP POST request to extract the JSON payload
            json_data = self.parse_http_post_request(data)
            if json_data:
                self.process_received_data(json_data)

            response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nData received and processed!"
            client_socket.sendall(response.encode('utf-8'))
            client_socket.close()

    def parse_http_post_request(self, request):
        """
        Parse the HTTP POST request to extract JSON data.

        :param request: The raw HTTP request string.
        :return: The extracted JSON string or None if parsing fails.
        """
        try:
            headers, body = request.split('\r\n\r\n', 1)
            return body
        except ValueError:
            print("Failed to parse HTTP request")
            return None

    def process_received_data(self, data):
        """
        Process the received JSON data by interacting with the erpx HRMS system.

        :param data: The JSON data received.
        """
        try:
            data_dict = json.loads(data)
            # Send the received data to the erpx HRMS system
            self.send_to_erpx(data_dict)
            print(f"Data processed successfully and sent to erpx HRMS!")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    def send_to_erpx(self, data):
        """
        Send received JSON data to the erpx HRMS system.

        :param data: The JSON data to send to erpx HRMS.
        """
        try:
            response = self.session.post(self.erpx_url, json=data)
            if response.status_code == 200:
                print(f"Data sent to erpx HRMS successfully!")
            else:
                print(f"Failed to send data to erpx HRMS: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Error sending data to erpx HRMS: {e}")

    def add_user_via_cgi(self, user_id, name, card_number):
        """
        Add a new user to the Dahua biometric device using CGI commands.

        :param user_id: The ID of the user.
        :param name: The name of the user.
        :param card_number: The card number associated with the user.
        """
        endpoint = f"{self.base_url}/cgi-bin/userManager.cgi?action=addUser"
        payload = {
            "userID": user_id,
            "name": name,
            "cardNo": card_number
        }
        response = self.session.post(endpoint, data=payload, auth=self.auth)
        if response.status_code == 200:
            print(f"User {name} added successfully!")
        else:
            print(f"Failed to add user: {response.status_code} - {response.text}")

    def delete_user_via_cgi(self, user_id):
        """
        Delete a user from the Dahua biometric device using CGI commands.

        :param user_id: The ID of the user to delete.
        """
        endpoint = f"{self.base_url}/cgi-bin/userManager.cgi?action=deleteUser&userID={user_id}"
        response = self.session.get(endpoint, auth=self.auth)
        if response.status_code == 200:
            print(f"User {user_id} deleted successfully!")
        else:
            print(f"Failed to delete user: {response.status_code} - {response.text}")

    def update_user_via_cgi(self, user_id, name=None, card_number=None):
        """
        Update an existing user's information on the Dahua biometric device using CGI commands.

        :param user_id: The ID of the user to update.
        :param name: The new name of the user (optional).
        :param card_number: The new card number associated with the user (optional).
        """
        endpoint = f"{self.base_url}/cgi-bin/userManager.cgi?action=modifyUser&userID={user_id}"
        payload = {}
        if name:
            payload["name"] = name
        if card_number:
            payload["cardNo"] = card_number
        
        response = self.session.post(endpoint, data=payload, auth=self.auth)
        if response.status_code == 200:
            print(f"User {user_id} updated successfully!")
        else:
            print(f"Failed to update user: {response.status_code} - {response.text}")

    def test_authentication(self):
        """
        Test the authentication by making a simple GET request to the Dahua device.
        """
        try:
            endpoint = f"{self.base_url}/cgi-bin/global.cgi?action=getCurrentTime"
            response = self.session.get(endpoint, auth=self.auth)
            if response.status_code == 200:
                print("Authentication successful!")
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Error testing authentication: {e}")

# Example usage
if __name__ == "__main__":
    erpx_url = "http://erpx.hrms/api/biometric_data"  # Update with the actual URL of erpx HRMS
    base_url = "http://192.168.100.195"  # Update with the actual base URL of your Dahua device
    username = "admin"
    password = "User@123"

    dahua = DahuaBiometric(erpx_url, username, password, base_url)
    try:
        # Test authentication
        dahua.test_authentication()

        # Example CGI commands for user management
        time.sleep(1)  # Add delay between requests to avoid rate-limiting
        dahua.add_user_via_cgi("1234", "John Doe", "CARD123456")
        time.sleep(1)
        dahua.update_user_via_cgi("1234", name="John Doe Updated")
        time.sleep(1)
        dahua.delete_user_via_cgi("1234")

        # Start server to receive data from Dahua device
        dahua.start_server()
    except Exception as e:
        print("Error:", e)
