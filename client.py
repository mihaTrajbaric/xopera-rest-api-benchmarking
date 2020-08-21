import requests
import urllib3
import uuid
import time
import datetime
import json
from multiprocessing import Pool


def monitor(url, session_token, timeout=300):
    time_start = time.time()
    resp = None
    while time.time() - time_start < timeout:
        resp = requests.get(f"{url}/info/status?token={session_token}")

        if resp.json()['state'] != 'running':
            return True, resp

        time.sleep(3)

    return False, resp


def parse_log(log_json: dict):
    logs_json = {k: v for d in log_json for k, v in d.items()}
    log_timestamps = list(logs_json.keys())
    key = log_timestamps[0]
    log = logs_json[key]
    timestamp_start = str_to_timestamp(log['timestamp_start'])
    timestamp_end = str_to_timestamp(log['timestamp_end'])
    duration = timestamp_end - timestamp_start

    return {
        'session_token': log['session_token'],
        'timestamp_start': str(timestamp_start),
        'timestamp_end': str(timestamp_end),
        'duration': str(duration)
    }


def str_to_timestamp(timestamp_str: str, time_format='%Y-%m-%dT%H:%M:%S.%f'):
    return datetime.datetime.strptime(timestamp_str, time_format)


def str_to_timedelta(timedelta_str):
    t = datetime.datetime.strptime(timedelta_str, "%H:%M:%S.%f")
    # ...and use datetime's hour, min and sec properties to build a timedelta
    delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
    return delta


def average_runtime(parsed_logs):
    timedeltas = [str_to_timedelta(item["duration"]) for item in parsed_logs]
    average_timedelta = sum(timedeltas, datetime.timedelta(0)) / len(timedeltas)
    return average_timedelta


def file_to_inputs(file_path):
    return open(file_path, 'rb')


def upload_CSAR(CSAR_path, url='http://154.48.185.209:5000/'):
    files = {'CSAR': ('CSAR.zip', open(CSAR_path, 'rb'), 'application/zip')}
    r = requests.post(f'{url}/manage', files=files)

    if r.status_code != 200:
        raise ConnectionError('Could not upload CSAR to xOpera REST API')

    return r.json()['blueprint_token']


def delete_CSAR(blueprint_token, url='http://154.48.185.209:5000/'):
    r = requests.delete(f'{url}/manage/{blueprint_token}')
    if r.status_code != 200:
        raise ConnectionError(f'Could not delete CSAR: {r.text}')

    return True


def deploy_only(blueprint_token, inputs, url):
    files = {'inputs_file': ('inputs_file.yaml', inputs, 'application/x-yaml')}
    r = requests.post(f'{url}/deploy/{blueprint_token}', files=files)

    if r.status_code != 202:
        print(r.text)

    session_token = r.json()['session_token']

    return session_token


def undeploy_only(blueprint_token, inputs, url):
    files = {'inputs_file': ('inputs_file.yaml', inputs, 'application/x-yaml')}
    r = requests.delete(f'{url}/deploy/{blueprint_token}', files=files)

    if r.status_code != 202:
        print(r.text)

    session_token = r.json()['session_token']

    return session_token


def deploy(blueprint_token, inputs: str, url='http://154.48.185.209:5000/'):
    files = {'inputs_file': ('inputs_file.yaml', inputs, 'application/x-yaml')}
    r = requests.post(f'{url}/deploy/{blueprint_token}', files=files)

    if r.status_code != 202:
        print(r.text)
    # assert r.status_code == 202
    session_token = r.json()['session_token']

    done, resp_status = monitor(url=url, session_token=session_token)

    assert done

    resp_log = requests.get(f"{url}/info/log/deployment?session_token={session_token}")

    return parse_log(resp_log.json())


def undeploy(blueprint_token, inputs, url='http://154.48.185.209:5000/'):
    files = {'inputs_file': ('inputs_file.yaml', inputs, 'application/x-yaml')}
    r = requests.delete(f'{url}/deploy/{blueprint_token}', files=files)

    if r.status_code != 202:
        print(r.text)
    session_token = r.json()['session_token']

    done, resp_status = monitor(url=url, session_token=session_token)

    assert done

    resp_log = requests.get(f"{url}/info/log/deployment?session_token={session_token}")

    return parse_log(resp_log.json())


