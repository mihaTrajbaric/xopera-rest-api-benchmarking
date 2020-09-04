from pathlib import Path
import glob
import json
from client import str_to_timedelta, str_to_timestamp
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter


class ResultMetadata:
    def __init__(self, results_file: Path):
        if not results_file.exists():
            raise FileExistsError("Results file does not exist!")
        self.full_filename = results_file
        self.parent = results_file.parent
        self.filename = results_file.name

        filename_parts = str(results_file.name).split('_')

        self.url = filename_parts[1]
        self.n = int(filename_parts[2])
        self.blueprint = filename_parts[3]
        self.timestamp = filename_parts[4]
        self.type = filename_parts[5].split('.')[0]

    def __str__(self):
        return f"Filename: {self.full_filename}\n" \
               f"Parent: {self.parent}\n" \
               f"filename: {self.filename}\n" \
               f"url: {self.url}\n" \
               f"n: {self.n}\n" \
               f"blueprint: {self.blueprint}\n" \
               f"timestamp: {self.timestamp}\n" \
               f"type: {self.type}\n"


def daterange_seconds(start_date, end_date):
    delta = datetime.timedelta(seconds=1)
    while start_date < end_date:
        yield start_date
        start_date += delta


def increment_counters(x, y, datetime_start, datetime_end):
    """
    increments every counter in y if corresponding x between datetime_start and datetime_end
    """
    assert len(x) == len(y)
    for i in range(len(y)):
        if datetime_start < x[i] < datetime_end:
            y[i] += 1


def plot_timedeltas(y, title: str, xlabel, ylabel, x=None, outdir: Path=None):
    if x is None:
        x = list(range(1, len(y)+1))

    zero = datetime.datetime(2018, 1, 1)
    time = [zero + t for t in y]
    df = pd.DataFrame({'n': x,
                       'Time': time})
    fig, ax = plt.subplots()

    fig.suptitle(title, fontsize=16)

    myFmt = DateFormatter("%H:%M:%S")
    ax.yaxis.set_major_formatter(myFmt)

    ax.plot(df['n'], df['Time'])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    plt.gcf().autofmt_xdate()

    if outdir:
        if not outdir.exists():
            outdir.mkdir(parents=True)
        plt.savefig(f'{outdir}/{title}.png')

    plt.show()


def plot_ints(x, y, title: str, xlabel, ylabel, outdir: Path=None):

    fig, ax = plt.subplots()

    fig.suptitle(title, fontsize=16)

    ax.plot(x, y)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if outdir:
        if not outdir.exists():
            outdir.mkdir(parents=True)
        plt.savefig(f'{outdir}/{title}.png')

    plt.show()


def average_time_plot(input_dir: Path, output_dir: Path=None):
    """
    Generates plot of average time vs n of parallel deploys
    """
    files = glob.glob(f"{input_dir}/*_summary.json")
    deploy_times = [None for i in range(len(files))]
    undeploy_times = [None for i in range(len(files))]
    for file in files:
        with open(file, 'r') as json_file:
            data = json.load(json_file)
            n = data['n_of_parallel_deploys']
            deploy_time = str_to_timedelta(data['average_deploy_time'])
            undeploy_time = str_to_timedelta(data['average_undeploy_time'])
            deploy_times[n-1] = deploy_time
            undeploy_times[n-1] = undeploy_time
    plot_timedeltas(deploy_times, title='Average deploy times', xlabel='n', ylabel='time (HH:MM:SS)', outdir=output_dir)
    plot_timedeltas(undeploy_times, title='Average undeploy times', xlabel='n', ylabel='time (HH:MM:SS)', outdir=output_dir)


def n_of_parallel_instances_plot(input_dir: Path, output_dir: Path=None):
    files = glob.glob(f"{input_dir}/*_full.json")
    for file in files:
        with open(file, 'r') as json_file:
            full_data = json.load(json_file)
        with open(file[:-9] + "summary.json", 'r') as json_file:
            summary_data = json.load(json_file)

        time_format = '%Y-%m-%d %H:%M:%S.%f'
        # extend interval to closest whole second (timestamp_start down, timestamp_end up)
        timestamp_start = str_to_timestamp(summary_data['job_started'], time_format).replace(microsecond=0)
        timestamp_end = str_to_timestamp(summary_data['job_ended'], time_format).replace(microsecond=0) + datetime.timedelta(seconds=1)

        x_axis = list(daterange_seconds(timestamp_start, timestamp_end))
        y_axis = [0 for _ in x_axis]

        for deploy_job in full_data['deploy']:
            datetime_start = str_to_timestamp(deploy_job['timestamp_start'], time_format) + datetime.timedelta(hours=2)

            datetime_end = str_to_timestamp(deploy_job['timestamp_end'], time_format) + datetime.timedelta(hours=2)
            increment_counters(x_axis, y_axis, datetime_start, datetime_end)

        for undeploy_job in full_data['undeploy']:
            datetime_start = str_to_timestamp(undeploy_job['timestamp_start'], time_format) + datetime.timedelta(hours=2)

            datetime_end = str_to_timestamp(undeploy_job['timestamp_end'], time_format) + datetime.timedelta(hours=2)
            increment_counters(x_axis, y_axis, datetime_start, datetime_end)

        plot_ints(x_axis, y_axis, title=f'Parallel jobs for N={summary_data["n_of_parallel_deploys"]}',
                  xlabel='time (HH:MM:SS)', ylabel='n', outdir=output_dir)


if __name__ == '__main__':
    average_time_plot(input_dir=Path("results/openstack-local"), output_dir=Path('results/openstack-local/plots'))
    n_of_parallel_instances_plot(input_dir=Path("results/openstack-local"), output_dir=Path('results/openstack-local'
                                                                                            '/plots')) 
