# -*- coding: utf-8 -*-
import pytest
from PySSHHelper import SSHConnection


# Test setup
@pytest.fixture
def ssh_connection():
    # Set up SSHConnection instance for testing
    ssh = SSHConnection(host="localhost", port=22, username_ssh="username_ssh",
                        password_ssh="password_ssh", username_sudo="username_sudo",
                        password_sudo="password_sudo")
    ssh.connect()
    yield ssh
    ssh.close()


# Test cases
def test_connect(ssh_connection):
    # Test whether the connection is established
    assert ssh_connection.is_connected == True


def test_elevate_privileges(ssh_connection):
    # Test elevating privileges
    ssh_connection.elevate_privileges()
    assert ssh_connection.prompt == ssh_connection.prompt_sudo


def test_revoke_privileges(ssh_connection):
    # Test revoking privileges
    ssh_connection.revoke_privileges()
    assert ssh_connection.prompt == ssh_connection.prompt_normal


def test_execute_command(ssh_connection):
    # Test executing a command
    output = ssh_connection.execute_command("echo 'Hello, SSH!'")
    assert 'Hello, SSH!' in output


def test_cleanup_escape_codes():
    # Test cleaning up escape codes
    text_with_escape_codes = "\x1b[1;31mHello\x1b[0m"
    cleaned_text = SSHConnection.cleanup_escape_codes(text_with_escape_codes)
    assert cleaned_text == "Hello"

# Add more test cases as needed
