# xopera-rest-api benchmarking tool
Client for xopera-rest-api benchmarking
## Usage
```python
from client import benchmark
benchmark(n=3, url='http://154.48.185.209:5000', csar_dir='blueprints', csar_name='CSAR_benchmarking-nginx.zip',
              results_dir='results', timeout=300)
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