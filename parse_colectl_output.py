import csv

# this script transforms command output in txt file to csv
# $ collectl -scmd -oT


def parse_output(filename: str, directory: str):
    with open(f'{directory}/{filename}', 'r') as file:
        spamreader = csv.reader(file, delimiter=' ', quotechar='|')
        headers = ['Time', 'cpu', 'sys', 'inter', 'ctxsw', 'Free', 'Buff', 'Cach', 'Inac', 'Slab', 'Map', 'KBRead', 'Reads',
                   'KBWrit', 'Writes']
        with open(f'{directory}/{filename[:-4]}.csv', 'w') as output_file:
            spamwriter = csv.writer(output_file, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(headers)
            for row in spamreader:

                # filter empty values
                row = list(filter(None, row))

                row_string = ', '.join(row)
                if '#' not in row_string:
                    spamwriter.writerow(row)


if __name__ == '__main__':
    filename = 'benchmark_ip:5000_3_CSAR_benchmarking-nginx.zip_2020-08-21 12:29:44.641194-system_resurces.txt'
    results_dir = 'results'
    parse_output(filename, directory=results_dir)
