from flask import *
import os
from hashlib import *
import openai
from tqdm import *
import json
import random
from flaskext.markdown import Markdown
import jwt
import time
secret_key = 'REMOVED'
secure_string = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
app = Flask(__name__)
Markdown(app)
openai.api_key = 'REMOVED'
temp_prompt = """
"""
temp_text = "hows your day?"
temp_tmpr = 0.5
temp_max = 3000
'''
print(correct[:10], len(correct))
print(wrong[:10], len(wrong))
'''
def secure_check(user):
    for i in user:
        if i not in secure_string:
            return False
    return True
def chat(prompt, text, tmpr, max):
    """向 ChatGPT提 交 提 示 (prompt)"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": rf"Text: {text}"},
        ],  # 提 示 (promp)
        temperature=float(tmpr),
        max_tokens=int(max),
    )
    return response
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/dictionary', methods=['GET', 'POST'])
def dictionary():
    if request.method == 'GET':
        if 'user' not in request.cookies:
            return render_template('dictionary.html', user_data='', response='')
        else:
            data=request.cookies.get('user')
            data1=jwt.decode(data, secret_key, algorithms=['HS256'])
            return render_template('dictionary.html', user_data=data1.pop('user_data'), response='')
    else:
        word=request.values.get('word')
        user_data=request.values.get('user_data')
        msg=f"{user_data}\nBase on my personal details(very important, don't make it to hard to understand for me), explain this word to me and say
it's meaning and give me an example sentence(and use some markdown to make it more clear):{word}"
        response=chat(temp_prompt, msg, temp_tmpr, temp_max)['choices'][0]['message']['content']
        hashvalue=md5(response.encode()).hexdigest()
        file=open(f'history/{hashvalue}', 'wb')
        file.write(response.encode())
        file.close()
        response = make_response(redirect(f'/history/@{hashvalue}'))
        return response
@app.route('/del')
def delqq():
    response = make_response(redirect('/dictionary'))
    response.delete_cookie('user')
    return response
@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'GET':
        if 'user' not in request.cookies:
            response = make_response(redirect('/login'))
            return response
        else:
            data=request.cookies.get('user')
            data1=jwt.decode(data, secret_key, algorithms=['HS256'])
            if data1.pop('exp')<=time.time():
                response = make_response(redirect('/login'))
                response.delete_cookie('user')
                return response
            else:
                return render_template('account.html', user_name=data1.pop('user_name'), user_data=data1.pop('user_data'))
    elif request.method == 'POST':
        data=request.cookies.get('user')
        data1=jwt.decode(data, secret_key, algorithms=['HS256'])
        word=request.form['word']
        username=data1.pop('user_name')
        file=open('users/'+username, 'wb')
        file.write(word.encode())
        file.close()
        response = make_response(redirect('/account'))
        data1={'user_name': username, 'user_data': open('users/'+username, 'rb').read().decode(), 'exp':int(time.time()) + 60*300}
        response.set_cookie('user', jwt.encode(data1, secret_key, algorithm='HS256').decode())
        return response
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        if secure_check(username)==False:
            return "<h1>Invalid Input</h1><h2><a href='login'>Login here</a></h2>"
        if os.path.isfile('pwd/'+username)==False:
            return "<h1>User doesn't exsist</h1><h2><a href='login'>Login
here</a></h2>"
        file=open('pwd/'+username, 'rb')
        pwd=file.read().decode()
        if md5(password.encode()+secret_key.encode()).hexdigest()!=pwd:
            return "<h1>密 碼 錯 誤 </h1><h2><a href='login'>Login here</a></h2>"
        else:
            response = make_response(redirect('/dictionary'))
            data1={'user_name': username, 'user_data': open('users/'+username, 'rb').read().decode(), 'exp':int(time.time()) + 60*60*72}
            response.set_cookie('user', jwt.encode(data1, secret_key, algorithm='HS256').decode())
        return response
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        repassword=request.form['repassword']
        if password!=repassword:
            return "<h1>Password doesn't match</h1><h2><a href='register'>Register here</a></h2>"
        if secure_check(username)==False:
            return "<h1>Invalid Input</h1><h2><a href='register'>Register
here</a></h2>"
        if os.path.isfile('pwd/'+username)==True:
            return "<h1>Username already been used</h1><h2><a href='register'>Register here</a></h2>"
        file=open('pwd/'+username, 'wb')
        file.write(md5(password.encode()+secret_key.encode()).hexdigest().encode())
        file.close()
        file=open('users/'+username, 'wb')
        file.write(b'I am a Whale')
        file.close()
        response = make_response(redirect('/login'))
        return response
@app.route('/history/@<id>')
def history(id):
    if secure_check(id)==False:
        response = make_response(redirect('/dictionary'))
        return response
    response=open(f'history/{id}', 'rb').read().decode()
    if 'user' not in request.cookies:
        return render_template('dictionary.html', user_data='', response=response)
    else:
        data=request.cookies.get('user')
        data1=jwt.decode(data, secret_key, algorithms=['HS256'])
        return render_template('dictionary.html', user_data=data1.pop('user_data'), response=response)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10100)
