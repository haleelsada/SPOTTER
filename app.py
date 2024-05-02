from flask import Flask, request, jsonify
import googlemaps
from datetime import datetime
from flask_cors import CORS, cross_origin
key = API_KEY_HERE
gmaps = googlemaps.Client(key=key)


def get_popular_places(cords, place_type, place_name='', radius=1500, rankby='prominence'):
    """
    Function to get popular places with their details based on coordinates.

    Args:
        lat (float): Latitude of the location.
        lng (float): Longitude of the location.
        radius (int, optional): Search radius in meters. Defaults to 1500 meters.
        place_type (str, optional): Type of place to search for. Defaults to 'restaurant'.
        rankby (str, optional): Specifies the ranking method. Defaults to 'prominence'.

    Returns:
        list: List of dictionaries containing place details.
    """
    places = gmaps.places_nearby(location=cords, radius=radius, type=place_type, rank_by=rankby)

    places_details = []

    for place in places['results']:
        place_id = place['place_id']
        details = gmaps.place(place_id, fields=['name', 'rating', 'user_ratings_total', 'geometry'])
        distance = gmaps.distance_matrix(origins=cords, destinations=(details['result']['geometry']['location']['lat'], details['result']['geometry']['location']['lng']))['rows'][0]['elements'][0]['distance']['value']
        try:
          place_details = {
              'name': details['result']['name'],
              'rating': details['result']['rating'],
              'user_ratings_total': details['result']['user_ratings_total'],
              'coordinates': details['result']['geometry']['location'],
              'distance': distance
          }
        except:
          place_details = {
            'name': details['result']['name'],
            'rating': 0.1,
            'user_ratings_total': 0.1,
            'coordinates': details['result']['geometry']['location'],
            'distance': 1 if distance==0 else distance
        }
        places_details.append(place_details)

    # Rank places based on rating and number of reviews
    places_details.sort(key=lambda x: (x['rating'], x['user_ratings_total']), reverse=True)

    return places_details



call=[(11.3599, 75.9129),(11.3215, 75.9953),(11.3049, 75.8771),('restaurant','medium','Calicut')]

ranks=[]
def get_rank(coordinates,type_,size):
  error=[]
  if size=='large':
    size=2000
  elif size=='medium':
    size=1000
  elif size=='small':
    size=500
  ranks=[]
  compsd=[]
  compsr=[]
  for c in coordinates:
    rank=0
    weight=0
    compd=0
    compr=0
    try:
      competitors=get_popular_places(c, place_type=type_, radius=size)
    except:
      error.append(c)
      continue
    
    for b in competitors:
      weight = b['rating']*b['user_ratings_total']/b['distance']
      compd+=b['distance']
      compr+=b['rating']*b['user_ratings_total']
      rank=rank+weight
    ranks.append(rank)
    compsd.append(compd)
    compsr.append(compr)
  #print(ranks)

  l = len(ranks)
  newl = ranks.copy()
  newl.sort()
  ranks = [newl.index(i)+1 for i in ranks]
  ranks=[l+1-i for i in ranks]

  #print(ranks)
  print(compsd)
  print(compsr)
  compsd_avg=sum(compsd)/len(compsd)
  for i in range(len(compsd)):
    if compsd[i]<(compsd_avg*80/100):
      compsd[i]='relatively more competitors nearby'
    elif compsd[i]==0:
      compsd[i]='make sure place got enough population density'
    else:
      compsd[i]=''
  compsr_avg=sum(compsr)/len(compsr)
  for i in range(len(compsr)):
    if compsr[i]>(compsr_avg*120/100):
      compsr[i]='comparatively more good competitors in area'
    elif compsr[i]==0:
      compsr[i]='make sure place got enough population density'
    else:
      compsr[i]=''
  #print(compsd)
  #print(compsr)
  for i in error:
    ind=call.index(c)
    ranks.insert(ind,'error')
    compsd.insert(ind,'error')
    compsr.insert(ind,'error')

  return {'rank':ranks,'observation1':compsd,'observation2':compsr}
#get_rank(call)
#data format:
#{coordinates: [{latitude: 37.7749, longitude: -122.4194 },{ latitude: 40.7128, longitude: -74.0060 },],type_: 'restaurant',size=['medium']}

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/')
def start():
	return jsonify({'hello':'test'})

@app.route('/test',methods=['POST','GET'])
def hello_world():
	name = request.args['name']
	print(name)
	print('api called')
	data = request.get_json()
	print('got data')
	print(data)
	cords=[(i['latitude'],i['longitude']) for i in data['coordinates']]
	type_=data['type']
	size=data['size']
	result=get_rank(cords,type_,size)
	
	print(result)
	
	'''call=request.args.get('cordinates')
	out = get_rank(call)'''
	return jsonify({'result':result})
