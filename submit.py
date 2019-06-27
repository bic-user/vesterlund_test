import time
import random
from tinydb import TinyDB, Query

from test_data import *

submit_body = '''<html><title>Vesterlund test</title>
<style>
body {{padding: 16px; font-family: sans-serif; font-size: 14px; color: #444}}
div {{
    background: white;
    position: relative;
    width: 100%;
    height: 100%;
}}
input {{font-size: 14px; padding: 8px 12px; outline: none; border: 1px solid #ddd}}
p {{padding: 12px}}
button {{background: #28d; padding: 9px 14px; border: none; outline: none;
        color: #fff; font-size: 14px; border-radius: 4px; cursor: pointer}}
button:hover {{box-shadow: 0 1px 2px rgba(0,0,0,.15); opacity: 0.9;}}
button:active {{background: #29f;}}
button[disabled] {{opacity: 0.4; cursor: default}}
footer {{
background-color: #FFF;
position:fixed;
bottom: 0px;
width: 100%;
text-align: center;
}}
</style>
<body>

<script>
function q(selector) {{return document.querySelector(selector)}}
</script>

</body>

</html>
'''

class Submit:

    def __init__(self):
        self.db = TinyDB('db.json')

    def _get_opponent_for_scenario(self, scenario):
        query = Query()
        opponents = self.db.search(query.round1_scenario == scenario or query.round2_scenario == scenario)
        opponent_name = random.choice(opponents)['name']
        return opponent_name
  
    def on_get(self, req, res):

        name = req.params.get('name')

        assert name and len(name) > 0

        query = Query()
        account = self.db.search(query.name == name)

        assert len(account) == 1
        account = account[0]


        if (account['round1_started'] and not account['round1']) or (account['round2_start'] and not account['round2']):
            # in process of round
        elif (not account['round1_started']) or (not account['round2_started']):
            # starting round: insert round start time, hit start time, idx, selected test scenario, selected opponent, round mode,
            # earned, timing for the the given round, toggle flag
            idx = 0
            acc_update = {'round_start': time.time(), 'hit_start': time.time(),'idx': idx}
            scenario = random.randint(0, TEST_SCENARIOS_NUM)
            if (not account['round1_started']):
                acc_update['round1_scenario'] = scenario
                acc_update['round1_opponent'] = self._get_opponent_for_scenario(scenario)
                acc_update['earned'] = 0.0
                acc_update['round1_started'] = True
                acc_update['round1_timings'] = self.db.search(Query().name == '%s%d' % (RANDOMIZED_OPPONENT_NAME, scenario))[0]['round1_timings']
            else:
                while scenario == account['round1_scenario']:
                    scenario = random.randint(0, TEST_SCENARIOS_NUM)
                acc_update['round2_scenario'] = scenario
                acc_update['round2_mode'] = req.params.get('mode')
                if acc_update['round2_mode'] == 'tournament':
                    acc_update['round2_opponent'] = self._get_opponent_for_scenario(scenario)
                acc_update['round2_started'] = True
                acc_update['round2_timings'] = self.db.search(Query().name == '%s%d' % (RANDOMIZED_OPPONENT_NAME, scenario))[0]['round2_timings']

            self.db.update(acc_update, Query().name == name)
            

        res.content_type = 'text/html'
        res.body = submit_body
