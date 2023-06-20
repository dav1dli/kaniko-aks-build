# Flask-Docker-App

Example python project.

The project shows how to build a container using kaniko
and publish the container to ACR. The project provides an example of Azure Devops pipeline automating the build.

Problem: container images traditionally built with `docker build`. This works for interactive scenarios or on traditional hypervisor VMs but when trying to move such workloads to containers it requires running containers in privileged mode. It is undesirable or might be forbidden by security policies.

Solution: [kaniko](https://github.com/GoogleContainerTools/kaniko) is a tool building container images from a Dockerfile, provided as a container which can run locally or in a Kubernetes cluster.

Prerequisites:
* Azure CLI
* AKS cluster running
* ACR

# Local
Kaniko container can run locally, build an image from a local context and push it to ACR registry requiring authentication.

Login to ACR:
```
docker login -u ACRPOCDL -p XXXXX acrpocdl.azurecr.io
```
This command creates credentials configuration in `$HOME/.docker/config.json`. It is injected into kaniko container. Image context (directory with files needed to build the image) is expected in /workspace.

Build and push an image:
```
docker run \
  -v $HOME:/workspace \
  -v $HOME/.docker:/kaniko/.docker \
  gcr.io/kaniko-project/executor \
  -d acrpocdl.azurecr.io/test:latest
```
Alternatively, the container image build context (files needed for the image build) can be archived (tar.gz) and published to a storage account blob. From where kaniko can download the archive, unpack it locally and run the build. This eliminates the need to mount the volume and it requires environment variable `AZURE_STORAGE_ACCESS_KEY` set to contain a storage account access key:

```
docker run \
  -e AZURE_STORAGE_ACCESS_KEY=XXXXX \
  -v $HOME/.docker:/kaniko/.docker \
  gcr.io/kaniko-project/executor \
  -d acrpocdl.azurecr.io/test:latest \
  -c https://STORAGEACCOUNT.blob.core.windows.net/imgbld/python-app-40160.tar.gz
```
where `python-app-40160.tar.gz` is the context archive.

Storage account key can be set with
```
AZURE_STORAGE_ACCESS_KEY=$(az storage account keys list \
  -g $(RESOURCE_GROUP) -n $(STORAGE_ACCOUNT_IMGBLD) \
  --query "[0].value")
```

# AKS
Instead of running Docker in Docker on a self-hosted agent a container image can be built in a separate pod running kaniko. The agent still needs to be able to access Azure APIs and sources, package and publish them to a storage account accessible by the AKS cluster running the image build kaniko pod.

Container registry authentication configuration can be provided as a secret and mounted in the image build pod.

*Note:* kaniko is EXTREMELY sensitive to the container registry file formatting. File .docker/config.json created by docker login command seems to be satisfying. This is NOT a registry pull kind of secret.

Create `config.json`:
```
docker login -u $(ACRUSER) -p $(ACRPASS) $(ACR_NAME)
```
Container registry configuration secret:
```
kubectl create secret generic acr-config \
  --from-file=config.json=.docker/config.json \
  -n $(imgname)-$(imgtag) -o yaml
```
Pod:
```
apiVersion: v1
kind: Pod
metadata:
  name: imgbuild
spec:
  restartPolicy: Never
  containers:
  - args:
    - --dockerfile=Dockerfile
    - --context=https://$(STGACC).blob.core.windows.net/imgbld/$(imgname)-$(tag).tar.gz
    - --destination=$(ACR_NAME}/$(imgname):$(tag)
    image: gcr.io/kaniko-project/executor:latest
    name: kaniko
    resources:
      limits:
        cpu: "1"
        memory: 1Gi
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker/
    envFrom:
    - secretRef:
        name: strg-config
  volumes:
  - name: docker-config
    secret:
      secretName: acr-config
```
# Azure DevOps pipeline
Azure DevOps pipeline is in `devops/pipelines/aks-build.yml`.