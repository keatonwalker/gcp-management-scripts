# GCP Scripts and API Client Toolss

## Script Authentication
The scripts and CLI assume GCP Application Default Credentials are set. Credentials can be set with `gcloud auth application-default login`


## network-resource-reporting.py
Tool to report on GCP network resources without logging enabled.

Example run command; `python network-resource-reporting.py <folder number> --output_csv_path "./subnets_and_firewalls_without_logging.csv"`

Replace `<folder number>` with GCP folder number to scan.

See `python network-resource-reporting.py -h` for other command line options

## Future additions
- Add the ability to patch update resources to enable logging.
- Other exciting and helpful tools using the GCP APIs.