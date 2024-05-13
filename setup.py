"""
This script automates the installation and setup of the Biomed IoT platform,
including pre-checks, user input for configuration, installation of necessary
packages (Docker, Node-RED, InfluxDB, Grafana, Mosquitto, PostgreSQL, Django,
Gunicorn, and NGINX), and final configuration.

The setup_files subfolder includes additional setup scripts that the main setup
process calls. These scripts are responsible for installing various components
of Biomed IoT.

The setup_files/config subfolder holds configuration files for the various
services being installed.

The setup_files/setup_logs subfolder stores log files generated by both this main
setup script and the individual installation scripts.
"""

import os
import sys
import socket
import platform
import re
import time
from getpass import getpass
from setup_files.setup_utils import (
    run_bash,
    get_linux_user,
    get_setup_dir,
    log,
    set_setup_dir_rights,
    get_random_string
)
from setup_files.write_config_file import generate_empty_config_data, write_config_file
from setup_files.install_01_basic_apt_packages import install_basic_apt_packages
from setup_files.install_02_security_packages import install_security_packages
from setup_files.install_03_docker import install_docker
from setup_files.install_04_nodered import install_nodered
from setup_files.install_05_influxdb import install_influxdb
from setup_files.install_06_grafana import install_grafana
from setup_files.install_07_mosquitto import install_mosquitto
from setup_files.install_08_postgres import install_postgres
from setup_files.install_09_django import install_django
from setup_files.install_10_gunicorn import install_gunicorn
from setup_files.install_11_nginx import install_nginx


def print_logo_header():
    logo_header = """
 ______   _                           _    _      _______ 
(____  \ (_)                         | |  | |    (_______)
 ____)  ) _   ___   ____   _____   __| |  | |  ___   _    
|  __  ( | | / _ \ |    \ | ___ | / _  |  | | / _ \ | |   
| |__)  )| || |_| || | | || ____|( (_| |  | || |_| || |   
|______/ |_| \___/ |_|_|_||_____) \____|  |_| \___/ |_|   

<<<----      Setup of Biomed IoT      --->>>
<<<----       Version v1.0        --->>>
"""
    print('\n' + logo_header + '\n')
    log(logo_header + '\n')


def get_and_check_cpu_architecture():
    """Check system's CPU architecture."""
    supported_architectures = ['amd64', 'x86_64', 'arm64', 'aarch64']
    cpu_architecture = platform.machine()
    if cpu_architecture.lower() not in supported_architectures:
        msg = (
            f'Your system architecture "{cpu_architecture}" is not '
            'supported. Only "amd64", "x86_64", "arm64"or  "aarch64" is '
            'supported.\nExiting Setup'
        )
        print(msg)
        log(msg)
        sys.exit(1)

    return cpu_architecture


def is_running_with_sudo_or_exit_setup():
    """Ensure the script is run with sudo."""
    if os.geteuid() != 0:
        msg = 'This script must be run with sudo. Exiting setup'
        print(msg)
        log(msg)
        sys.exit(1)


def get_setup_scheme():
    """Determine the setup scheme based on user input."""
    print(
        '\nTLS (Transport Layer Security) encrypts the data between your '
        'server and its users and gateways (using https), ensuring the data '
        'remains private and secure. It is highly recommended for most '
        "installations.\nHowever, if you're setting up a development "
        "environment, running tests or you're in a controlled and isolated "
        "environment where encryption isn't a priority and even have limited "
        'system resources (older Raspberry Pi), you might consider running '
        'without TLS (using http).\n'
    )
    chosen_scheme = 'NO_TLS'  # Default scheme without TLS encryption
    answer = (
        input('Shall your Biomed IoT use TLS encryption for MQTT messages? ' '(Y/n, default is n): ').strip().lower()
    )
    if answer == 'y':
        chosen_scheme = 'TLS_NO_DOMAIN'
        # Ask about the domain
        domain_answer = (
            input('Is the server using a domain name like ' "'example.com')? (y/N, default is N): ").strip().lower()
        )
        if domain_answer == 'y':
            chosen_scheme = 'TLS_DOMAIN'

    log('Chosen setup scheme: ' + chosen_scheme)
    return chosen_scheme


def confirm_proceed(question_to_ask):
    """Ask the user to confirm to proceed."""
    while True:
        user_answer = input(f'{question_to_ask} (y/n): ').strip().lower()

        if user_answer == 'y':
            break  # Exit the loop and proceed
        elif user_answer == 'n':
            msg = 'You declined to proceed. Exiting setup.'
            print(msg)
            log(msg)
            sys.exit(1)  # Exit the script with an error code
        else:
            print("Invalid response. Please enter 'Y' or 'N'.")


