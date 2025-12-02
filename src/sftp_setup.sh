ssh-keygen -t rsa -b 4096
sftpserver --host localhost -p 2222 -k ~/.ssh/id_rsa