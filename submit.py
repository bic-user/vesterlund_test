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

<p style="margin-left:5px">{}</p>

<form style="margin-left:10px">
<font size="6">{} + {} = </font> 
<input style="font-size:25px;" id="text" type="text" onkeypress='validate(event)' size="4" style="margin-top:5px">
<button id="button" name="enter" style="margin-left:5px">Submit</button>
</form>

<p style="margin-left:5px">{} seconds left...</p>

<script>
function q(selector) {{return document.querySelector(selector)}}
q('#text').focus()
q('#button').addEventListener('click', function(e) {{
    val = q('#text').value.trim()
    if (val) {{
        window.location = '/submit?name=' + window.location.search.split("name=")[1].split("&")[0] + '&val=' + val
    }}
    e.preventDefault()
    return false
}})

function validate(evt) {{

  if (evt.which == 13) {{
      val = q('#text').value.trim()
      if (val) {{
          window.location = '/submit?name=' + window.location.search.split("name=")[1].split("&")[0] + '&val=' + val
      }}
      e.preventDefault()
      return false
  }}

  var theEvent = evt || window.event;

  // Handle paste
  if (theEvent.type === 'paste') {{
      key = event.clipboardData.getData('text/plain');
  }} else {{
  // Handle key press
      var key = theEvent.keyCode || theEvent.which;
      key = String.fromCharCode(key);
  }}
  var regex = /[0-9]|\./;
  if( !regex.test(key) ) {{
    theEvent.returnValue = false;
    if(theEvent.preventDefault) theEvent.preventDefault();
  }}
}}

</script>

</body>

</html>
'''

class Submit:

    def __init__(self):
        self.db = TinyDB('db.json')

    def _get_opponent_for_scenario(self, scenario):
        query = Query()
        opponents = self.db.search(((query.round1_scenario == scenario) & query.round1) | \
                                   ((query.round2_scenario == scenario) & query.round2))
        opponent_name = random.choice(opponents)['name']
        return opponent_name

    def _get_time_left(self, name):
        round_start = self.db.search(Query().name == name)[0]['round_start']
        time_left = int(round(180.0 - time.time() + round_start))
        return time_left

    def _get_time_for_hit(self, name):
        account = self.db.search(Query().name == name)[0]
        time_spent = '%.1f' % (time.time() - account['hit_start'])
        return time_spent
  
    def on_get(self, req, res):

        name = req.params.get('name')

        assert name and len(name) > 0

        query = Query()
        account = self.db.search(query.name == name)

        assert len(account) == 1
        account = account[0]

        in_round1 = account['round1_started'] and not account['round1']
        in_round2 = account['round2_started'] and not account['round2']
        round1_not_started = (not account['round1_started']) and (not account['round1'])
        round2_not_started = (not account['round2_started']) and (not account['round2'])

        if in_round1 or in_round2:
            # in process of round
            suffix = '1' if in_round1 else '2'
            scenario = account['round%s_scenario' % suffix]
            is_tournament = in_round1 or (in_round2 and acc_update['round2_mode'] == 'tournament')
            idx = account['idx']
            time_left = self._get_time_left(name)

            if time_left < 0:
                acc_update = {'round%s_solved' % suffix: idx, 'round%s' % suffix: True}
                self.db.update(acc_update, Query().name == name)        
                if in_round1:
                    # go to round 2
                    pass
                else:
                    # say thanks 
                    pass
                return

            val = req.params.get('val')
            try:
                val_int = int(val)
            except ValueError:
                val_int = -1
            earned = account['earned']
            hit_time = self._get_time_for_hit(name)
            expected_sum = test_scenarios['a_%d' % scenario][idx] + test_scenarios['b_%d' % scenario][idx]
            if val_int == expected_sum:
                if is_tournament:
                    opponent_name = account['round%s_opponent' % suffix]
                    opponent = self.db.search(Query().name == opponent_name)[0]
                    if opponent['round1_scenario'] == scenario:
                        opponent_timings = opponent['round1_timings']
                    elif opponent['round2_scenario'] == scenario:
                        opponent_timings = opponent['round2_timings']
                    else:
                        raise
                    if hit_time > opponent_timings[idx]:
                        prev_result = 'You were correct, but your opponent was faster. Previous hit took %s, your balance %.2f$' % (hit_time, earned)
                    else:
                        earned += 0.1
                        prev_result = 'You were correct and outperform the opponent. Previous hit took %s, you earned 0.1$, current balance %.2f$' % (hit_time, earned)
                else:
                    earned += 0.05
                    prev_result = 'You were correct! Previous hit took %s, you earned 0.05$, current balance %.2f$' % (hit_time, earned)
            else:
                prev_result = 'You were wrong! Previous hit took %s, your balance %.2f$' % (hit_time, earned)
            timings = account['round%s_timings' % suffix]
            timings[idx] = hit_time
            idx += 1
            acc_update = {'idx': idx, 'hit_start': time.time(), 'round%s_timings' % suffix: timings, 'earned': earned}
        elif round1_not_started or round2_not_started:
            # starting round: insert round start time, hit start time, idx, selected test scenario, selected opponent, round mode,
            # earned, timing for the the given round, toggle flag
            idx = 0
            acc_update = {'round_start': time.time(), 'hit_start': time.time(),'idx': idx, 'round1_scenario': -1, 'round2_scenario': -1}
            scenario = random.randint(0, TEST_SCENARIOS_NUM)
            if round1_not_started:
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
            prev_result = ''
            time_left = 300 
            
        self.db.update(acc_update, Query().name == name)        

        res.content_type = 'text/html'
        res.body = submit_body.format(prev_result,
                                      test_scenarios['a_%d' % scenario][idx],
                                      test_scenarios['b_%d' % scenario][idx],
                                      time_left)
