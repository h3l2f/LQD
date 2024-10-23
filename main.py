from flask import *
import sqlside
import session_gen as sg
import time
from flask_cors import CORS
from datetime import datetime
from bs4 import BeautifulSoup
from markdown import markdown as md

app = Flask(__name__,template_folder='templates')
CORS(app)

def checkCookie(cookie):
    s = sqlside.execute(f"select username,alive from session where sid='{cookie}'")
    if (len(s) >= 2) or (len(s) == 0): return (False, "/logout?auth=fail")
    user = s[0][0]
    if time.time() > s[0][1]:
        return (False, "/logout?auth=fail")
    data = sqlside.execute(f"select name,accountType,avatarImageLink,username from loginInformation where username='{user}'")
    if (len(data) == 0): return (False, "/logout?auth=fail")

    return (True, data)


def login(user, passwd):
    s = None
    try:
        s = sqlside.execute(f"SELECT username,password,name,accountType FROM loginInformation where `username` = '{user}' and `password` = '{passwd}'")
    except Exception as e:
        if type(e).__name__ == "InterfaceError":
            return "NOT WORKING HERE HEHE!"
        elif type(e).__name__ == "ProgrammingError":
            return "INVALID USERNAME OR PASSWORD!"
        else: 
            print(type(e).__name__)
            return f"SOMETHING WENT WRONG!<br>HERE IS THE OUTPUT:<br>#===================#<br>{type(e).__name__}: {e}<br>#===================#"
    else:
        if (len(s) == 0) or (len(s) >=2): return "INVALID USERNAME OR PASSWORD!"
        return s[0]

@app.route("/")
def hp():
    return render_template("index.html")

@app.route('/login/',methods=["GET","POST"])
def lg():
    if request.method == "GET":
        ch = checkCookie(request.cookies.get('sid'))
        if ch[0] == False: 
            return render_template("login.html")
        else:
            s = sqlside.execute(f"select username,alive from session where sid='{request.cookies.get('sid')}'")
            if (len(s) >= 2) or (len(s) == 0): return render_template("login.html")
            else: return redirect("/",code=302)
    else:
        user = request.form.get("user")
        passwd = request.form.get("passwd")
        s = login(user,passwd)
        if type(s) == str:
            return render_template("login.html",err=True,error=s)
        else:
            cookie = sg.gen() 
            resp = make_response(redirect("/",code=302))
            s = f"insert into session values ('{cookie}',{time.time()+(15*86400)},'{user}')"
            s = sqlside.execute(s,type="insert")
            print(s)
            resp.set_cookie('sid', cookie, max_age=(15*86400),path="/")
            
            return resp

@app.route("/logout")
def logout():
    reason = request.args.get("auth")
    sqlside.execute(f"UPDATE session set alive = 0 where sid='{request.cookies.get('sid')}'",type="update")
    resp = make_response(redirect(f"/{f'?auth={reason}' if reason else ''}",code=302))
    resp.delete_cookie("sid")
    return resp

@app.route("/admin/delete/<catelogy>/<id>",methods=["DELETE"])
def deleteItem(catelogy,id):
    ch = checkCookie(request.cookies.get('sid'))
    if ch[0] == False: return redirect(ch[1],code=302)
    data = ch[1]
    if data[0][1] != "admin": return redirect("/?auth=forbidden",code=302)
    return f"{catelogy} & {id}"

@app.route("/admin/",methods=["GET","POST"])
def admin():
    if request.method == "GET":
        ch = checkCookie(request.cookies.get('sid'))
        if ch[0] == False: return redirect(ch[1],code=302)
        data = ch[1]
        user = data[0][0]
        if data[0][1] != "admin": return redirect("/?auth=forbidden",code=302)
        return render_template("admin.html",name=data[0][0],username=user,avtLink= data[0][2] if data[0][2] != '-1' else f"https://placehold.co/45x45/0040ff/white?text={user[0]}")
    else:

        ch = checkCookie(request.cookies.get('sid'))
        if ch[0] == False: return redirect(ch[1],code=302)
        data = ch[1]
        if data[0][1] != "admin": return redirect("/?auth=forbidden",code=302)
        
        s = sqlside.execute("SELECT * FROM articleContent ORDER BY view DESC")
        s = json.dumps(s, default=str)
        today = int(datetime.now().strftime("%d%m%y"))
        s1 = sqlside.execute(f"select count(*) from loginInformation union select count(*) from articleContent union select sum(view) from articleContent union select ifnull((select view from viewPerDay where day={today}),-1)")
        tAccount = int(s1[0][0])
        tArticle = int(s1[1][0])
        tView = int(s1[2][0])
        if s1[3][0] == -1:
            sqlside.execute(f"INSERT INTO viewPerDay (day, view) values ({today}, 0);",type="insert")
            todayView = 0
        else: todayView = int(s1[3][0])

        rData = {"mainTabData": [tView, tArticle, todayView],
                 "articleTabData": json.loads(s),
                 "accountTabData":{
                    "total": tAccount
                 }}

        return jsonify(rData)

@app.route("/bai-viet/<id>")
@app.route("/bai-viet/")
def bv(id=0):
    ch = checkCookie(request.cookies.get('sid'))
    if ch[0] == False: logged = False
    else: logged = True
    id1 = None
    sA = {
        "gioithieu": [-1,"Giới Thiệu"]
    }

    if not id.isdigit():
        id1 = sA.get(id)
        if id1 == None:
            return render_template("article.html", logged = logged, nf=True, id=id)
        else: id = id1[0]
    s = sqlside.execute(f"select author, createDate, lastChange, type, view, content from articleContent where id={id}")    
    if s == []: return render_template("article.html", logged = logged, nf=True, id=id)
    s = s[0]
    if s[3] != "show":
        return render_template("article.html", logged = logged, nf=True, id=id)
    cDate = datetime.fromtimestamp(s[1]).strftime("%H:%M:%S %d/%m/%y")
    lChange = datetime.fromtimestamp(s[2]).strftime("%H:%M:%S %d/%m/%y")
    ctn = BeautifulSoup(s[5], "lxml").text
    if id1: id = id1[1]
    return render_template("article.html", logged = logged, nf=False, id=id, author=s[0], view=s[4], createTime = cDate, lastTime = lChange, content = md(ctn).replace("\n", "<br>"))

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port='80')