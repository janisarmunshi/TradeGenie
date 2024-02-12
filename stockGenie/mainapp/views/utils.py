from pandas import Series
def trim(data):
    if type(data) is str:        
        return " ".join(data.split()) 
    else:
        return data


def isBlankOrNone(obj):
    return obj == '' or obj == None  

def getItemByKey(list, key, value, first_only=False):
    lstItem = []
    for struct in list:
        for k, v in struct.items():
            if k == key:
                if type(v)==bytes:
                    val = v.decode("utf-8")
                else:
                    val = v
                if val == value:
                    lstItem.append(struct)
                    if first_only == True:
                        return lstItem                      
    return lstItem

def getUniqueKey(list,key):
# Order preserving
    lstKey = []
    for struct in list:
        for k, v in struct.items():
            if k == key and v not in lstKey:
                lstKey.append(v)

    return lstKey

def getUniqueStruct(list):
# Order preserving
    lstUnique = []
    for item in list:
        if item not in lstUnique:
            lstUnique.append(item)
    return lstUnique

def getStructKey(struct, val):
    for key, value in struct.items():
        if val == value:
            return key 
    return None

def pdSeries(df, column = None,value = None):
    # Return Unique value as list from the dataframe for each column 
    try:
        if column == None or value == None:
            df1 = df
        else:
            df1 = df.loc[df[column] == value]
        return Series({c: df1[c].unique() for c in df1})    
    except Exception as e:
        return False