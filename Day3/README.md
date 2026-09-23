# Day 3

## Lab - Declaratively deploy nginx into Kubernetes with Kubernetes manifest file(yaml)
```
# In case, you already have some deployment and service, let's delete them first
kubectl delete deploy/nginx svc/nginx -n jegan

# Let's generate the declarative manifest yaml to deploy nginx
kubectl create deployment nginx --image=nginx:latest --replicas=3 --dry-run=client -o yaml
kubectl create deployment nginx --image=nginx:latest --replicas=3 --dry-run=client -o yaml > nginx-deploy.yml

# Create nginx deployment in declarative style
kubectl create -f nginx-deploy.yml --save-config=true

# Let's say we made some delta changes like we updated the replicas from 3 to 5 pods
kubectl apply -f nginx-deploy.yml

kubectl get deploy,rs,po
```