def get_confirmed_text_input(input_prompt, hidden_input=False):
    """
    Example usage:
        password = get_confirmed_text_input("Enter your password", hidden_input=True)
    """
    while True:
        print()
        if hidden_input:
            input_text = getpass(f'{input_prompt}: ')
            confirmation = getpass('Please repeat your entry: ')
        else:
            input_text = input(f'{input_prompt}: ').strip()
            confirmation = input('Please repeat your entry: ').strip()

        if not input_text:
            print('Nothing entered. Please try again.')
        elif input_text == confirmation:
            return input_text
        else:
            print('Your inputs do not match. Please try again.')


def prompt_for_password(required_length=12):
    # unused
    """
    Parameters:
    - required_length (int): The minimum required length of the password.
    Returns:
    - str: The user-provided password that meets the criteria.
    """
    password_pattern = re.compile(
        r"""
    (?=.*[A-Z])     # at least one uppercase letter
    (?=.*[a-z])     # at least one lowercase letter
    (?=.*\d)        # at least one digit
    (?=.*[!@#$%%&*()_+\-=\[\]{}|;:'"<>,.?/]) # at least one special character
    .{%d,}          # at least required_length characters
    """
        % required_length,
        re.VERBOSE,
    )

    while True:
        password = get_confirmed_text_input(
            'Enter and remember a safe '
            f'password (min length {required_length}) for your Biomed IoT admin '
            'user\nIt must contain at least one uppercase letter, one '
            'lowercase letter, one digit and one special character from '
            '!@#$%&*()_+-=[]}{|;:<>/?,',
            hidden_input=True,
        )
        if password_pattern.match(password):
            return password
        else:
            print('Password does not meet the criteria.\n')


def get_domain(setup_scheme):
    domain = ''
    if setup_scheme == 'TLS_DOMAIN':
        domain = input("Enter the domain name (e.g., 'example.com') " "without leading 'www.': ").strip()
    log('Entered Domain: ' + domain)
    return domain


def get_credentials_for_pw_reset():
    question = (
        "\nDo you want to Enter the credentials for the website's "
        'password reset function?\nYou can add the credentials for the '
        "website's password reset function later in /etc/biomed-iot/config.toml"
    )
    while True:
        user_answer = input(f'{question} (y/n): ').strip().lower()
        if user_answer == 'y':
            pwreset_host = get_confirmed_text_input(
                'Enter the host ' "for the website's password reset function (e.g. smtp.gmail.com)"
            )
            pwreset_port = int(
                get_confirmed_text_input('Enter the port ' "for the website's password reset function (e.g. 587)")
            )
            pwreset_email = get_confirmed_text_input(
                'Enter the email address ' "for the website's password reset function"
            )
            pwreset_pass = get_confirmed_text_input(
                'Enter the password ' "for the website's password reset function",
                hidden_input=True,
            )
            msg = 'Credentials for password reset functions have been entered'
            break
        elif user_answer == 'n':
            msg = 'No credentials for password reset function have been entered'
            pwreset_host = ''
            pwreset_port = ''
            pwreset_email = ''
            pwreset_pass = ''
            break
        else:
            print("Invalid response. Please enter 'Y' or 'N'.")
    print(msg)
    log(msg)
    return pwreset_host, pwreset_port, pwreset_email, pwreset_pass


