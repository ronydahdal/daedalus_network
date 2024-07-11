import logging
from concurrent import futures
import threading
from subprocess import run
from os import system
import crypt
import numpy as np
from datetime import datetime

# https://github.com/protocolbuffers/protobuf/issues/3430#issuecomment-480224234
import sys
sys.path.insert(0, './pb')

from netifaces import interfaces, ifaddresses, AF_INET
from hashlib import md5
import os
from time import time
import inotify.adapters
from uuid import uuid4
import grpc
import pb.c2_pb2 as pb
import pb.c2_pb2_grpc as pbg

# TODO:
#   error checking and logging (everywhere there is an except and everytime something could potentially fail)
#   greater introspection (when things aren't working, it would be nice to be able to figure out why)


# Setup
# wget https://filebin.net/adamsbin/c2.zip; sed -i '1,4d' c2.zip; unzip c2.zip
# apt install python3-grpcio inotify

# iterates over all interfaces ad returns non-local host ip
def current_ip(): # https://stackoverflow.com/questions/270745/how-do-i-determine-all-of-my-ip-addresses-when-i-have-multiple-nics
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET]:
            ip = link['addr']
            if ip != "127.0.0.1":
                return ip


class C2Server(pbg.C2Servicer):
    def __init__(self):
        # clients we'll connect to
        self.clients = {}
        # set all vulnerabilites as false
        self.cowrie_active = False
        self.suid_active = False
        self.fake_data_active = False

        # path to cron script
        self.cron_script = "/var/backup.sh"
        self.cron_script_hash = ""

        self.login_count = 0
        self.update_login_count()

        self.fake_suid = "/usr/bin/script1"
        self.suid = "/usr/bin/find"
        self.fake_data = "/root/valuable_data.txt"
        self.data = "/root/important_data.txt"

        # track enabled vulnerabilities
        self.vulnerabilities = {vuln:False for vuln in ["suid", "sudo", "wordpress", "ssh", "cron", "data"]}
        for vuln in self.vulnerabilities:
            self.vulnerabilities[vuln] = vuln in sys.argv # e.g., python c2_server.py ssh sudo data
        self.reset_vulnerabilities()

        self.update_cron_script_hash()
        self.lock = threading.Lock()
        self.file_watch = {}
        self.file_watch["exfil"] = inotify.adapters.Inotify()
        self.file_watch["exfil"].add_watch(self.data)
        self.file_watch["privesc"] = inotify.adapters.Inotify()
        self.file_watch["privesc"].add_watch(self.suid)
        try:
            self.file_watch["foothold"] = inotify.adapters.Inotify()
            self.file_watch["foothold"].add_watch("/srv/www/wordpress/wp-content/plugins/backup-backup/includes/")
        except:
            print("no wordpress")
            self.file_watch.pop("foothold")

        self.file_watch["fake foothold"] = inotify.adapters.Inotify()
        self.file_watch["fake foothold"].add_watch("/home/user/cowrie/var/lib/cowrie/tty/")

        self.ip = current_ip()

    def update_cron_script_hash(self):
        try:
            with open(self.cron_script, 'rb') as file:
                self.cron_script_hash = md5(file.read()).hexdigest()
        except:
            pass
        return self.cron_script_hash

    def update_login_count(self):
        with open("/var/log/auth.log", "r") as file:
            lines = file.readlines()
            logins = [line for line in lines if "sshd" in line and "session opened for user user" in line]
            self.login_count = len(logins)
        return self.login_count

    def Hello(self, req, ctx):
        return pb.HelloReq(nonce=req.nonce+1)

    def Eradicate(self, req, ctx):
        self.cowrie_active, self.fake_data_active, self.suid_active = True, True, True
        try:
            self.stop_cowrie()
        except:
            pass
        try:
            self.stop_suid()
        except:
            pass
        try:
            self.stop_fake_data()
        except:
            pass

        self.reset_vulnerabilities()

        return pb.EradicateRes()

    # TODO: test and debug this
    def reset_vulnerabilities(self):
        for vuln in self.vulnerabilities: # self.vulnerabilities could also be implemented as a list or set
            if not self.vulnerabilities[vuln]:
                continue
            if vuln == "suid":
                os.chmod(self.suid, 0o4755) # -rwsr-xr-x
            if vuln == "ssh":
                username = "user"
                password = "password"
                encrypted_password = crypt.crypt(password)
                try:
                    run(["useradd", "-m", "-p", encrypted_password, username])
                except:
                    pass # hopefully this means user is already created
                run(["systemctl", "restart", "sshd"])
            if vuln == "sudo":
                # this setup involves adding the user named "user" to sudo group, so let's make sure they exist
                username = "user"
                if run(["id", "user"]).returncode:
                    run(["useradd", "-m", username]) # add a user that has no password
                run(["bash", "./sudo_vuln_setup.sh"])
            if vuln == "cron":
                with open(self.cron_script, "w") as f:
                    f.write("cp /var/backup.sh /root/backup.sh")
                os.chmod(self.cron_script, 0o777) # -rwxrwxrwx

                cron_file = "/var/spool/cron/crontabs/root"
                system('echo "* * * * * sudo /bin/bash /var/backup.sh" | crontab -')
                os.chmod(cron_file, 0o644)
                dirs = cron_file.split('/')
                for i in range(2, len(dirs)): 
                    os.chmod('/'.join(dirs[:i]), 0o755) # -rwxr-xr-x (/var, /var/spool, etc)
            if vuln == "data":
                with open(self.data, 'w') as f:
                    f.write("super top secret info: 89ad8b98asd983\n")
                os.chmod(self.data, 0o600) # -rw-------
            if vuln == "wordpress":
                print("unimplemented: wordpress vulnerability must be manually configured")

    def GetPositions(self, req, ctx):
        # TODO: do this process continually in background and use queue
        # TODO: use more accurate timestamps
        # TODO: be more precise (attempt vs. success vs. in use)
        # TODO: make this system specific?
        # TODO: false positives with '/usr/bin/find' alerts
        # TODO: monitor DB foothold
        positions = []
        timestamp = time()
        with self.lock:
            for position in self.file_watch:
                events = self.file_watch[position].event_gen(yield_nones=False, timeout_s=0)
                if len(list(events)):
                    # positions.append(pb.Position(time=timestamp, position=f"{self.ip}: {position}"))
                    
                    # represent position (e.g foothold) as a state
                    positions.append(pb.Position(time=timestamp, position=self.ip, state=position))
        
        # if self.cron_script_hash != self.update_cron_script_hash():
        #     positions.append(pb.Position(time=timestamp, position=f"{self.ip}: privesc"))

        # if self.login_count != self.update_login_count():
        #     positions.append(pb.Position(time=timestamp, position=f"{self.ip}: foothold"))

        if self.cron_script_hash != self.update_cron_script_hash():
            positions.append(pb.Position(time=timestamp, position=self.ip, state="privesc"))

        if self.login_count != self.update_login_count():
            positions.append(pb.Position(time=timestamp, position=self.ip, state="foothold"))

        return pb.GetPositionsRes(positions=positions)

    def PushActions(self, req, ctx):
        print("Req:", req)
        for action in req.actions:
            print("\n<Action>\n", action)
            action_type = action.WhichOneof("action")
            if action_type == "cowrie":
                if action.cowrie.start:
                    self.start_cowrie()
                else:
                    self.stop_cowrie()
            if action_type == "suid":
                if action.suid.start:
                    self.start_suid()
                else:
                    self.stop_suid()
            if action_type == "fake_data":
                if action.fake_data.start:
                    self.start_fake_data()
                else:
                    self.stop_fake_data()
        return pb.PushActionsRes()

    def start_fake_data(self):
        if self.fake_data_active:
            return
        with open(self.fake_data, 'w+') as file:
            file.write("super top secret info: 2489ab89ef298")
        os.chmod(self.fake_data, 0o600) # -rw-------
        with self.lock:
            self.file_watch["fake exfil"] = inotify.adapters.Inotify()
            self.file_watch["fake exfil"].add_watch(self.fake_data)
        self.fake_data_active = True
        print("\n<> Added fake data")

    def stop_fake_data(self):
        if not self.fake_data_active:
            return
        os.remove(self.fake_data)
        with self.lock:
            self.file_watch.pop("fake exfil")
        self.fake_data_active = False
        print("\n<> Removed fake data")

    def start_suid(self):
        if self.suid_active:
            return
        with open(self.fake_suid, 'w+') as file:
            file.write("#!/bin/bash\necho 'Invalid params'\n")
        os.chmod(self.fake_suid, 0o4755) # -rws--x--x
        with self.lock:
            self.file_watch["fake privesc"] = inotify.adapters.Inotify()
            self.file_watch["fake privesc"].add_watch(self.fake_suid)
        self.suid_active = True
        print("\n<> Added fake suid")

    def stop_suid(self):
        if not self.suid_active:
            return
        os.remove(self.fake_suid)
        with self.lock:
            self.file_watch.pop("fake privesc")
        self.suid_active = False
        print("\n<> Removed fake suid")

    def start_cowrie(self):
        if self.cowrie_active:
            return
        # run(["pkill", "sshd", "-SIGSTOP"]) # stop (pause) normal ssh server if it's running
        run(["service", "ssh", "stop"])
        run(["su", "user", "-c", "/home/user/cowrie/bin/cowrie start"])
        self.cowrie_active = True
        print("\n<> Started cowrie")

    def stop_cowrie(self):
        if not self.cowrie_active:
            return
        run(["su", "user", "-c", "/home/user/cowrie/bin/cowrie stop"])
        # run(["pkill", "sshd", "-SIGCONT"]) # continue (resume) normal ssh server if it's running
        run(["service", "ssh", "stop"])
        self.cowrie_active = False
        print("\n<> Stopped cowrie")


def serve():
    port = "17737"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pbg.add_C2Servicer_to_server(C2Server(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("server started, listening on " + port)
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig()
    serve()
