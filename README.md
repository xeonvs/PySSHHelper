[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/xeonvs/PySSHHelper?logo=github)](https://github.com/xeonvs/PySSHHelper/releases) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<!-- [![Pypi_Version](https://img.shields.io/pypi/v/PySSHHelper.svg)](https://pypi.python.org/pypi/PySSHHelper) -->
<!-- [![Downloads](https://static.pepy.tech/personalized-badge/PySSHHelper?period=total&units=international_system&left_color=black&right_color=blue&left_text=Downloads)](https://pepy.tech/project/PySSHHelper) -->

Please note that the project is in beta phase. Please report any issues you encounter or suggestions you have. We will do our best to address them quickly. Contributions are very welcome!

# PySSHHelper
PySSHHelper is a Python library for simplifying SSH connections and interactions with remote servers.

## Installation
You can install PySSHHelper using pip:

```shell
pip install PySSHHelper
```

If you would like the most up-to-date version, you can instead install directly from GitHub:
```shell
git clone <copied link from github>
cd PySSHHelper
pip install .
```

### Example of usage
```python
from PySSHHelper import SSHConnection
```

After importing the package, you can use SSHConnection in your code:
```python
# Create an SSH connection object
ssh = SSHConnection(
    host='your_host',
    port=22,
    username_ssh='your_ssh_username',
    password_ssh='your_ssh_password',
    username_sudo='your_sudo_username',
    password_sudo='your_sudo_password',
    verbose=True  # Set verbose to True for debugging information
)

# Connect to the SSH server
ssh.connect()

# Execute a command
output = ssh.execute_command("ls -l")
print(output)
```

The output variable will contain all output in the console, including escape codes from the terminal, you can use the method to clear them:
```python
print(ssh.cleanup_escape_codes(output))
```

If you want to execute commands in sudo context:
```python
ssh.elevate_privileges()
print(ssh.execute_command("echo 123 && sleep 5 && echo 321", timeout=10))
print(ssh.execute_command("id"))
```

And after you can revoke privileges and then continue to execute in normal context
```python
ssh.revoke_privileges()
print(ssh.execute_command("id"))
```

Also, you can do some SFTP operations
```python
print(ssh.list_directory())
ssh.sftp_get('/remote/path/file.txt', 'local_file.txt')
ssh.sftp_put('local_file.txt', '/remote/path/file.txt')
```

Close the SSH connection
```python
ssh.close()
```