def create_tmp_dir():
    # Create a temporary folder for config files within setup_dir
    tmp_dir = os.path.join(get_setup_dir(), 'setup_files', 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    log("Directory 'setup_files/tmp' created. Path: " + tmp_dir)


def create_config_dir():
    # Create a folder for the project-wide config.toml file
    config_dir = '/etc/biomed-iot'
    os.makedirs(config_dir, exist_ok=True)
    log("Directory '/etc/biomed-iot' created. Path: " + config_dir)


def main():
    """
    Content:
    - "DO PRE-CHECKS"
    - "ASK FOR USER INPUT"
    - "INSTALLATION OF SOFTWARE" (setup files in sub directory "setup_files")
    - "WRITE CONFIG FILE" (Some config data will be written during installation of software)
    - "FINAL INFORMATION OUTPUT FOR THE USER"
    """

    hostname = socket.gethostname()
    ip_address = run_bash("hostname --all-ip-addresses | awk '{print $1}'", show_output=False)
    linux_user = get_linux_user()
    setup_dir = get_setup_dir()
    django_admin_name = 'admin-' + get_random_string(5)
    django_admin_pass = 'Dj4' + get_random_string(2) + '-' + get_random_string(5) + '-' + get_random_string(5)
    pwreset_email = None
    pwreset_pass = None
    domain = ''
    setup_scheme = None

    print_logo_header()

    """ DO PRE-CHECKS """
    architecture = get_and_check_cpu_architecture()

    is_running_with_sudo_or_exit_setup()

    print("\nTo make sure your system is up to date, run 'sudo apt update' " "and 'sudo apt upgrade' before setup.\n")
    confirm_proceed('Do you want to proceed? Otherwise please update, upgrade ' 'and reboot - then start setup again.')

    """ ASK FOR USER INPUT """
    setup_scheme = get_setup_scheme()
    
    domain = get_domain(setup_scheme)

    django_admin_email = get_confirmed_text_input('Enter email address for ' "your website's admin user")

    pwreset_host, pwreset_port, pwreset_email, pwreset_pass = get_credentials_for_pw_reset()
    pw_reset_credentials = {
        'RES_EMAIL_HOST': pwreset_host,
        'RES_EMAIL_PORT': pwreset_port,
        'RES_EMAIL_ADDRESS': pwreset_email,
        'RES_EMAIL_PASSWORD': pwreset_pass,
    }

    """ INSTALLATION OF SOFTWARE """

    print(
        '\nThis will install Biomed IoT with server installation scheme: '
        f"{setup_scheme} into directory '{setup_dir}' for user '{linux_user}'"
    )
    confirm_proceed(
        'Do you want to proceed with the installation of ' 'Biomed IoT, including necessary packages and services?'
    )
    msg = '\nStarting installation of Biomed IoT. Please do not interrupt!\n'
    print(msg)
    log(msg)

    # Capture the start time to measure the duration of the setup routine
    start_time = time.time()

    # TODO: build gateway zip file

    create_tmp_dir()
    create_config_dir()

    host_config_data = {
        'IP': ip_address,
        'HOSTNAME': hostname,
        'DOMAIN': domain,
        'TLS': "true" if setup_scheme != 'NO_TLS' else "false"
    }

    empty_config_data = generate_empty_config_data()
    write_config_file(empty_config_data)

    install_basic_apt_packages()
    print('Basic apt packages installed')
    log('Basic apt packages installed')

    install_security_packages()
    print('Security Packages installed')
    log('Security Packages installed')

    install_docker()
    print('Docker installed')
    log('Docker installed')

    nodered_config_data = install_nodered(setup_scheme)
    print('Node-RED installed')
    log('Node-RED installed')

    influxdb_config_data = install_influxdb(architecture)
    print('InfluxDB installed')
    log('InfluxDB installed')

    grafana_config_data = install_grafana(
        architecture, 
        setup_scheme, 
        ip_address, 
        domain,
        django_admin_email,
        django_admin_name,
        django_admin_pass
        )
    print('Grafana installed')
    log('Grafana installed')

    mosquitto_config_data = install_mosquitto(setup_scheme)
    print('Mosquitto Broker installed')
    log('Mosquitto Broker installed')

    postgres_config_data = install_postgres()
    print('')
    log('PostgreSQL database installed')

    # Write current known config data to config.toml; essential for django setup
    current_config_data = {
        **host_config_data,
        **pw_reset_credentials,
        **nodered_config_data,
        **influxdb_config_data,
        **grafana_config_data,
        **mosquitto_config_data,
        **postgres_config_data,
    }
    write_config_file(current_config_data)

    set_setup_dir_rights()
    django_config_data = install_django(
        django_admin_email,
        django_admin_name,
        django_admin_pass
    )
    print('Django installed')
    log('Django installed')

    install_gunicorn()
    print('Gunicorn installed')
    log('Gunicorn installed')

    install_nginx(setup_scheme, domain, ip_address, hostname)
    print('NGINX installed')
    log('NGINX installed')

    set_setup_dir_rights()

    """WRITE CONFIG FILE"""

    all_config_data = {
        **host_config_data,
        **pw_reset_credentials,
        **nodered_config_data,
        **influxdb_config_data,
        **grafana_config_data,
        **mosquitto_config_data,
        **postgres_config_data,
        **django_config_data,
    }

    write_config_file(all_config_data)

    # Capture the end time and calculate the total time taken for setup.
    end_time = time.time()
    setup_duration = end_time - start_time
    num_minutes = int(setup_duration // 60)
    num_seconds = setup_duration % 60

    """ FINAL INFORMATION OUTPUT FOR THE USER """
    # TBD
    # set pw reset credentials in config.toml
    print('\n\n\n\n____________________________')
    print('\n\nThe setup of Biomed IoT has successfully completed in\n' f'{num_minutes} min and {num_seconds} s.')

    print("\n\nAccess your website's admin user credentials in '/etc/biomed-iot/config.toml'.")

    msg_no_tls = f'The website is accessible at http://{ip_address}'
    msg_tls_no_domain = f'The website is accessible at https://{ip_address}'
    msg_tls_domain = f'The website is accessible at https://{domain}'

    if setup_scheme == 'NO_TLS':
        print(msg_no_tls)
        log(msg_no_tls)
    elif setup_scheme == 'TLS_NO_DOMAIN':
        print(msg_tls_no_domain)
        log(msg_tls_no_domain)
    else:
        print(msg_tls_domain)
        log(msg_tls_domain)

    print(
        '\nFor detailed information on the installation process, '
        f'please refer to the log files located in {setup_dir}/setup_files/setup_logs.\n'
        f"You can delete the directory 'tmp' in '{setup_dir}/setup_files/'"
        '\nTo make everything work, please reboot your machine and then change the grafana admin password'
    )

    print('\n--- END OF SETUP ---\n\n')


if __name__ == '__main__':
    main()
