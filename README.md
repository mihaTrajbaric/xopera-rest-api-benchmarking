# xopera-rest-api benchmarking tool
Client for [xopera-rest-api](https://github.com/SODALITE-EU/xopera-rest-api) benchmarking
## Usage
### Client
Client uploads blueprint to REST API, deploys, and undeploys  _n instances.
```python
from client import benchmark
benchmark(n=3, url='http://ip:5000', csar_dir='blueprints', csar_name='CSAR_benchmarking-nginx.zip',
          results_dir='results', timeout=300)
```

### Helper scripts
#### parse_colectl_output
This script can transform system resurces stacktrace, obtained with colectl tool `$ collectl -scmd -oT` and transform it to .csv format.
```python
from parse_colectl_output import parse_output
filename = 'benchmark_ip:5000_3_CSAR_benchmarking-nginx.zip_2020-08-21 12:29:44.641194-system_resurces.txt'
parse_output(filename, directory="results")
```
#### plot_data
This script can produce some  usefull plots from data, obtained from client and colectl,
```python
from plot_data import average_time_plot, n_of_parallel_instances_plot
from pathlib import Path
average_time_plot(input_dir=Path("results/openstack-local"), output_dir=Path('results/openstack-local/plots'))
n_of_parallel_instances_plot(input_dir=Path("results/openstack-local"), 
                             output_dir=Path('results/openstack-local/plots')) 
```

## Results dir
### File format
benchmark_[ip]\_[n]\_[csar_name]\_[timestamp]\_[log_type].json
### Results files
Each test produces several results files:
- _full.json
    - report of every deploy / undeploy job
- _summary.json
    - aggregated summary
- _system-resources.txt
    - stacktrace from xOpera VM
- _system-resources.csv
    - staktrace in csv format. Obtain with `parse_colectl_output.py`
