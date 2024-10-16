#!/usr/bin/python3
import subprocess
import sys
import syslog


def cleaning_resources_and_exit():
    syslog.closelog()
    sys.exit(1)


def run_command(command: str) -> subprocess.CompletedProcess:
    syslog.syslog(syslog.LOG_DEBUG, f'Attempt run command: {command}')
    result = subprocess.run(args=command, shell=True, capture_output=True)
    syslog.syslog(syslog.LOG_DEBUG, f'Return code of the command = {result.returncode}')
    return result


def delete_interface(namespace: str, interface_name: str) -> None:
    syslog.syslog(syslog.LOG_INFO, f'Delete interface {interface_name} in namespace {namespace}')

    command = f'ip netns exec {namespace} ip link delete {interface_name}'
    result = run_command(command)
    if result.returncode != 0:
        syslog.syslog(syslog.LOG_ERR, f'Error: {result.stderr.decode("utf-8")}')
        cleaning_resources_and_exit()

    syslog.syslog(syslog.LOG_INFO, f'Interface {interface_name} deleted in namespace {namespace}')


def delete_namespace(namespace: str) -> None:
    syslog.syslog(syslog.LOG_INFO, f'Delete namespace {namespace}')

    command = f'ip netns delete {namespace}'
    result = run_command(command)
    if result.returncode != 0:
        syslog.syslog(syslog.LOG_ERR, f'Error: {result.stderr.decode("utf-8")}')
        cleaning_resources_and_exit()

    syslog.syslog(syslog.LOG_INFO, f'Namespace {namespace} deleted')


def delete_interface_namespace(namespace: str) -> None:
    syslog.syslog(syslog.LOG_DEBUG, f'Get full interface')
    command = f'ip netns exec {namespace} ls /proc/sys/net/ipv4/neigh/'
    result = run_command(command)
    if result.returncode != 0:
        syslog.syslog(syslog.LOG_ERR, f'Error: {result.stderr.decode("utf-8")}')
        cleaning_resources_and_exit()
    else:
        list_interfaces = result.stdout.decode('utf-8').split()
        for interface in list_interfaces:
            if interface.startswith('ng_') or interface == 'lo':
                continue
            else:
                delete_interface(namespace, interface)

    delete_namespace(namespace)


def get_network_namespaces() -> list:
    command = 'ip netns list'
    result = subprocess.run(args=command, shell=True, capture_output=True)
    if result.returncode != 0:
        syslog.syslog(syslog.LOG_ERR, f'Error: {result.stderr.decode("utf-8")}')
        cleaning_resources_and_exit()
    else:
        return [line.split()[0] for line in result.stdout.decode('utf-8').split('\n') if line.strip()]


if __name__ == "__main__":
    namespaces = get_network_namespaces()
    syslog.syslog(syslog.LOG_INFO, f'Find namespaces: {namespaces}')
    for namespace in namespaces:
        delete_interface_namespace(namespace.split(' ')[0].strip())
