
following spark on docker tutorial here: 
https://medium.com/@SaphE/testing-apache-spark-locally-docker-compose-and-kubernetes-deployment-94d35a54f222


also:
sudo usermod -aG docker $USER
sudo chmod 660 /var/run/docker.sock

that didn't work. trying this:
sudo chown $USER /var/run/docker.sock
that worked.
update: maybe it did work but i needed to log out and log back in...

run with:
docker-compose up
