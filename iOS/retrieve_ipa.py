import paramiko
import sys
import os
import re
import argparse

def ssh_command(ip, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username='root', password=password)
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    if error:
        print("Error:", error)
    client.close()
    return output

def sftp_get(ip, password, remote_path, local_path):
    transport = paramiko.Transport((ip, 22))
    transport.connect(username='root', password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get(remote_path, local_path)
    transport.close()

def main():
    parser = argparse.ArgumentParser(description="Extract an iOS app from an iPhone over SSH")
    parser.add_argument("IP", help="IP address of the iPhone")
    parser.add_argument("password", help="SSH password")
    parser.add_argument("app_name", help="Name of the iOS app")
    args = parser.parse_args()

    ip = args.IP
    password = args.password
    app_name = args.app_name

    # SSH commands
    app_path_command = f"cd /var/containers/Bundle/Application/ && find . -type d -name '*{app_name}*' | head -n 1"
    app_path_output = ssh_command(ip, password, app_path_command)
    match = re.search(r'(\./[0-9A-F\-]+)', app_path_output)
    if not match:
        print("Error: Couldn't find app path")
        sys.exit(1)

    app_uuid_path = match.group(1)[2:]
    app_path = "/var/containers/Bundle/Application/"
    payload_path = "/Payload"
    app_bundle_path = f"/{app_name}.app"
    ipa_name = f"/var/root/{app_name}.ipa"

    mkdir_payload_command = f"mkdir {app_path}{app_uuid_path}{payload_path}"
    ssh_command(ip, password, mkdir_payload_command)

    copy_app_command = f"cp -r {app_path}{app_uuid_path}{app_bundle_path} {app_path}{app_uuid_path}{payload_path}"
    ssh_command(ip, password, copy_app_command)

    zip_command = f"zip -r {ipa_name} {app_path}{app_uuid_path}{payload_path}"
    ssh_command(ip, password, zip_command)

    # SFTP commands
    cwd = os.getcwd()
    sftp_get(ip, password, ipa_name, cwd)

if __name__ == "__main__":
    main()
