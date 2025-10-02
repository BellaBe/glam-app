#!/bin/bash
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}'

echo "Memory Usage:"
free -h

echo "Disk Usage:"
df -h /

echo "Docker Stats:"
docker stats --no-stream