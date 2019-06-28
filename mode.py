
from tinydb import TinyDB, Query

from message_body import *

mode_body = '''<html><title>Vesterlund test</title>
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
<div>
<p style="margin-left:5px">{}</p>
<p style="margin-left:5px">{}</p>
<p id="mode_selection">
<input type="radio" name="mode" id="tournament" value="tournament" checked>
<label for="tournament">Tournament</label>
<input type="radio" name="mode" id="piece" value="piece" style="margin-left:5px" {}>
<label for="piece">Piece-rate</label>
</p>
<button id="button" name="start" style="margin-left:5px" style="margin-top:5px">Start</button>
</div>

<script>
function q(selector) {{return document.querySelector(selector)}}
q('#button').focus()
q('#button').addEventListener('click', function(e) {{
    window.location = '/submit' + window.location.search + '&mode=' + get_mode()
    e.preventDefault()
    return false
}})

function get_mode() {{
    mode = ""
    if (q('#tournament').checked) {{
        mode = "tournament" 
    }} else if (q('#piece').checked) {{
        mode = "piece"
    }}
    return mode
}}
</script>

</body>
</html>
'''

class SelectMode:

    def __init__(self):
        self.db = TinyDB('db.json')

    def on_get(self, req, res):
        res.content_type = 'text/html'
        name = req.params.get('name')
        if not name:
            res.body = message_body.format('Empty name')
            return

        query = Query()
        account = self.db.search(query.name == name)
        if not account:
            self.db.insert({'name': name, 'round1': False, 'round2': False, 'round1_started': False, 'round2_started': False})
            res.body = mode_body.format('', 'Tournament mode preselected for Round 1:', 'disabled')
        else:
            assert(len(account) == 1)
            account = account[0]
            print('in mode')
            print(account['round1'])
            print(account['round2'])
            if not account['round1']:
                res.body = mode_body.format('', 'Tournament mode preselected for Round 1:', 'disabled')
            elif not account['round2']:
                msg = '%d submitted in Round 1; %d were correct; %d were faster than opponent. You earned %.2f$' % \
                      (account['round1_solved'], account['round1_correct'], account['round1_faster'], account['earned'])
                res.body = mode_body.format(msg, 'Select the mode for Round 2:', '')
            else:
                earned = account['earned']
                res.body = message_body.format('You already finished the test. You earned %.2f' % earned)
