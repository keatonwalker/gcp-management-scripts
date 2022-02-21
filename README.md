# GCP Scripts and API Client Toolss

## Script Authentication
The scripts and CLI assume GCP Application Default Credentials are set. Credentials can be set with `gcloud auth application-default login`


## network_resource_reporting.py
Tool to report on GCP network resources without logging enabled.

Example run command; `python network_resource_reporting.py <folder number> --output_csv_path "./subnets_and_firewalls_without_logging.csv"`

Replace `<folder number>` with GCP folder number to scan.

See `python network_resource_reporting.py -h` for other command line options

Only searchs projects directly in `<folder number>` currently.

## Future additions
- Add the ability to patch update resources to enable logging.
- Resurvively search folders for projects.
- Other exciting and helpful tools using the GCP APIs.