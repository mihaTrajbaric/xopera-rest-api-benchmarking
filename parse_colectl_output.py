import csv

# this script transforms command output in txt file to csv
# $ collectl -scmd -oT
filename = 'benchmark_154.48.185.209:5000_3_CSAR_benchmarking-nginx.zip_2020-08-21 12:29:44.641194-system_resurces.txt'
results_dir = 'results'

with open(f'{results_dir}/{filename}', 'r') as file:
    spamreader = csv.reader(file, delimiter=' ', quotechar='|')
    headers = ['Time', 'cpu', 'sys', 'inter', 'ctxsw', 'Free', 'Buff', 'Cach', 'Inac', 'Slab', 'Map', 'KBRead', 'Reads',
               'KBWrit', 'Writes']
    with open(f'{results_dir}/{filename[:-4]}.csv', 'w') as output_file:
        spamwriter = csv.writer(output_file, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(headers)
        for row in spamreader:

            # filter empty values
            row = list(filter(None, row))

            row_string = ', '.join(row)
            if '#' not in row_string:
                spamwriter.writerow(row)


