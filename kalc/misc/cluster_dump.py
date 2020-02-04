from kalc.interactive import ALL_RESOURCES
import subprocess

def run():
    for res in ALL_RESOURCES:
        result = subprocess.run(['kubectl', 'get', res, '--all-namespaces', '-o=yaml'])