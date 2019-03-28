import docker
import time
import sys
from os import path
from .utils import fs_util, cli_util

CUR_DIR = path.dirname(__file__)

if sys.version_info[0] < 3:
    user_input = raw_input
else:
    user_input = input


def run_syslog_server(logs_path, syslog_config_path):
    """
    Runs a syslog server that creates a volume with host in `log_path` and dumps logs there
    :param string logs_path: the host path where the logs will be saved for later processing
    :param string syslog_config_path: the syslog config path
    :return: The handle to the container to control it upstream
    """
    client = docker.from_env()
    volumes = [
        '{}:/var/log'.format(logs_path),
        '{}:/etc/syslog-ng/syslog-ng.conf'.format(syslog_config_path)
    ]
    container_handle = client.containers.run(image='balabit/syslog-ng:latest', command='--no-caps', stdout=True,
                                             stderr=True, remove=True, detach=True, volumes=volumes,
                                             ports={'514': '514'}, name='instrumentation-syslog-ng')
    return container_handle


def run_ngrok(auth_token, remote_addr):
    """
    Runs an ngrok docker container that the fastly service will send logs to
    :param string auth_token: the ngrok user authentication token
    :param  string remote_addr: the ngrok remote address to expose
    :return: The handle to the container to control it upstream
    """
    client = docker.from_env()
    syslog_name = 'instrumentation-syslog-ng'

    auth_token_str = '--authtoken ' + auth_token if auth_token else ''
    command = 'ngrok tcp {} --remote-addr {} {}:514'.format(auth_token_str, remote_addr, syslog_name)
    links = {syslog_name: syslog_name}
    container_handle = client.containers.run(image='wernight/ngrok:latest', command=command, stdout=True,
                                             stderr=True, remove=True, detach=True, links=links,
                                             name='instrumentation-ngrok')
    return container_handle


def start_listening(logs_path, standalone_proxy, proxy_remote_addr, listen_seconds, ngrok_auth_token):
    """
    Starts a docker syslog server and a docker ngrok to allow the fastly service to send logs to it
    :param string logs_path: the host path where the logs will be saved for later processing
    :param bool standalone_proxy: whether a standalone proxy is used
    :param string ngrok_auth_token: the ngrok user authentication token
    :param string proxy_remote_addr: the ngrok remote address to expose
    :param integer listen_seconds: optional - the number of seconds to listen for incoming logs
    :return:
    """
    syslog_config_path = path.join(CUR_DIR, 'assets', 'syslog-ng.conf')
    syslog_container_handle = None
    ngrok_container_handle = None
    try:
        syslog_container_handle = run_syslog_server(logs_path, syslog_config_path)
        if not standalone_proxy:
            ngrok_container_handle = run_ngrok(ngrok_auth_token, proxy_remote_addr)

        # sleeping to let service activate and containers finish booting up
        time.sleep(10)
        if listen_seconds:
            cli_util.output('Listening for {} seconds'.format(listen_seconds))
            time.sleep(listen_seconds)
        else:
            user_input('! You can now run the tests. Press any key when the tests finished..')
            time.sleep(5)
    finally:
        if ngrok_container_handle:
            ngrok_container_handle.stop()
        if syslog_container_handle:
            syslog_container_handle.stop()


def collect_logs(logs_path):
    """
    Reads the logs from the log path
    :param string logs_path:
    :return string: the content of the logs
    """
    return fs_util.read_file(path.join(logs_path, 'messages'))
