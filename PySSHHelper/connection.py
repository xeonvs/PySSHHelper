# -*- coding: utf-8 -*-
import re
import logging
import paramiko
import time


class SSHConnection:
    ESCAPE_PATTERN = re.compile(r'\x1b[^m]*m')

    def __init__(self, host: str, port: int, username_ssh: str, password_ssh: str,
                 username_sudo: str, password_sudo: str, exec_sleep_time: int = 1, ssh_timeout: int = 15,
                 prompt_shell: str = '$', prompt_sudo: str = '#',
                 verbose_ssh: bool = False, verbose: bool = False):
        self.host = host
        self.port = port
        self.username_ssh = username_ssh
        self.username_sudo = username_sudo
        self.password_ssh = password_ssh
        self.password_sudo = password_sudo
        self.ssh_timeout = ssh_timeout
        self.exec_sleep_time = exec_sleep_time
        self.ssh_client = paramiko.SSHClient()
        self.is_connected: bool = False
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_shell = None
        self.prompt_normal = prompt_shell
        self.prompt_sudo = prompt_sudo
        self.prompt = prompt_shell
        self.verbose = verbose
        self.verbose_ssh = verbose_ssh

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.WARNING)

        if self.verbose:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        if self.verbose_ssh:
            paramiko_log = logging.getLogger("paramiko")
            paramiko_log.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            paramiko_log.addHandler(handler)

    def connect(self):
        try:
            self.ssh_client.connect(self.host, self.port, self.username_ssh, self.password_ssh,
                                    timeout=self.ssh_timeout)
            self.logger.info("Connected to SSH server")
            stdin, stdout, stderr = self.ssh_client.exec_command("whoami", get_pty=True)
            self.is_connected = stdout.readline().strip() == self.username_ssh
            if not self.is_connected:
                self.logger.error('Not logged in!')
                self.ssh_client = None

        except paramiko.AuthenticationException:
            self.logger.error("Authentication failed, please check your credentials.")
            self.ssh_client = None
        except paramiko.SSHException as ssh_ex:
            self.logger.error("Unable to establish SSH connection: %s" % ssh_ex)
            self.ssh_client = None
        except Exception as e:
            import traceback
            self.logger.error(f"Connection exception: {str(e)}")
            self.logger.error("\n".join(traceback.format_exception(e)))
            self.close()
            self.ssh_client = None

    def elevate_privileges(self, prompt_start_timeout: int = 2):
        """
        Elevate privileges by sudo su - username command
        :param prompt_start_timeout: wait timeout before sudo prompt.
        """
        if self.ssh_client:
            if self.ssh_shell:
                self.ssh_shell.send("sudo su - " + self.username_sudo + "\n")
                time.sleep(prompt_start_timeout)
                for t in range(3):
                    self.ssh_shell.send(self.password_sudo + '\n')
                    if self.ssh_shell.recv_ready():
                        data = self.ssh_shell.recv(1024).decode('utf-8')
                        if data.strip().endswith(self.prompt_sudo):
                            self.prompt = self.prompt_sudo
                            return
                    time.sleep(1)
        else:
            self.logger.warning("Not connected to SSH server")

    def revoke_privileges(self):
        if self.ssh_client:
            if self.ssh_shell and self.prompt == self.prompt_sudo:
                self.ssh_shell.send("exit\n")
                self.prompt = self.prompt_normal
        else:
            self.logger.warning("Not connected to SSH server")

    def execute_command(self, command, buffer_size: int = 65535,
                        wait_complete: bool = True, timeout: int = 60) -> str:
        """
        :param command: shell command
        :param buffer_size: socket buffer size
        :param wait_complete: wait shell prompt after command execution
        :param timeout: output wait timeout
        :return: all output from console
        """
        if self.ssh_client:
            if not self.ssh_shell:
                self.ssh_shell = self.ssh_client.invoke_shell()

            self.ssh_shell.send(command + '\n')

            output = ''
            if wait_complete:
                # Wait execution
                timeout += self.exec_sleep_time
                while True:
                    if self.ssh_shell.recv_ready():
                        data = self.ssh_shell.recv(buffer_size)
                        if not data:
                            break
                        data = data.decode('utf-8')
                        output += data

                        # Check if the prompt is in the output, indicating that the command has completed
                        if data.strip().endswith(self.prompt):
                            break

                    time.sleep(self.exec_sleep_time)
                    timeout -= self.exec_sleep_time
                    if timeout <= 0:
                        output += '\ncommand timeout\n'
                        break
            else:
                # No wait command result
                while self.ssh_shell.recv_ready():
                    data = self.ssh_shell.recv(buffer_size)
                    if not data:
                        break
                    output += data.decode('utf-8')

            return output
        else:
            self.logger.warning("Not connected to SSH server")

    @staticmethod
    def cleanup_escape_codes(text: str) -> str:
        """Remove escape codes from the text using the pre-compiled pattern"""
        clean_text = SSHConnection.ESCAPE_PATTERN.sub('', text)
        return clean_text

    def sftp_get(self, remote_path, local_path):
        """
        Get file from remote server
        """
        if self.ssh_client:
            sftp_client = self.ssh_client.open_sftp()
            sftp_client.get(remote_path, local_path)
            sftp_client.close()
        else:
            self.logger.warning("Not connected to SSH server")

    def sftp_put(self, local_path, remote_path):
        """
            Put local file to remote server
        """
        if self.ssh_client:
            sftp_client = self.ssh_client.open_sftp()
            sftp_client.put(local_path, remote_path)
            sftp_client.close()
        else:
            self.logger.warning("Not connected to SSH server")

    def list_directory(self, path: str = '.'):
        """
            List files in directory path on remote server
        """
        if self.ssh_client:
            sftp_client = self.ssh_client.open_sftp()
            files = sftp_client.listdir(path)
            sftp_client.close()
            return files
        else:
            self.logger.warning("Not connected to SSH server")

    def close(self):
        if self.ssh_client:
            self.ssh_client.close()
            self.logger.info("Disconnected from SSH server")
        else:
            self.logger.warning("Not connected to SSH server")
