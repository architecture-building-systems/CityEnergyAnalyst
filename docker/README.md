== Converting a Docker image into a Singularity image ==
$ docker images

 REPOSITORY                 TAG       IMAGE ID       CREATED          SIZE
 jp1127/ubuntu-python3     latest    d639b6f22ee5   18 minutes ago   2.19GB

$ docker save d639b6f22ee5 -o ubuntu-python3.tar
$ scp ubuntu-python3.tar jarunanp@euler.ethz.ch:/cluster/scratch/jarunanp

Login to Euler
$ ssh jarunanp@euler.ethz.ch
$

== Use a Docker image on Dockerhub ==
$ docker build -t jp1127/ubuntu-python3 .
$ docker images
 REPOSITORY                 TAG       IMAGE ID       CREATED          SIZE
 jp1127/ubuntu-python3     latest    d639b6f22ee5   18 minutes ago   2.19GB

$ docker login
username: jp1127
password:

$ docker push jp1127/ubuntu-python3:latest
The push refers to repository [docker.io/jp1127/ubuntu-python3]
4648e930d81f: Pushed 
2e38cc729d73: Pushed 
f281ab5d2fac: Pushed 
2f140462f3bc: Mounted from library/ubuntu 
63c99163f472: Mounted from library/ubuntu 
ccdbb80308cc: Mounted from library/ubuntu 
latest: digest: sha256:cd8a34b30aabe432232787d1e93844cd01027c2b235fb88f106297ed26c1f2ca size: 1576

$ ssh jarunanp@euler.ethz.ch
On Euler:
$ module load eth_proxy
$ singularity pull docker://jp1127/ubuntu-python3
INFO:    Converting OCI blobs to SIF format
WARNING: 'nodev' mount option set on /scratch, it could be a source of failure during build process
INFO:    Starting build...
Getting image source signatures
Copying blob 345e3491a907 done  
Copying blob 57671312ef6f done  
Copying blob 5e9250ddb7d0 done  
Copying blob 59cb202cc95d done  
Copying blob 11a3e9d5c98b done  
Copying blob 0dc45453c4be done  
Copying config 60390c52c7 done  
Writing manifest to image destination
Storing signatures
2021/06/09 14:05:31  info unpack layer: sha256:345e3491a907bb7c6f1bdddcf4a94284b8b6ddd77eb7d93f09432b17b20f2bbe
2021/06/09 14:05:32  info unpack layer: sha256:57671312ef6fdbecf340e5fed0fb0863350cd806c92b1fdd7978adbd02afc5c3
2021/06/09 14:05:32  info unpack layer: sha256:5e9250ddb7d0fa6d13302c7c3e6a0aa40390e42424caed1e5289077ee4054709
2021/06/09 14:05:32  info unpack layer: sha256:59cb202cc95d3e96a8ea195395e5aba5386cb0a7aefc920e419fa1b8b5b15bbf
2021/06/09 14:05:32  info unpack layer: sha256:11a3e9d5c98bcb1bc09f415abb9db936988faf1128fabe875ee18f31d497a9d2
2021/06/09 14:05:32  info unpack layer: sha256:0dc45453c4bed490c08acc9437d253d2c36290e72d00c43fa1779f7a42b12e48
INFO:    Creating SIF file...

$ ls
ubuntu-python3_latest.sif

$ singularity shell ubuntu-python3_latest.sif
Singularity> lsb_release -a

No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 20.04.2 LTS
Release:	20.04
Codename:	focal

Singularity> python3
Python 3.8.5 (default, May 27 2021, 13:30:53) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import tensorflow as tf
2021-06-09 14:08:24.919069: W tensorflow/stream_executor/platform/default/dso_loader.cc:64] Could not load dynamic library 'libcudart.so.11.0'; dlerror: libcudart.so.11.0: cannot open shared object file: No such file or directory; LD_LIBRARY_PATH: /.singularity.d/libs
2021-06-09 14:08:24.919094: I tensorflow/stream_executor/cuda/cudart_stub.cc:29] Ignore above cudart dlerror if you do not have a GPU set up on your machine.
>>> tf.__version__
'2.5.0'
>>> 
Singularity> 