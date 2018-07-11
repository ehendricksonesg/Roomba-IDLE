#!/usr/bin/python
import json

# by list
j = json.loads('{"one" : "1", "two" : "2", "three" : "3"}')
print j["two"]

# by file or URL
json_file = 'myfile.json'
json_data = open(json_file)
data = json.load(json_data)
print json.dumps(data)
print data["fa"]

# dump Create2 json.config file
j_file = 'config.json'
j_data = open(j_file)
d = json.load(j_data)
#print json.dumps(d)
print d["opcodes"]["play"]
print d["sensor group packet lengths"]["2"]
print d["sensor data"]["voltage"]
