import time
import random
import falcon
import sqlite3

from test_data import *
from message_body import *

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

  if (evt.which == 8 || evt.which == 46) {{
      return false
  }}

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

def _get_submitted_val(request):
    val = request.params.get('val')
    try:
        val_int = int(val)
    except ValueError:
        val_int = -1
    return val_int


class Submit:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)

    def __del__(self):
        self.conn.close()

    def _get_opponent_for_scenario(self, scenario):
        c = self.conn.cursor()
        opponents = c.execute('SELECT * FROM testers WHERE ((round1_scenario={} AND round1=1) OR '
                                   '(round2_scenario={} AND round2=1))'.format(scenario, scenario)).fetchall()
        opponent_name = random.choice(opponents)[0]
        return opponent_name

    def _get_time_left(self, name):
        c = self.conn.cursor()
        round_start = column2list(c.execute('SELECT * FROM testers WHERE name="{}"'.format(name)).fetchone())['round_start']
        time_left = int(round(SECONDS - time.time() + round_start))
        return time_left

    def _get_time_for_hit(self, name):
        c = self.conn.cursor()
        account = column2list(c.execute('SELECT * FROM testers WHERE name="{}"'.format(name)).fetchone())
        time_spent = time.time() - account['hit_start']
        return time_spent

    def _handle_no_time_left(self, name, res, suffix, in_round1, account):
        c = self.conn.cursor()
        c.execute('UPDATE testers SET round{}_solved={}, round{}=1 WHERE name="{}"'.format(suffix, account['idx'], suffix, name))
        self.conn.commit()
        if in_round1:
            # go to round 2
            raise falcon.HTTPMovedPermanently('%s:%s/mode?name=%s' % (LOCATION, PORT, name))
        else:
            # say thanks
            res.body = message_body.format('You finished the test. Thanks! Your balance is %.2f' % account['earned'])

    def _handle_in_round(self, name, account, req, res, in_round1, in_round2):
        # define which round exactly
        suffix = '1' if in_round1 else '2'
        scenario = account['round%s_scenario' % suffix]
        is_tournament = in_round1 or (in_round2 and account['round2_mode'] == 'tournament')
        idx = account['idx']
        time_left = self._get_time_left(name)

        c = self.conn.cursor()
        if time_left < 0:
            self._handle_no_time_left(name, res, suffix, in_round1, account)
        else:
            val = _get_submitted_val(req)
            earned = account['earned']
            hit_time = self._get_time_for_hit(name)
            expected_sum = test_scenarios['a_%d' % scenario][idx] + test_scenarios['b_%d' % scenario][idx]
            acc_update = ''
            if val == expected_sum:
                acc_update = '%s, round%s_correct=%d' % (acc_update, suffix, account['round%s_correct' % suffix] + 1)
                if is_tournament:
                    opponent_name = account['round%s_opponent' % suffix]
                    opponent = column2list(c.execute('SELECT * FROM testers WHERE name="{}"'.format(opponent_name)).fetchone())
                    if opponent['round1_scenario'] == scenario:
                        opponent_timings = opponent['round1_timings']
                    elif opponent['round2_scenario'] == scenario:
                        opponent_timings = opponent['round2_timings']
                    else:
                        raise
                    if hit_time > opponent_timings[idx]:
                        prev_result = 'You were correct, but your opponent was faster. Previous hit took %.2f, your balance %.2f$' % (
                        hit_time, earned)
                    else:
                        earned += 0.1
                        prev_result = 'You were correct and outperform the opponent. Previous hit took %.2f, you earned 0.1$, current balance %.2f$' % (
                        hit_time, earned)
                        acc_update = '%s, round%s_faster=%d' % (acc_update, suffix, account['round%s_faster' % suffix] + 1)
                else:
                    earned += 0.05
                    prev_result = 'You were correct! Previous hit took %.2f, you earned 0.05$, current balance %.2f$' % \
                                  (hit_time, earned)
                    acc_update = '%s, round%s_faster=%d' % (acc_update, suffix, account['round%s_faster' % suffix] + 1)
            else:
                prev_result = 'You were wrong! Previous hit took %.2f, your balance %.2f$' % (hit_time, earned)
            timings = account['round%s_timings' % suffix]
            timings[idx] = hit_time
            idx += 1

            acc_update = '{}, idx={}, hit_start={}, round{}_timings="{}", earned={}'.format(
                acc_update, idx, time.time(), suffix, serialize_timings(timings), earned)
            c.execute('UPDATE testers SET {} WHERE name="{}"'.format(acc_update.strip(', '), name))
            self.conn.commit()
            res.body = submit_body.format(prev_result,
                                          test_scenarios['a_%d' % scenario][idx],
                                          test_scenarios['b_%d' % scenario][idx],
                                          time_left)

    def _start_round(self, name, account, req, res, round1_not_started):
        idx = 0
        acc_update = 'round_start={}, hit_start={}, idx={}'.format(time.time(), time.time(), idx)
        scenario = random.randint(0, TEST_SCENARIOS_NUM)
        c = self.conn.cursor()
        if round1_not_started:
            timings = column2list(c.execute('SELECT * FROM testers WHERE name="{}"'.format(
                '%s%d' % (RANDOMIZED_OPPONENT_NAME, scenario))).fetchone())['round1_timings']
            acc_update = '{}, round1_scenario={}, round1_opponent="{}", round1_correct=0, round1_faster=0, earned=0, ' \
                         'round1_started=1, round1_timings="{}"'.format(
                acc_update, scenario, self._get_opponent_for_scenario(scenario), serialize_timings(timings))
        else:
            while scenario == account['round1_scenario']:
                scenario = random.randint(0, TEST_SCENARIOS_NUM)

            timings = column2list(c.execute('SELECT * FROM testers WHERE name="{}"'.format(
                '%s%d' % (RANDOMIZED_OPPONENT_NAME, scenario))).fetchone())['round2_timings']
            acc_update = '{}, round2_scenario={}, round2_correct=0, round2_faster=0, round2_mode="{}", ' \
                         'round2_opponent="{}", round2_started=1, round2_timings="{}"'.format(
                acc_update, scenario, req.params.get('mode'), self._get_opponent_for_scenario(scenario),
                serialize_timings(timings))
        c.execute('UPDATE testers SET {} WHERE name="{}"'.format(acc_update, name))
        self.conn.commit()

        res.body = submit_body.format('',
                                      test_scenarios['a_%d' % scenario][idx],
                                      test_scenarios['b_%d' % scenario][idx],
                                      SECONDS)

    def on_get(self, req, res):

        name = req.params.get('name')
        res.content_type = 'text/html'

        if not name or len(name) == 0:
            res.body = message_body.format('Empty name')
            return

        c = self.conn.cursor()
        account = column2list(c.execute('SELECT * FROM testers WHERE name="{}"'.format(name)).fetchone())

        in_round1 = account['round1_started'] and not account['round1']
        in_round2 = account['round2_started'] and not account['round2']
        round1_not_started = (not account['round1_started']) and (not account['round1'])
        round2_not_started = (not account['round2_started']) and (not account['round2'])

        if in_round1 or in_round2:
            self._handle_in_round(name, account, req, res, in_round1, in_round2)
        elif round1_not_started or round2_not_started:
            self._start_round(name, account, req, res, round1_not_started)
        elif account['round1'] and account['round2']:
            res.body = message_body.format('Test is finished. Balance %.2f$' % account['earned'])
        else:
            c = self.conn.cursor()
            c.execute('DELETE FROM testers WHERE name="{}"'.format(name))
            self.conn.commit()
