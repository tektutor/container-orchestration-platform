# Day 3

## Info - Default CPU, RAM resources allocated by Kubernetes
<pre>
- In case, we haven't explicitly requested for CPU, RAM, etc resources,
  how much CPU, RAM, etc resources will be allocated by Kubernetes by default
- Answer:
  - No guaranteed CPU ( can use whatever is available on the node )
  - No guaranteed RAM ( can use whatever is available on the node )
  - No upper limit on either ( can consume the entire node )
  - pods that don't have these kind of constraints defined are the ones first will be killed
    when the node runs out of memory
  - Administrators can define cluster-wide defaults per namespace using a LimitRange
</pre>

## Lab - Declaratively deploy nginx into Kubernetes with Kubernetes manifest file(yaml)
```
# In case, you already have some deployment and service, let's delete them first
kubectl delete deploy/nginx svc/nginx -n jegan

# Let's generate the declarative manifest yaml to deploy nginx
kubectl create deployment nginx --image=nginx:latest --replicas=3 --dry-run=client -o yaml
kubectl create deployment nginx --image=nginx:latest --replicas=3 --dry-run=client -o yaml > nginx-deploy.yml

# Create nginx deployment in declarative style
# First time this should be used
kubectl create -f nginx-deploy.yml --save-config=true

# Let's say we made some delta changes like we updated the replicas from 3 to 5 pods
# Subsequent times - second time onwards this is the recommended approach
kubectl apply -f nginx-deploy.yml

kubectl get deploy,rs,po
```

## Lab - Moving to a specific namespace to avoid repeatedly mentioning namespace for each command
```
kubectl config set-context --current --namespace=jegan
```

Checking the current namespace, minify shows the current context
```
kubectl config view --minify | grep namespace
```

## Lab - Declaratively creating ClusterIP Internal Service
```
# Ensure you are in your namespace
kubectl config view --minify | grep namespace

kubectl get deploy

kubectl expose deploy/nginx --type=ClusterIP --port=80 --dry-run=client -o json
kubectl expose deploy/nginx --type=ClusterIP --port=80 --dry-run=client -o yaml > nginx-clusterip-svc.yml

kubectl create -f nginx-clusterip-svc.yml --save-config=true
kubectl get svc
kubectl describe svc/nginx

# Create a test pod to try accessing the clusterip internal service
kubectl run test --image=tektutor/spring-ms:1.0 --port=8080
# -w will put this command in watch mode, so you can see the pod status getting updated in real-time, to come out press Ctrl+c
kubectl get pod -w

kubectl exec -it test -- /bin/bash

curl http://nginx:80
```

## Lab - Declaratively creating NodePort external service
Let's ensure the existing clusterip internal service is declaratively deleted
```
kubectl delete -f nginx-clusterip-svc.yml
```

Let's create the declarative manifest file for nodeport service
```
kubectl expose deploy/nginx --type=NodePort --port=80 --dry-run=client -o yaml > nginx-nodeport-svc.yml
kubectl apply -f nginx-nodeport-svc.yml

kubectl get svc

curl http://192.168.122.230:31208
```

## Lab - Declaratively deleting nginx deployment
```
kubectl delete -f nginx-deploy.yml
kubectl get deploy,rs,po
```

## Lab - 
