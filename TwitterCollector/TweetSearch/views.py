from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
import requests
import json
import xlwt
from datetime import datetime
from django.shortcuts import render
from django.conf import settings
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from TweetSearch.models import Tweet

api_key = settings.API_KEY
api_key_secret = settings.API_KEY_SECRET
bearer_token = settings.BEARER_TOKEN

path = './'
file_name = 'twitter_json'


search_url = "https://api.twitter.com/2/tweets/search/recent"

def createFile(path, file_name, data):
    pathAndName = './'+path+'/'+file_name+'.json'
    with open(pathAndName, 'w') as pdr:
        json.dump(data, pdr)

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def create_query(user_hashtag):
    # Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
    # expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields
    query_params = {'query': '#'+ user_hashtag +' -is:retweet lang:en',
                    #'start_time': start_date,
                    #'end_time': end_date,
                    'user.fields': 'username,verified,public_metrics',
                    'tweet.fields': 'author_id,created_at,text,entities,public_metrics',
                    'expansions': "author_id",
                    'max_results': 10,}

    return (query_params)
def create_query2(user_hashtag, next_token):
    # Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
    # expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields
    query_params = {'query': '#'+ user_hashtag +' -is:retweet lang:en',
                    'next_token': next_token,
                    #'start_time': start_date,
                    #'end_time': end_date,
                    'user.fields': 'username,verified,public_metrics',
                    'tweet.fields': 'author_id,created_at,text,entities,public_metrics',
                    'expansions': "author_id",
                    'max_results': 100,}

    return (query_params)

@csrf_exempt
def collector(request):
    try:
        Tweet.objects.all().delete()
        user_hashtag = str(request.POST['hashtag'])
        # if datetime.strptime(request.POST['start_date'],'%Y-%m-%d') == datetime.today():
        #     start_iso=''
        # else:
        #     start_iso = datetime.strptime(request.POST['start_date'],'%Y-%m-%d').isoformat()
        # end_iso = datetime.strptime(request.POST['end_date'],'%Y-%m-%d').isoformat()
        print(user_hashtag, type(user_hashtag))
        
        json_response = connect_to_endpoint(search_url, create_query(user_hashtag))
        counter = 0
        next_token = json_response['meta']['next_token']
        
        while next_token and counter < 5:
            for t_tweet, t_user in zip(json_response['data'], json_response['includes']['users']):
                print(t_tweet['created_at'])
                date_string = datetime.strptime(t_tweet['created_at'], '%Y-%m-%dT%H:%M:%S.000Z')
                hashtags = t_tweet['entities']['hashtags']
                hashtag_string = ''
                for hashtag in hashtags:
                    if hashtag_string == '':
                        hashtag_string = hashtag['tag']
                    else:
                        hashtag_string = hashtag_string +','+ hashtag['tag']
                Tweet.objects.create(
                    t_id = t_tweet['author_id'],
                    t_text = t_tweet['text'],
                    t_hashtags = hashtag_string,
                    t_username = t_user['username'],
                    t_nickname = t_user['name'],
                    t_likes = t_tweet['public_metrics']['like_count'],
                    t_retweets = t_tweet['public_metrics']['retweet_count'],
                    t_followers = t_user['public_metrics']['followers_count'],
                    t_verified = t_user['verified'],
                    t_date = date_string,
                )
                
            json_response = connect_to_endpoint(search_url, create_query2(user_hashtag, next_token))
            if json_response['meta']['next_token']:
                next_token = json_response['meta']['next_token']
            else:
                next_token = None
            counter = counter + 1

        createFile(path, file_name, json_response)

        # print(json.dumps(json_response, indent=4, sort_keys=True))
        return render (request, 'search.html', {'tweets':Tweet.objects.all()})
    except Exception as e:
        return render (request, 'search.html', {'data':''})

def index(request):
    return render(request,'index.html', {'tweets': Tweet.objects.all()})


def export(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Dataset' + str(datetime.now()) + '.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Dataset')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['ID','Username','Nickname','Text','Hashjtags','Likes','Retweets','Followers','Verified']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    
    rows = Tweet.objects.all().values_list('t_id','t_username','t_nickname','t_text','t_hashtags','t_likes','t_retweets', 't_followers','t_verified')
    for row in rows:
        row_num+=1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    
    wb.save(response)

    return response



    
    
    
# class indexView(TemplateView):
#     template_name = 'TwitterCollector/index.html'
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         return context

# class tableView(TemplateView):
#     template_name = 'TwitterCollector/table.html'
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         return context