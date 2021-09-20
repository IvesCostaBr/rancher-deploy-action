import os
import sys
import requests
import json

class Log:
    def __init__(self, request):
        self.request = request
        
    def status_request(self):
        if self.request.status_code >= 200 and self.request.status_code < 299:
            print(f"""
               \033[92m REPONSE --> {self.request}  \033[0;0m
            """)
        else:
            print(f"""
                \033[1;31m RESPONSE FAIL--> {self.request.json()} \033[0;0m
            """)
        

class DeployRancher:
    def __init__(self, rancher_access_key, rancher_secret_key, rancher_url_api,
                 rancher_service_name, rancher_docker_image):
        self.access_key = rancher_access_key
        self.secret_key = rancher_secret_key
        self.rancher_url_api = rancher_url_api
        self.service_name = rancher_service_name
        self.docker_image = rancher_docker_image
        self.rancher_deployment_path = ''
        self.rancher_namespace = ''
        self.rancher_workload_url_api = ''

    def rancher_auth(self):
        return requests.get('{}/projects'.format(self.rancher_url_api), auth=(self.access_key, self.secret_key))

    def deploy(self):
        rp = self.rancher_auth()
        projects = rp.json()
        for p in projects['data']:
            w_url = '{}/projects/{}/workloads'.format(self.rancher_url_api, p['id'])
            rw = requests.get(w_url, auth=(self.access_key, self.secret_key))
            workload = rw.json()
            for w in workload['data']:
                if w['name'] == self.service_name:
                    self.rancher_workload_url_api = w_url
                    self.rancher_deployment_path = w['links']['self']
                    self.rancher_namespace = w['namespaceId']
                    break
            if self.rancher_deployment_path != '':
                break

        rget = requests.get(self.rancher_deployment_path,
                            auth=(self.access_key, self.secret_key))
        
        with open("log.json", "w") as outfile:
            outfile.write(json.dumps(rget.json(), indent=4))
            
        response = rget.json()
        if 'status' in response and response['status'] == 404:
            config = {
                "containers": [{
                    "imagePullPolicy": "Always",
                    "image": self.docker_image,
                    "name": self.service_name,
                }],
                "namespaceId": self.rancher_namespace,
                "name": self.service_name
            }

            requests.post(self.rancher_workload_url_api,
                          json=config, auth=(self.access_key, self.secret_key))
        else:
            response['containers'][0]['image'] = self.docker_image

            requests.put(self.rancher_deployment_path + '?action=redeploy',
                         json=response, auth=(self.access_key, self.secret_key))  
        Log(rget).status_request()
        sys.exit(0)
        
    def update_workload(self):
        pass
        
        
def deploy_in_rancher(rancher_access_key, rancher_secret_key, rancher_url_api,
                      rancher_service_name, rancher_docker_image):
    deployment = DeployRancher(rancher_access_key, rancher_secret_key, rancher_url_api,
                               rancher_service_name, rancher_docker_image)
      
    deployment.deploy()
    return deployment


if __name__ == '__main__':
    rancher_access_key = os.environ['RANCHER_ACCESS_KEY']
    rancher_secret_key = os.environ['RANCHER_SECRET_KEY']
    rancher_url_api = os.environ['RANCHER_URL_API']
    rancher_service_name = os.environ['SERVICE_NAME']
    rancher_docker_image = os.environ['DOCKER_IMAGE']
    rancher_docker_image_latest = os.environ['DOCKER_IMAGE_LATEST']
    
     
    try:
        deploy_in_rancher(rancher_access_key, rancher_secret_key, rancher_url_api,
                            rancher_service_name, rancher_docker_image)
        
        
        if rancher_docker_image_latest != None and rancher_docker_image_latest != "":
            deploy_in_rancher(rancher_access_key, rancher_secret_key, rancher_url_api, 
                                rancher_service_name, rancher_docker_image_latest)
                    
    except KeyError as key:
        raise  print(key)
        sys.exit(1)

        
        
 