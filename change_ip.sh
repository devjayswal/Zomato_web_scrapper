#!/bin/bash

# Network interface to change IP address for
INTERFACE="eth0"  # Change to "eth1" if needed

# Generate a random IP address within a specific range
OCTET=$(shuf -i 1-254 -n 1)
NEW_IP="68.183.83.$OCTET"  # Adjust the IP range according to your network

# Change the IP address using ifconfig
sudo ifconfig $INTERFACE $NEW_IP netmask 255.255.240.0 up

echo "IP address changed to $NEW_IP"


#!/bin/bash

# Network interface to change IP address for
INTERFACE="eth1"  # Change to "eth1" if needed

# Generate a random IP address within a specific range
OCTET=$(shuf -i 1-254 -n 1)
NEW_IP="68.183.83.$OCTET"  # Adjust the IP range according to your network

# Change the IP address using ifconfig
sudo ifconfig $INTERFACE $NEW_IP netmask 255.255.240.0 up

echo "IP address changed to $NEW_IP"

