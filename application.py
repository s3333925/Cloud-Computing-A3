import json
import boto3
import requests
from datetime import datetime, date, timedelta

from flask import Flask, request, render_template, url_for, redirect
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from botocore.config import Config
config = Config (region_name = 'us-east-1')

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', config=config)

victoria_table = dynamodb.Table('victoria')
localarea_table = dynamodb.Table('localarea')

application = Flask(__name__)
application.secret_key = '?'

# Functions

def get_date(query):
    return query.get('date')

def query_victoria():

    response = victoria_table.scan()
    return response['Items']


def query_localarea():

	response = localarea_table.scan()
	return response['Items']

# Routes

@application.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        time_query = int(request.form['time'])

        user_query = query_victoria()

        for x in user_query:
            x['date'] = datetime.strptime(x['date'], "%d/%m/%Y").date()

        sorted_list = sorted(user_query, key=lambda x: int(x.get('id', 0)))
        sorted_list = sorted_list[-time_query:]
        return render_template('index.html', user_query=sorted_list)

    else:
        user_query = query_victoria()

        for x in user_query:
            x['date'] = datetime.strptime(x['date'], "%d/%m/%Y").date()

        sorted_list = sorted(user_query, key=lambda x: int(x.get('id', 0)))
        return render_template('index.html', user_query=sorted_list)

#

@application.route('/localarea/', methods=['GET', 'POST'])
def localarea():

    if request.method == 'POST':

        area_query = request.form['area']+" "

        if area_query == " ":
            error = 'User must enter a suburb.'
            return render_template('localarea.html', error=error)

        time_query = int (request.form['time'])
        user_query = query_localarea()

        areafilter = []

        for item in user_query:
            if item['area'] == area_query:
                areafilter.append(item)

        user_query = areafilter

        if len(user_query) == 0:
            error = 'No result is retrieved. Please query again'
            return render_template('localarea.html', error=error)

        for x in user_query:
            x['date'] = datetime.strptime(x['date'], "%d/%m/%Y").date().isoformat()

        sorted_list = sorted(user_query, key=lambda x: int(x.get('id', 0)))

        if time_query != 0:
            timefilter = []

            for item in user_query:
                if item['date'] >= (datetime.now()-timedelta(days=time_query)).date().isoformat():
                    timefilter.append(item)

            user_query = timefilter

            if len(user_query) == 0:
                error = 'No cases found in the last '+ str(time_query) + ' days'
                return render_template('localarea.html', error=error)

            filter = []
            i=0
            time = time_query

            while i <= time_query:
                x = {'date':(datetime.now()-timedelta(days=time)).date().isoformat(), 'total':0}
                filter.append(x)
                time-=1
                i+=1

            for item in filter:
                for x in user_query:
                    if x['date'] == item['date']:
                        item['total'] = x['total']

            user_query = filter
            sorted_list = sorted(user_query, key=lambda x: x.get('date', 0))

        return render_template('localarea.html', user_query=sorted_list, area=area_query )

    return render_template('localarea.html')

@app.route('/news/', methods=['GET'])
def news():
    
    response = requests.get('http://newsapi.org/v2/top-headlines?country=au&q=COVID&apiKey=5922bb9e9b2e49a4885173c91c5dbb3a')

    data = response.json() 
    top_headlines = data['articles'] 

    return render_template('news.html', top_headlines=top_headlines)

if __name__ == '__main__':

    application.run()
