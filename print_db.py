from test_data import *
import sqlite3
import numpy as np


conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

users = c.execute('SELECT * FROM testers WHERE (round1=1 AND round2=1)').fetchall()

for u in users:
    ud = column2list(u)
    if not ud['name'].startswith(RANDOMIZED_OPPONENT_NAME):
        for i in [1, 2]:
            arr = np.array(ud['round%d_timings' % i][:ud['idx']])
            print('%s, round%d mean %f; std %f' % (ud['name'], i, np.mean(arr), np.std(arr)))

        print('%s\tearned:%.2f$\tmode in round2:%s' % (ud['name'], ud['earned'], ud['round2_mode']))

conn.close()
