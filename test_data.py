
import os
import argparse
import numpy as np
from tinydb import TinyDB


RANDOMIZED_OPPONENT_NAME = 'gAjIz8p7LA'

RANDOMIZED_OPPONENT_MEAN_TIME = 1.0
RANDOMIZED_OPPONENT_STD_TIME = 0.2

MAX_COMPLETED_HITS = 600 # if each example takes 0.3 seconds

TEST_SCENARIOS_PATH = 'test_scenarios.npz'
TEST_SCENARIOS_NUM = 10

test_scenarios = None
if os.path.isfile(TEST_SCENARIOS_PATH):
    test_scenarios = dict(np.load(TEST_SCENARIOS_PATH))
else:
    print('Create test scenarios!')


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--action', choices=['db', 'data'], required=True)
    args = ap.parse_args()
    return args


def main():
    args = parse_args()
    if args.action == 'db':
        db = TinyDB('db.json')
        db.purge()
        db.all()

        for i in range(TEST_SCENARIOS_NUM):
            timings1 = np.random.randn(MAX_COMPLETED_HITS,) * RANDOMIZED_OPPONENT_STD_TIME + RANDOMIZED_OPPONENT_MEAN_TIME
            timings2 = np.random.randn(MAX_COMPLETED_HITS,) * RANDOMIZED_OPPONENT_STD_TIME + RANDOMIZED_OPPONENT_MEAN_TIME
            timings1[np.where(timings1) <= 0.1] = 0.1 
            timings2[np.where(timings2) <= 0.1] = 0.1 
            db.insert({'name': '%s%d' % (RANDOMIZED_OPPONENT_NAME, i), 
                       'round1': True, 
                       'round2': True, 
                       'round1_started': True, 
                       'round2_started': True,
                       'round1_scenario': i,
                       'round2_scenario': i,
                       'round1_timings': timings1.tolist(),
                       'round2_timings': timings2.tolist()})
    elif args.action == 'data':
        scenarios = {}
        for i in range(TEST_SCENARIOS_NUM):
            scenarios['a_%d' % i] = np.random.randint(10, high=100, size=MAX_COMPLETED_HITS)
            scenarios['b_%d' % i] = np.random.randint(10, high=100, size=MAX_COMPLETED_HITS)
        np.savez(TEST_SCENARIOS_PATH, **scenarios)
    else:
        print('Unsupported action %s' % args.action)


if __name__ == '__main__':
    main() 
