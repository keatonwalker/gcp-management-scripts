import googleapiclient.discovery
from dataclasses import dataclass
import argparse
import json
import csv


class Project():
    """Store GCP project properties."""
    def __init__(self, project_rm_v3: dict):
        self.project_number = project_rm_v3['name'].split('/')[1]
        self.project_id = project_rm_v3['projectId']


def list_folder_projects(folder_number):
    """List all projects in a GCP folder."""
    rm = googleapiclient.discovery.build('cloudresourcemanager', 'v3')
    params = {
        'parent': f'folders/{folder_number}'
    }
    folder_projects = []
    projects = rm.projects()
    request  = projects.list(**params)
    while request is not None:
        projects_list = request.execute()
        folder_projects += [Project(prj) for prj in projects_list.get('projects', [])]
        request = projects.list_next(request, projects_list)
    
    return folder_projects

def list_enable_services(project_id):
    """List all API services that are enabled in a project."""
    project = f'projects/{project_id}'

    project_services = []
    api = googleapiclient.discovery.build('serviceusage', 'v1')
    services = api.services()
    request = services.list(parent=project, filter='state:ENABLED')
    while request is not None:
        services_list = request.execute()
        project_services += services_list.get('services', [])
        request = services.list_next(request, services_list)
    
    return [s['name'] for s in project_services]


def project_has_compute_api_enabled(project_number, service_usage_api=None):
    """
    Check if GCP project has compute engine API enabled.
    Projects without compute egnine API have no newtorking resources.
    """
    api = service_usage_api
    if api is None:
        api = googleapiclient.discovery.build('serviceusage', 'v1')

    services = api.services()
    request = services.get(name=f'projects/{project_number}/services/compute.googleapis.com')
    compute_service = request.execute()
    
    return compute_service['state'] == 'ENABLED'


class Firewall():
    """Class to store GCP firewall properties."""

    def __init__(self, project_rm_v3: dict):
        self.name = project_rm_v3['name']
        self.project_id = project_rm_v3['network'].split('projects/')[1].split('/')[0]
        self.vpc = project_rm_v3['network'].split('networks/')[1].split('/')[0]
        self.logging_enabled = project_rm_v3['logConfig']['enable']
    
    def __repr__(self):
        return repr(f'{self.project_id}/{self.vpc}/{self.name}')


def list_firewalls(project_id, compute_api=None, filter=None):
    """List all firewalls in a project."""
    api = compute_api
    if api is None:
        api = googleapiclient.discovery.build('compute', 'v1')
    
    project_firewalls = []
    firewalls = api.firewalls()
    request = firewalls.list(project=project_id, filter=filter)
    while request is not None:
        firewalls_list = request.execute()
        project_firewalls += [Firewall(fw) for fw in firewalls_list.get('items', [])]
        request = firewalls.list_next(request, firewalls_list)
    return project_firewalls


def list_firewalls_without_logging(project_id, compute_api=None):
    """List firewalls in a project that do not have logging enabled."""
    return list_firewalls(project_id, compute_api, filter='logConfig.enable=false')


class Subnetwork():
    """Class to store GCP subnet properties."""

    def __init__(self, subnet_compute_v1: dict):
        self.name = subnet_compute_v1['name']
        self.project_id = subnet_compute_v1['network'].split('projects/')[1].split('/')[0]
        self.vpc = subnet_compute_v1['network'].split('networks/')[1].split('/')[0]
        self.region = subnet_compute_v1['region'].split('regions/')[1].split('/')[0]
        self.logging_enabled = subnet_compute_v1.get('enableFlowLogs', False)
        self.logging_interval = subnet_compute_v1.get('aggregationInterval', None)
        self.logging_sample_percentage = subnet_compute_v1.get('flowSampling', None)
    
    def __repr__(self):
        
        return repr(f'{self.project_id}/{self.vpc}/{self.region}/{self.name}')


