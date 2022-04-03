docker run --name portainer \
-p 9001:9000 -d --restart always \
-v /home/ubuntu/portainer:/data \
-v /var/run/docker.sock:/var/run/docker.sock \
portainer/portainer