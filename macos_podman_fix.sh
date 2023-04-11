# IN CASE YOU ARE ON A LOCAL MACHINE WITH MAC OS AND DO NOT WANT TO EXECUTE PYNGUIN / FLAPY ON A CLUSTER.
# HERE IS A POSSIBLE FIX IN ORDER TO USE PODMAN ON MAC OS.

# https://dalethestirling.github.io/Macos-volumes-with-Podman/ <-- If not working, here is the link i used. Worked for me.

YOUR_USER_NAME="Please type in your username here!"

# Connect to the host
ssh -i ~/.ssh/podman-machine-default -R 10000:$(hostname):22 -p 54575 core@localhost

# Generate SSH key and share back to Macos host
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
ssh-copy-id -p 10000 "${YOUR_USER_NAME}"@127.0.0.1

# Create mount point for host filesystem
sudo mkdir -p /mnt/Users
sudo chown core:core /mnt/Users

# Define our screen session
screen -t podman

# Connect to the VM with reverse proxy
ssh -i ~/.ssh/podman-machine-default -R 10000:$(hostname):2222 -p 54575 core@localhost

# Mount the host filesystem to the guest
sshfs -p 10000 "${YOUR_USER_NAME}"@127.0.0.1:/Users /mnt/Users