def benchmark(n: int, url, csar_path, results_path, timeout=30):
    timestamp_start = datetime.datetime.now()
    print('uploading CSAR...')
    blueprint_token = upload_CSAR(csar_path, url)

    print('deploying...')
    deploy_session_tokens = [deploy_only(blueprint_token, inputs=f'marker: {i}', url=url) for i in range(n)]

    print('Monitoring deploys...')
    for i, session_token in enumerate(deploy_session_tokens):
        done, resp_status = monitor(url=url, session_token=session_token, timeout=timeout)
        print(f'{i+1}. {"Done" if done else "Failed"}')
        if not done:
            print('failed', resp_status.json())

    print('Getting deploy_logs')
    deploy_logs = [parse_log(requests.get(f"{url}/info/log/deployment?session_token={session_token}").json()) for
                   session_token in deploy_session_tokens]

    print('Undeploying...')
    undeploy_session_tokens = [undeploy_only(blueprint_token, inputs=f'marker: {i}', url=url) for i in range(n)]

    print('Monitoring undeploys...')
    for i, session_token in enumerate(undeploy_session_tokens):
        done, resp_status = monitor(url=url, session_token=session_token, timeout=timeout)
        print(f'{i + 1}. {"Done" if done else "Failed"}')
        if not done:
            print('failed', resp_status.json())

    print('Getting undeploy_logs...')
    undeploy_logs = [parse_log(requests.get(f"{url}/info/log/deployment?session_token={session_token}").json()) for
                     session_token in undeploy_session_tokens]

    timestamp_stop = datetime.datetime.now()

    average_deploy_time = average_runtime(deploy_logs)
    average_undeploy_time = average_runtime(undeploy_logs)

    summary = {
        "n_of_parallel_deploys": n,
        "average_deploy_time": str(average_deploy_time),
        "average_undeploy_time": str(average_undeploy_time),
        "job_started": str(timestamp_start),
        "job_ended": str(timestamp_stop),
    }

    print(f"-------------------------\n"
          f"summary:\n"
          f"{json.dumps(summary, indent=2)}\n"
          f"-------------------------\n")
    full_logs = {
        "deploy": deploy_logs,
        "undeploy": undeploy_logs
    }
    print(f"Full logs:")
    print(json.dumps(full_logs, indent=2))

    json.dump(summary, open(f'{results_path}/benchmark_{n}_{str(timestamp_start)}-summary.json', 'w'), indent=2)
    json.dump(full_logs, open(f'{results_path}/benchmark_{n}_{str(timestamp_start)}-full.json', 'w'), indent=2)


def test_case(input):
    blueprint_token = '04ba6cea-d65f-418a-96e3-1fe835a1943d'
    url = 'http://localhost:5000'

    inputs = f'marker: {input}'
    deploy_response = deploy(blueprint_token=blueprint_token, inputs=inputs, url=url)
    undeploy_response = undeploy(blueprint_token=blueprint_token, inputs=inputs, url=url)
    return {
        'deploy': deploy_response,
        'undeploy': undeploy_response
    }


if __name__ == '__main__':
    url = 'http://localhost:5000'
    token = '04ba6cea-d65f-418a-96e3-1fe835a1943d'
    # blueprint_token = upload_CSAR('blueprints/CSAR-hello_inputs.zip', url=url)
    # delete_json = delete_CSAR(blueprint_token=token)
    # response = deploy(blueprint_token=token, inputs_file_path='blueprints/hello_inputs.yaml', url=url)
    # response = undeploy(blueprint_token=token, inputs_file_path='blueprints/hello_inputs.yaml', url=url)
    # print(response)
    # for i in range(3):
    #    print(json.dumps(test_case(i), indent=2))
    # pass
    # n = 5
    # p = Pool(n)
    # result = p.map(test_case, range(n))
    # print(json.dumps(result, indent=2))
    benchmark(n=1, url=url, csar_path='blueprints/CSAR-hello_inputs.zip', results_path='results')