"""
Summarise details of a raw trace from the Austin python profiler https://github.com/P403n1x87/austin

For example show for each thread the total elapsed/cpu time and allocated/deallocated memory

Helps with narrowing down which parts of a large trace to investigate (e.g. by looking at the flame graph)
"""
import argparse
import pprint
import time
from collections import defaultdict

# pip install austin-python
from austin.stats import AustinFileReader, InvalidSample, MetricType, Sample



def analyse_austin_trace(filename):
    print(f'Input: {filename}')
    with AustinFileReader(filename) as fin:
        print(f'Metadata: {pprint.pformat(fin.metadata)}')

        # TODO: support other cases; for now this only works on a --full trace for simplicity
        # In that case MetricType.from_mode returns None (which means all 4: cpu, wall time, mem alloc, mem dealloc)
        metric_type = MetricType.from_mode(fin.metadata["mode"])
        if metric_type is not None:
            raise NotImplementedError('This script currently only supports full traces')

        # Store totals by thread
        totals = defaultdict(lambda: defaultdict(int))

        start_time = time.time()
        print('Analysing', end='')
        n_lines = 0
        for line in fin:
            n_lines += 1
            if n_lines % 10000 == 0:
                # Show progress
                print('.', end='', flush=True)
            try:
                # Returns a list of Sample instances, one for each metric
                # which for `--full` is [cpu time, wall time, memalloc, memdealloc]
                samples = Sample.parse(line, metric_type)
                # Accumulate totals by thread
                pid_tid = f'P{samples[0].pid};T{samples[0].thread}'
                for i, label in enumerate(['cpu_time_micros', 'wall_time_micros', 'mem_alloc_KB', 'mem_dealloc_KB']):
                    totals[pid_tid][label] += samples[i].metric.value
            except InvalidSample:
                continue

        print('')  # newline after the progress dots
        end_time = time.time()
        print(f'Completed analysis in {end_time - start_time:.1f} seconds\n')


    print('Totals per thread:')
    for pid_tid, stats in sorted(totals.items()):
        print(
            f"{pid_tid:<12}"
            f"   {stats['wall_time_micros']/1000000: 6.1f}s elapsed"
            f"   {stats['cpu_time_micros']/1000000: 6.3f}s CPU"
            f"   {stats['mem_alloc_KB']/1024:+7.1f}MB allocated"
            f"   ({stats['mem_dealloc_KB']/1024: 7.1f}MB deallocated)"
        )


def main():
    parser = argparse.ArgumentParser(description='Provide thread-level summaries for an Austin profile trace')
    parser.add_argument('input', help='File name of Austin output profile (normal raw text-based file with 1 sample per line)')
    args = parser.parse_args()
    analyse_austin_trace(filename=args.input)


if __name__ == '__main__':
    main()
