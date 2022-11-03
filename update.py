import pysftp
from urllib.parse import urlparse
import os
import pathlib
print(pathlib.Path().absolute())

class Sftp:
    def __init__(self, hostname, username, password, port=22):
        self.connection = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

    def connect(self):
        try:
            self.connection = pysftp.Connection(
                host=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port,
            )
        except Exception as err:
            raise Exception(err)
        finally:
            print(f"Connected to {self.hostname} as {self.username}.")

    def disconnect(self):
        self.connection.close()
        print(f"Disconnected from host {self.hostname}")

    def listdir(self, remote_path):
        for obj in self.connection.listdir(remote_path):
            yield obj

    def listdir_attr(self, remote_path):
        for attr in self.connection.listdir_attr(remote_path):
            yield attr

    def download(self, remote_path, target_local_path):
        try:
            print(
                f"downloading from {self.hostname} as {self.username} [(remote path : {remote_path});(local path: {target_local_path})]"
            )

            path, _ = os.path.split(target_local_path)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception as err:
                    raise Exception(err)

            self.connection.get(remote_path, target_local_path)
            print("download completed")

        except Exception as err:
            raise Exception(err)


class Update:
    def __init__(self):
        self.sftp = Sftp(hostname="10.0.11.99", username="updater", password="passord", port=22)
        self.sftp.connect()
        self.file_names = ["main.py", "requirements.txt", "versions.py", "homeassistant/config.py",
                           "homeassistant/connect.py", "homeassistant/entity_control.py", "homeassistant/power.py",
                           "homeassistant/stats.py", "other/gude.py"]

    def download(self):
        for path in self.file_names:
            self.sftp.download(remote_path=f"/home/updater/home_assistant_price_cap/{path}", target_local_path=f"{pathlib.Path().absolute()}/{path}")

        self.sftp.disconnect()

