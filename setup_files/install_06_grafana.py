import os
import requests
from time import sleep
from requests.auth import HTTPBasicAuth
from .setup_utils import run_bash, log, get_random_string, get_setup_dir, get_conf_path

GRAFANA_INSTALL_LOG_FILE_NAME = 'install_06_grafana.log'


def install_grafana(
        architecture, 
        setup_scheme, 
        ip_address, 
        domain, 
        django_admin_email,
		django_admin_name,
		django_admin_pass
        ):
    """
    Install Grafana OSS (Open Source) Version based on the provided architecture and setup scheme.
    Download pages:
        https://grafana.com/grafana/download?edition=oss&platform=linux
        https://grafana.com/grafana/download?edition=oss&platform=arm
    """
    setup_dir = get_setup_dir()
    conf_dir = get_conf_path()
    grafana_files_dir = f'{setup_dir}/setup_files/tmp/grafana_install_files'
    new_admin_username = "grafana-admin-" + get_random_string(10)
    new_admin_password = get_random_string(20)
    host = domain if setup_scheme == "TLS_DOMAIN" else ip_address
    port = 3000

    installation_commands_amd64 = [
        # Ensure the temp directory exists and enter it
        f'mkdir -p {grafana_files_dir} && cd {grafana_files_dir} && '
        'sudo apt-get install -y adduser libfontconfig1 musl && '
        + 'wget https://dl.grafana.com/oss/release/grafana_10.4.2_amd64.deb && '
        + 'sudo dpkg -i grafana_10.4.2_amd64.deb && '
        + 'cd -',  # Return to install_dir
    ]

    installation_commands_arm64 = [
        # Ensure the temp directory exists and enter it
        f'mkdir -p {grafana_files_dir} && cd {grafana_files_dir} && '
        'sudo apt-get install -y adduser libfontconfig1 musl && '
        + 'wget https://dl.grafana.com/oss/release/grafana_10.4.2_arm64.deb && '
        + 'sudo dpkg -i grafana_10.4.2_arm64.deb && '
        + 'cd -',  # Return to install_dir
    ]

    if architecture in ['amd64', 'x86_64']:
        installation_commands = installation_commands_amd64
    elif architecture in ['arm64', 'aarch64']:
        installation_commands = installation_commands_arm64

    for command in installation_commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    commands = [
        'systemctl daemon-reload',
        'systemctl enable grafana-server',  # Configure grafana to start automatically
        # Start grafana-server by executing
        'systemctl start grafana-server',
    ]

    for command in commands:
        output = run_bash(command)
        log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    run_bash('echo sleeping for 5 seconds now to let grafana start???')
    sleep(5)
    try:
        with open(f'{conf_dir}/tmp.grafana.ini', 'r') as file:
            content = file.read()

        print("Replacing content with actual configuration.")
        log("Replacing content with actual configuration.")
        print(f"Using host: {host}")
        log(f"Using host: {host}")
        print(f"Using admin name: {django_admin_name}")
        log(f"Using admin name: {django_admin_name}")
        print(f"Using admin password: {django_admin_pass}")
        log(f"Using admin password: {django_admin_pass}")
        print(f"Using admin email: {django_admin_email}")
        log(f"Using admin email: {django_admin_email}")
            
        content = content.replace('DOMAIN_OR_IP', host)
        content = content.replace('ADMIN_USERNAME', django_admin_name)
        content = content.replace('ADMIN_PASSWORD', django_admin_pass)
        content = content.replace('ADMIN_EMAIL', django_admin_email)

        output_path = f'{setup_dir}/setup_files/tmp/grafana.ini'
        with open(output_path, 'w') as file:
            file.write(content)
        log(f"File successfully created at: {output_path}", GRAFANA_INSTALL_LOG_FILE_NAME)
    except Exception as e:
        log(f"Error during file handling: {e}", GRAFANA_INSTALL_LOG_FILE_NAME)
    
    run_bash('cp /etc/grafana/grafana.ini /etc/grafana/grafana.ini.backup')
    # output = run_bash('cp {setup_dir}/setup_files/tmp/grafana.ini /etc/grafana/grafana.ini')
    # log(output, GRAFANA_INSTALL_LOG_FILE_NAME)
    source_file = f'{setup_dir}/setup_files/tmp/grafana.ini'
    destination_file = '/etc/grafana/grafana.ini'

    log(f"Attempting to copy from {source_file} to {destination_file}", GRAFANA_INSTALL_LOG_FILE_NAME)
    if os.path.exists(source_file):
        command = f'cp {source_file} {destination_file}'
        output = run_bash(command)
        log(f"Copy operation result: {output}", GRAFANA_INSTALL_LOG_FILE_NAME)
    else:
        log("Source file grafana.ini does not exist.", GRAFANA_INSTALL_LOG_FILE_NAME)


    output = run_bash('systemctl restart grafana-server')
    log(output, GRAFANA_INSTALL_LOG_FILE_NAME)

    # TODO: REMOVE since not needed. Admin username and pw will be set in grafana.ini
    # change_grafana_password(port, admin_username, old_admin_password, new_admin_password)

    config_data = {
        'GRAFANA_HOST': host,
        'GRAFANA_PORT': port,
        'GRAFANA_ADMIN_USERNAME': new_admin_username,
        'GRAFANA_ADMIN_PASSWORD': new_admin_password,
    }
    log('Grafana installation done', GRAFANA_INSTALL_LOG_FILE_NAME)
    return config_data
