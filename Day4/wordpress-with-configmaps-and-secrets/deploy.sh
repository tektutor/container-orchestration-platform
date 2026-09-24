echo "\nDeploying mysql ..."
oc apply -f wordpress-cm.yml
oc apply -f wordpress-secrets.yml
oc apply -f mysql-pv.yml
oc apply -f mysql-pvc.yml
oc apply -f mysql-deploy.yml
oc apply -f mysql-svc.yml

echo "\nDeploying wordpress ..."
oc apply -f wordpress-pv.yml
oc apply -f wordpress-pvc.yml
oc apply -f wordpress-deploy.yml
oc apply -f wordpress-svc.yml
oc apply -f wordpress-route.yml
