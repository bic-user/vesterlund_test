login_body = '''<html><title>Vesterlund test</title>
<style>
body {padding: 16px; font-family: sans-serif; font-size: 14px; color: #444}
div {
    background: white;
    position: relative;
    width: 100%;
    height: 100%;
}
input {font-size: 14px; padding: 8px 12px; outline: none; border: 1px solid #ddd}
p {padding: 12px}
button {background: #28d; padding: 9px 14px; border: none; outline: none;
        color: #fff; font-size: 14px; border-radius: 4px; cursor: pointer}
button:hover {box-shadow: 0 1px 2px rgba(0,0,0,.15); opacity: 0.9;}
button:active {background: #29f;}
button[disabled] {opacity: 0.4; cursor: default}
footer {
background-color: #FFF;
position:fixed;
bottom: 0px;
width: 100%;
text-align: center;
}
</style>
<body>

<form>
<input id="text" type="text" size="30" placeholder="Enter your name" style="margin-top:5px">
<button id="button" name="login" style="margin-left:5px" style="margin-top:5px">Login</button>
</form>

<script>
function q(selector) {return document.querySelector(selector)}
q('#text').focus()
q('#button').addEventListener('click', function(e) {
    name = q('#text').value.trim()
    if (name) {
        window.location = '/mode?name=' + name
    }
    e.preventDefault()
    return false
})
</script>

</body>

</html>
'''

class Login:
    def on_get(self, req, res):
        res.content_type = 'text/html'
        res.body = login_body
