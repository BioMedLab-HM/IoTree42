from .setup_utils import run_bash, get_random_string

MOSQUITTO_INSTALL_LOG_FILE_NAME = "install_mosquitto.log"

def install_mosquitto():
    """
    
    """
    

    commands = [
        ''
    ]

    for command in commands:
        run_bash(command, MOSQUITTO_INSTALL_LOG_FILE_NAME)
