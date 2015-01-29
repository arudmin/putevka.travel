#!venv/bin/python
# -*- coding: utf-8 -*-
import os, re, requests
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, Response, request, escape, redirect, url_for
from flask.ext.compress import Compress
from htmlmin import minify as html_minify
import json as JSON
from lxml import html
from lxml.etree import tostring

app = Flask(__name__)
Compress(app)

# @app.before_request
# def beforerequest():
  # if 'iPhone' in request.headers['User-Agent'] and 'mobile' not in request.path:
    # return redirect(url_for('mobile'))

@app.route('/api/rating/tophotels/<query>')
def getRatingTophotels(query=None, country=''):
  fromGoogle     = request.args.get('fromGoogle')
  fromGETcountry = request.args.get('fromGETcountry')

  if not fromGoogle: # delete country from query
    country = query.split()[0]
    query   = ' '.join(query.split()[1:])

  url = 'http://www.tophotels.ru/actions/hotel_search_new/?q=%s' % query
  r   = requests.get(url)
  # print '==================='
  # print r.text
  # print ''
  # print query, fromGETcountry, fromGoogle
  # print ''

  # If hotel found
  itemsCount = int(r.text.split('|')[1])

  if not itemsCount:
    getHotelName = getNameFromGoogle(country + ' ' + query)
    return getHotelName

  if not itemsCount:
    data = {'status': 404}
    return json(data)

  items = []
  elem  = {}
  for item in range(1, itemsCount+1):
    # example (al|Dessole Cataract Sharm Resort|4*|Шарм-Эль-Шейх|Египет|13544|4,16)
    params  = r.text.split('\n')[item].split('|')
    elem['id']      = params[5]
    elem['rating']  = params[6]
    elem['country'] = params[4]
    elem['city']    = params[3]
    elem['stars']   = params[2][0]
    elem['name']    = params[1]
    if (not fromGoogle or (elem['country'] == fromGETcountry)):
      items.append(elem)

  # print items, elem, items
  return json(items)

  # if (status):
    # print 'success'
    # rating = r.text.split('\n')[1].split('|')[7]
    # data = {'status': 200, 'data': g}
    # return json(resp)


  # rating = '8.33'
  # return r.text
  # return json(data)

@app.route('/json')
@app.route('/<query>/json')
def main(query=None):
  data = getData(query)
  return json(data)

@app.route('/')
# @app.route('/mobile')
# @app.route('/mobile/')
@app.route('/<query>')
@app.route('/tags/<query>')
def mainApp(query=None):
  mobile_platforms = ('ipad', 'iphone', 'android') 

  data = getData(query)

  if (request.headers.get('Content-Type') == 'application/json'):
    return json(data)

  # if any(p in mobile_platforms for p in request.user_agent.platform):
  # if ('iphone' in request.user_agent.platform):
  if any(p in request.user_agent.platform for p in mobile_platforms):
    return html_minify(render_template('mobile/index.html', **data))

  return html_minify(render_template('index.html', **data, platform=request.user_agent.platform))






def getData(query=None):
  if query:
    r = requests.get('http://putevka.travel/tag/' + query)
  else:
    r = requests.get('http://putevka.travel')

  soup  = bs(r.text)
  for tag in soup.findAll('del'):
    tag.replaceWith('')
  tours     = []
  countries = {}
  imgUrl = ''
  #Generating Tours Array
  posts = soup.findAll('div', 'post')
  for post in posts:
    items   = []
    header  = post.find('h1').get_text()
    url     = post.find('h1').find('a', href=True)['href']
    # print url
    publish = post.find('div', 'postmetadata').get_text().split('.')[0]
    try:
      imageUrl   = str(post.find('img', 'size-full')).split('"')[7]
    except:
      imageUrl = None

    tagsArr  = []
    tagsList = ''
    tags     = post.findAll('a', {'rel': 'tag'})
    for tag in tags:
      tagsArr.append({
        'name': tag.get_text(),
        'url' : tag['href'].split('/')[4]
      })
      tagsList += tag.get_text() + ', '

    for item in post.find('div', 'entry').findAll('p'):
      offer = item.get_text().replace('&', 'and')
      # items.append(escape(offer))
      items.append(offer)
    description = items[-2:-1]
    items.pop(0)
    items.pop(-2)
    items.pop(-1)

    tours.append({
      '_published'   : publish[:-2].strip(), #date format "dd MM YYYY" (RUS)
      '_title'     : header,
      'items'      : items,
      'imageUrl'    : imageUrl,
      'description' : description[0],
      # 'tags'      : tagsList[:-2].replace(' ', '').replace(u'—', '_').split(',')
      'tags'      : tagsArr
    })

    # items.append(tagsList[:-2])

  # Generating Countries Array for the Select Input
  list_countries = soup.find('div', 'menu-populyarnyie-container').findAll('a', href=True)
  for item in list_countries:
    title = item.text
    link  = item['href'].split('/')[4]
    countries[link] = title

  # Remove the first Post from the Main Page (infopost)
  if query:
    try:
      title = countries[query]
    except:
      title = ''
      pass
  else:
    tours.pop(0)
    title = ''

  return {'title': title, 'tours': tours, 'countries': countries}

def json(data):
  return Response(JSON.dumps(data), mimetype="application/json; charset=utf-8")

def getNameFromGoogle(param):
    host  = 'www.tophotels.ru/main/hotel/al'
    url   = "https://www.google.com/search?q=%s&oq=%s&sourceid=chrome&es_sm=119&ie=UTF-8#newwindow=1&safe=off&q=%s+site:tophotels.ru" % (param, param, param)
    r     = requests.get(url)
    tree  = html.fromstring(r.text)
    # return r.text
    try:
      url   = tree.xpath('.//div[@id="ires"]//h3//a/@href')[0]
      title = tree.xpath('.//div[@id="ires"]//h3//b')[0].text
      if host in url:
        return redirect(url_for('getRatingTophotels', query=title.strip(), fromGoogle=1, fromGETcountry=param.split()[0]))
    except:
      pass
    return json({'status': 404})




app.jinja_env.globals['static'] = (
    lambda filename: url_for('static', filename = filename)
)

if __name__ == '__main__':
  app.debug = True
  app.run('0.0.0.0', 5000)
