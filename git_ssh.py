#!/usr/bin/env python3
import paramiko, sys, os

key_path = os.path.expanduser("~/.ssh/id_rsa")
key = paramiko.RSAKey.from_private_key_file(key_path)

host = sys.argv[1].split()[0] if len(sys.argv) > 1 else "github.com"

# Use paramiko's proxycommand approach
# Actually, git needs us to act as an SSH transport
# We'll use the GIT_SSH_COMMAND approach with a paramiko-based SSH client

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("github.com", username="git", pkey=key)

# Get the command git wants to run
cmd = os.environ.get("SSH_ORIGINAL_COMMAND", "")
if not cmd and len(sys.argv) > 1:
    cmd = " ".join(sys.argv[1:])

if cmd:
    transport = client.get_transport()
    channel = transport.open_session()
    channel.exec_command(cmd)
    
    # Forward data between stdin/stdout and the channel
    import select, socket
    
    while True:
        r, w, x = select.select([channel, sys.stdin], [], [], 1.0)
        if channel in r:
            data = channel.recv(4096)
            if not data:
                break
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        if sys.stdin in r:
            data = sys.stdin.buffer.read(1)
            if not data:
                channel.shutdown_write()
            else:
                channel.send(data)
    
    channel.close()
    client.close()
    sys.exit(channel.recv_exit_status())
else:
    client.close()
    sys.exit(1)
