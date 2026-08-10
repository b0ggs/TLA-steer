import json,sys
result={}
for name in sys.argv[1:]:result.update(json.load(open(name)))
print(json.dumps(result))

