import json

# 조건에 만족하는 오브젝트가 존재하는지 확인하는 함수
def isObjectExists(model, **kwargs):
    return model.objects.filter(**kwargs).exists()

# Model.objects.filter(model, **kwargs) 의 결과로 반환된 OrderedDict 객체를 Json으로 반환하는 함수
# toObject : True => json을 list 형태로 반환해준다. (결과가 여러 json을 반환할 때 사용)
# toObject : False => json을 단일 json으로 반환해준다. (결과가 하나인 json을 반환할 때 사용)
def OrderedDicttoJson(dic, tolist=False):

    json_data = json.loads(json.dumps(dic, indent=4))
    
    if len(json_data) > 0:
        # tolist에 따라 다른 데이터 형식으로 반환
        return json_data if tolist else json_data.pop()
    else:
        return []

def ConcatDict(*dicts):

    return_dict = {}

    for dict_item in dicts:
        return_dict.update(dict_item)
    
    return return_dict