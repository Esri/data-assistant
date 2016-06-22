"""
-------------------------------------------------------------------------------
 | Copyright 2016 Esri
 |
 | Licensed under the Apache License, Version 2.0 (the "License");
 | you may not use this file except in compliance with the License.
 | You may obtain a copy of the License at
 |
 |    http://www.apache.org/licenses/LICENSE-2.0
 |
 | Unless required by applicable law or agreed to in writing, software
 | distributed under the License is distributed on an "AS IS" BASIS,
 | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 | See the License for the specific language governing permissions and
 | limitations under the License.
 ------------------------------------------------------------------------------
 """
import arcpy,time, dla,json

uselib2 = False
import urllib
try: #looks like just import urllib parts the 'new' python way works best. lib2 is old python 2 approach
    import urllib.parse as parse
    import urllib.request as request
    print('urllib')
except:
    import urllib2
    uselib2 = True
    print('urllib2')


def main(argv = None):

    token = None
    for i in range(0,90):
        arcpy.AddMessage("i:"+ str(i))
        data = arcpy.GetSigninToken()
        if data is not None:
            token = data['token']
            expires = data['expires']
            arcpy.AddMessage("i:"+ str(i) + " expires:" + str(expires))
            #referer = data['referer']
            arcpy.AddMessage("Using current token")
        else:
            arcpy.AddMessage("Error: No token - Please sign in to ArcGIS Online or your Portal to continue")
            username = "S"  # Should never need this section in ArcGIS Pro...
            password = "S"  
            #portal = arcpy.GetActivePortalURL()
            #portal = portal.replace('http:','https:')
            portal = 'https://www.arcgis.com'
            tokenUrl = portal + '/sharing/rest/generateToken'  
            params = {'f': 'pjson', 'username': username, 'password': password, 'referer': portal}  #save if user/pass needed...
            #params = {'f': 'pjson', 'referer': portal} # assume signed in ...
            response = openRequest(tokenUrl,params)
            result = response.read().decode('utf-8')
            
            data = json.loads(result)  
            token = data['token']
            #return
        step = 300
        arcpy.AddMessage("sleep " + str(step))
        time.sleep(step)
'''
        arcpy.AddMessage("Error: No token - creating one")
        username = "***"  # Should never need this section in ArcGIS Pro...
        password = "***"  
          
        portal = arcpy.GetActivePortalURL()
        portal = portal.replace('http:','https:')
        tokenUrl = portal + '/generateToken'  
        #params = {'f': 'pjson', 'username': username, 'password': password, 'referer': portal}  save if user/pass needed...
        params = {'f': 'pjson', 'referer': portal} # assume signed in ...
        response = openRequest(tokenUrl,params)
        result = response.readall().decode('utf-8')
        
        data = json.loads(result)  
        token = data['token']
'''

def openRequest(url,params):
    # supposed to handle urrlib2 such as when the tool is used from the command line.
    response = None
    if uselib2 == True:
        data = urllib.urlencode(params)
        data = data.encode('utf8')
        req = urllib2.Request(url,data)  
        response = urllib2.urlopen(req)
    else:
        data = parse.urlencode(params)
        data = data.encode('utf8')
        req = request.Request(url,data)
        response = request.urlopen(req)
    
    return response

if __name__ == "__main__":
    main()
