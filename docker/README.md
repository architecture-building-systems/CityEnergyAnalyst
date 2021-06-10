## Use a Docker image on Dockerhub
### On your local computer
Build a Docker image
```
$ docker build -t dockeruser/cityea:latest .
$ docker images
REPOSITORY                   TAG       IMAGE ID       CREATED          SIZE
dockeruser/cityea:latest    latest    d639b6f22ee5   18 minutes ago   4.69GB
```
Log in to Dockerhub before pushing the image to Dockerhub
```
$ docker login
username: dockeruser
password:
```
Push the Docker image to Dockerhub
```
$ docker push dockeruser/cityea:latest
```
Log in to Euler
```
$ ssh nethzuser@euler.ethz.ch
```

### On Euler
Request a compute node with Singularity
```
$ bsub -n 1 -R singularity -R light -Is bash
```
Load eth_proxy to connect to the internet from compute nodes
```
$ module load eth_proxy
```
Pull the container image with Sigularity
```
$ singularity pull docker://dockeruser/cityea
$ ls
cityea_latest.sif
```
Run the container interactively as shell
```
$ singularity shell -B $HOME cityea_latest.sif
Singularity> source /venv/bin/activate
(venv) Singularity> cea test
```
