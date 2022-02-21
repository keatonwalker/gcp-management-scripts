from network_resource_reporting import *

project_id = 'ut-udot-shared-vpc-prod'
fws = list_firewalls_without_logging(project_id)
for fw in fws:
    if 'gke' not in fw.name:
        print(fw.get_terraform_import_command())
        print('\n\n')
        print(fw.get_terraform_resource_template())