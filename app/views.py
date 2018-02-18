from flask import session, redirect, flash, request, url_for, render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, BaseView, expose, has_access
from app import appbuilder, db
from flask_login import current_user
from flask_oauth import OAuth
import requests
from splitwise import Splitwise as splimp
import config as Config
from data_classes import *

import json
from app import app

from app.graphs import line_balance
from bokeh.embed import components

oauth = OAuth()
splitwise = oauth.remote_app('splitwise',
base_url='https://secure.splitwise.com/api/v3.0/',
request_token_url='https://secure.splitwise.com/oauth/request_token',
access_token_url='https://secure.splitwise.com/oauth/access_token',
authorize_url='https://secure.splitwise.com/oauth/authorize',
consumer_key='QhKCiloQAS3UKPQm9yrI59WGfIsJcv2VO0llHsmX',
consumer_secret='yPIQ0El2AwF8kg4RjdPjZIBKHRHTKBviycTqyHOh')




@appbuilder.sm.oauth_user_info_getter
def my_user_info_getter(sm, provider, response=None):
    if provider == 'splitwise':
        me = sm.oauth_remotes[provider].get('get_current_user').data['user']
        return {'username': str(me['id']),
                'first_name': me['first_name'],
                'last_name': me['last_name'],
                'email': me['email']}
    else:
        return {}


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', base_template=appbuilder.base_template, appbuilder=appbuilder), 404


class Starling(BaseView):
    route_base = '/starling'

    @expose('/login/')
    #@has_access
    def login(self):
        return redirect('/starling/auth')
        #return self.render_template('output.html',
         #                   getresp = str(expenses_list))
    @expose('/auth/')
    #@has_access
    #@splitwise.authorized_handler
    def authed(self):
        access_token = "idBjil3J7CS0ZCa1wqSN4vReAiM3oq2Sl0iaE6MY1MN9Bj0B0skZBxdd3X7vMRKY"
        session['starling_access_token']  = access_token
        getreq = 'transactions/mastercard'
        url = "https://api-sandbox.starlingbank.com/api/v1/"+getreq
        data = requests.get(url, headers={'Authorization': 'Bearer '+ access_token}).json()
        with open('card_transactions.json', 'w') as f:
            json.dump(data, f)
        print("\n\n\n\n\n\n")
        print(url)
        #print(data)

        return redirect('/home/login')

    @expose('/hint')
    def starling(self):
        return render_template('welcome.html', top_text="Now log in to your banking Provider",
                               auth="Starling Bank", redirect="/starling/login", img="starling",
                               base_template=appbuilder.base_template, appbuilder=appbuilder)


class Welcome(BaseView):
    route_base = '/welcome'
    default_view = '/'

    @expose('/')
    def welcome(self):
        return render_template('welcome.html', top_text="Get started by logging in to Splitwise",
                               auth="Splitwise", redirect="/splitwise/login", img="splitwise",
                               base_template=appbuilder.base_template, appbuilder=appbuilder)


@splitwise.tokengetter
def get_splitwise_token(token=None):
    return session['splitwise_token']

class Splitwise(BaseView):
    route_base = '/splitwise'

    @expose('/login/')
    #@has_access
    def login(self):
        # do something with param1
        # and render template with param
        sObj = splimp(Config.consumer_key,Config.consumer_secret)
        url, secret = sObj.getAuthorizeURL()
        session['secret'] = secret
        #url ='/splitwise/auth'
        return redirect(url)
    @expose('/auth/')
    #@has_access
    #@splitwise.authorized_handler
    def authed(self):
        if 'secret' not in session:
            return redirect('/home/login')

        oauth_token    = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')

        sObj = splimp(Config.consumer_key,Config.consumer_secret)
        access_token = sObj.getAccessToken(oauth_token,session['secret'],oauth_verifier)
        session['access_token'] = access_token

        return redirect('/home/login')

    @expose('/expenses')
    def get_expenses(self):
        sObj = splimp(Config.consumer_key,Config.consumer_secret)
        sObj.setAccessToken(session['access_token'])
        url = splimp.GET_EXPENSES_URL
        options = {}
        url += sObj.__prepareOptionsUrl(options)
        content = sObj.__makeRequest(url)
        content = json.loads(content.decode("utf-8"))
        session['expenses'] = content
        #print("\n\n\n\n\n\n" , content)
        #resp = splitwise.get('get_current_user')
        return render_template('output.html', getresp="waddup pimps", base_template=appbuilder.base_template, appbuilder=appbuilder)


class Home(BaseView):
    route_base = '/home'
    default_view = '/home'
    @expose('/login')
    def login(self):
        sw_auth = 'access_token' in session
        sl_auth = 'starling_access_token' in session
        return render_template("login.html", splitwise_auth=sw_auth, starling_auth = sl_auth,
                               base_template=appbuilder.base_template, appbuilder=appbuilder)

    @expose('/settle')
    def settle(self):
        d = []
        d.append(Debtor("Hugh Mungus", 69.0))
        d.append(Debtor("Gareth Funk", 100000))
        d.append(Debtor("The Queen", 1000000000.01))

        return render_template("settle.html", debtors=d,
                               base_template=appbuilder.base_template, appbuilder=appbuilder)

    @expose('/home')
    def root(self):
        if 'calculated_records' not in session:
            df = m.get_sample_data()
            self.r = create_records(df)
            session['calculated_records'] = True
        return render_template("root.html", records=self.r,
                               base_template=appbuilder.base_template, appbuilder=appbuilder)
    
    @expose('/balance')
    def balance(self):
        chart = line_balance("data")
        script, div = components(chart)
        return render_template("graphs.html", script=script, div=div, base_template=appbuilder.base_template, appbuilder=appbuilder)



appbuilder.add_view_no_menu(Splitwise())
appbuilder.add_view_no_menu(Starling())
appbuilder.add_view_no_menu(Home())

#appbuilder.add_view(Welcome, "Welcome", category='Charts')
# appbuilder.add_view(Home, "/home/home")
appbuilder.add_link("Settle", "/home/settle", label="Settle")
# appbuilder.add_view_no_menu(Welcome())
# appbuilder.add_link("Splitwise", href='/splitwise_login/', category='Login')

  
db.create_all()