def list_subnetworks(project_id, compute_api=None, filter=None):
    """List all subnets in a project."""
    api = compute_api
    if api is None:
        api = googleapiclient.discovery.build('compute', 'v1')
    
    project_subnets = []
    subnets = api.subnetworks()
    request = subnets.aggregatedList(project=project_id)

    while request is not None:
        subnets_list = request.execute()
        regions = subnets_list.get('items', [])
        for region in regions:
            project_subnets += [Subnetwork(s) for s in regions[region].get('subnetworks', [])]
        request = subnets.list_next(request, subnets_list)
    return project_subnets

def list_subnetworks_without_logging(project_id, compute_api=None):
    """List all subnets in a project that do not have logging enabled."""
    return [subnet for subnet in list_subnetworks(project_id , compute_api) if not subnet.logging_enabled]

def create_no_logging_csv(project_network_resource_nologging, output_path):

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(('project_id', 'vpc', 'region', 'resource_name', 'resource_type', 'logging_enabled'))
        for project, networking in project_network_resource_nologging.items():
            for fw in networking['firewalls']:
                writer.writerow((project, fw.vpc, '', fw.name, 'firewall', fw.logging_enabled))
            for subnet in networking['subnets']:
                writer.writerow((project, subnet.vpc, subnet.region, subnet.name, 'subnet', subnet.logging_enabled))


def create_no_logging_json(project_network_resource_nologging, output_path):
    
    nologging_to_json = []
    
    for project, networking in project_network_resource_nologging.items():
        prj_json = {
            'project_id': project,
            'firewalls': None,
            'subnets': None}
        
        firewalls_json = []
        for fw in networking['firewalls']:
            firewalls_json.append({
                'vpc': fw.vpc,
                'resource_name': fw.name,
                'logging_enabled': fw.logging_enabled})
        prj_json['firewalls'] = firewalls_json

        subnets_json = []    
        for subnet in networking['subnets']:
            subnets_json.append({
                'vpc': subnet.vpc,
                'region': subnet.region,
                'resource_name': subnet.name,
                'logging_enabled': subnet.logging_enabled})
        prj_json['subnets'] = subnets_json
    
        nologging_to_json.append(prj_json)
    
    with open(output_path, 'w', newline='') as jsonfile:
        json.dump(nologging_to_json, jsonfile, indent=4, sort_keys=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List networking constructs in a GCP folder.')

    parser.add_argument('-q', action='store_true', dest='quiet',
                    help='Do not print list to stdout.')

    parser.add_argument('folder_number', action='store',
                    help='GCP folder to search projects for selected resources.')
    parser.add_argument('--output_csv_path', action='store', dest='output_csv_path',
                    help='Path and filename for CSV file output.')
    parser.add_argument('--output_json_path', action='store', dest='output_json_path',
                    help='Path and filename for JSON file output.')
    
    args = parser.parse_args()

    folder_number = args.folder_number
    projects = list_folder_projects(folder_number)
    service_usage_api = googleapiclient.discovery.build('serviceusage', 'v1')
    computeapi_enabled_projects = [p for p in projects if project_has_compute_api_enabled(p.project_number, service_usage_api)]
    

    project_network_resource_nologging = {}
    compute_api = googleapiclient.discovery.build('compute', 'v1')
    for project in computeapi_enabled_projects:
        project_id = project.project_id
        fws = list_firewalls_without_logging(project_id , compute_api)
        subnets = list_subnetworks_without_logging(project_id , compute_api)
        if len(fws) > 0 or len(subnets) > 0:
            project_network_resource_nologging[project_id] = {'firewalls': fws, 'subnets': subnets}

    if args.output_csv_path is not None:
        create_no_logging_csv(project_network_resource_nologging, args.output_csv_path)
    
    if args.output_json_path is not None:
        create_no_logging_json(project_network_resource_nologging, args.output_json_path)
    
    if not args.quiet:
        for project, networking in project_network_resource_nologging.items():
            print('\n------------------------------\n', project, '\n------------------------------')
            print(':FIREWALLS:')
            for firewall in networking['firewalls']:
                print(firewall)
            print('\n:SUBNETS:')
            for subnet in networking['subnets']:
                print(subnet)
