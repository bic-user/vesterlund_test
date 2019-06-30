
import os
import argparse
import sqlite3
import numpy as np

PORT = '8080'
LOCATION = 'http://127.0.0.1'
DB_PATH = 'sqlite_db'
RANDOMIZED_OPPONENT_NAME = 'gAjIz8p7LA'

RANDOMIZED_OPPONENT_MEAN_TIME = 3.5
RANDOMIZED_OPPONENT_STD_TIME = 1.0

MAX_COMPLETED_HITS = 400  # if each example takes 0.3 seconds
SECONDS = 300

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


def serialize_timings(timings):
    timings_str = ['%.3f' % x for x in timings]
    return '|'.join(timings_str)


def deserialize_timings(line):
    timings_str = line.split('|')
    return [float(x) for x in timings_str]


DB_COLUMN_NAME = 'name'
DB_COLUMNS_INT = ['round1', 'round2', 'round1_started', 'round2_started', 'round1_scenario', 'round2_scenario',
                  'round1_correct', 'round2_correct', 'round1_faster', 'round2_faster', 'round1_solved',
                  'round2_solved', 'idx']
DB_COLUMNS_FLOAT = ['earned', 'round_start', 'hit_start']
DB_COLUMNS_TEXT = ['round1_opponent', 'round2_opponent', 'round1_timings', 'round2_timings', 'round2_mode', 'ip']
DB_COLUMNS = [DB_COLUMN_NAME]
DB_COLUMNS.extend(DB_COLUMNS_INT)
DB_COLUMNS.extend(DB_COLUMNS_FLOAT)
DB_COLUMNS.extend(DB_COLUMNS_TEXT)


def column2list(col):
    assert len(col) == len(DB_COLUMNS)
    d = {k: v for k, v in zip(DB_COLUMNS, col)}
    for name in ['round1_timings', 'round2_timings']:
        if d[name]:
            d[name] = deserialize_timings(d[name])
    return d


def _create_testers_db():
    os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('CREATE TABLE testers ({} TEXT PRIMARY KEY)'.format(DB_COLUMN_NAME))
    # integers
    for name in DB_COLUMNS_INT:
        c.execute("ALTER TABLE testers ADD COLUMN '{}' INTEGER".format(name))

    # floats
    for name in DB_COLUMNS_FLOAT:
        c.execute("ALTER TABLE testers ADD COLUMN '{}' REAL".format(name))

    # strings
    for name in DB_COLUMNS_TEXT:
        c.execute("ALTER TABLE testers ADD COLUMN '{}' TEXT".format(name))
    conn.commit()
    return conn, c


def main():
    args = parse_args()
    if args.action == 'db':

        conn, c = _create_testers_db()
        for i in range(TEST_SCENARIOS_NUM):
            timings1 = np.random.randn(
                MAX_COMPLETED_HITS, ) * RANDOMIZED_OPPONENT_STD_TIME + RANDOMIZED_OPPONENT_MEAN_TIME
            timings2 = np.random.randn(
                MAX_COMPLETED_HITS, ) * RANDOMIZED_OPPONENT_STD_TIME + RANDOMIZED_OPPONENT_MEAN_TIME
            timings1[np.where(timings1) <= 0.1] = 0.1
            timings2[np.where(timings2) <= 0.1] = 0.1

            try:
                name = '%s%d' % (RANDOMIZED_OPPONENT_NAME, i)
                c.execute("INSERT INTO testers (name, round1, round2, round1_started, round2_started, round1_scenario, "
                          "round2_scenario, round1_timings, round2_timings) VALUES ('{}', 1, 1, 1, 1, {}, {}, '{}', '{}')".format(
                    name, i, i, serialize_timings(timings1), serialize_timings(timings2)))
            except sqlite3.IntegrityError:
                print('[%s] already exist' % name)
        conn.commit()
        conn.close()

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
