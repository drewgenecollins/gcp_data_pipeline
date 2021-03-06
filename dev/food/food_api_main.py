import requests
import json
import random
import os
import datetime
import re
import multiprocessing
import time
import ast


def openfoodfacts_codes_extractor():
    '''Extracts the codes from the 22G DB JSON'''
    ip = r"C:\Users\drewg\Desktop\jobs\mobkoi\openfoodfacts-products.jsonl\openfoodfacts-products.json"
    with open(ip, encoding='cp437') as fp, open('codes.txt', 'w') as ofp:
        q= '\"code\":\"'
        for p, line in enumerate(fp):
            code=line.split(q, 1)[1].split('\"')[0]
            ofp.write(code+'\n')



def product_codes(sample_size):
    with open("codes.txt") as fp:
        i = 1860044
        code_indexes = random.sample(range(1,i), sample_size) # 300 samples for 5MB
        codes = []
        for p, line in enumerate(fp):
            if p in code_indexes:
                codes.append(line.rstrip("\n"))
    return (codes)


def openfoodfacts(code):
    '''calls api and gives json'''
    r = requests.get( 
        url =  "https://world.openfoodfacts.org/api/v0/product/" 
        + code + ".json"
    )
    return (r.json())



def modify_json(input_json):
    '''corrects format of JSON keys for big query import '''

    ps = json.dumps(input_json) # product string from json

    pattern = re.compile(r'(?<=\")(\w*-\w*)+(?=\":)') # finds all keys that have a dash
    match = pattern.search(ps)
    while match is not None:
        new_str = match.group().replace('-', '_')
        ps = ps[:match.start()] + new_str + ps[match.end():]
        match = pattern.search(ps)

    pattern = re.compile(r'(?<=\")(\w*:\w*)+(?=\":)') # finds all keys that have a dash
    match = pattern.search(ps)
    while match is not None:
        new_str = match.group().replace(':', '_')
        ps = ps[:match.start()] + new_str + ps[match.end():]
        match = pattern.search(ps)

    pattern = re.compile(r'(?<=\")\d\w*(?=\":)') # finds all keys that start with a number
    match = pattern.search(ps)
    while match is not None:
        new_str = '_' + match.group()
        ps = ps[:match.start()] + new_str + ps[match.end():]
        match = pattern.search(ps)

    ps = ps.replace('{}', '[]')

    return(json.loads(ps))

    



def multi_product_jsonl(sessions):
    
    f = sessions + '\\' + datetime.datetime.now().strftime("%Y%m%d_%H%M") + '_food.jsonl'
    print(f)

    with open(f, 'w') as fp:
        for i, code in enumerate(product_codes(5)):
            print('{} code {}'.format(i, code))
            j = openfoodfacts(code) # call api with code and gives json now dict
            m = modify_json(j)      # corrects format of JSON keys for big query import

            json.dump(m, fp)
            fp.write('\n')

    return(f)



def main():
    sessions =  "C:\\Users\\drewg\\Documents\\code\\gcp_data_pipeline\\dev\\tests"
    multi_product_jsonl(sessions)



if __name__ == '__main__':
    main()


    '''
    Issue with keys having dash instead of underscore.
    Need to correct dashes but easier to debug with a single product json.

    Test setup and 
    1. DONE Create single product json, indent to see all keys
    ^ useful if manual schema necessary

    2. DONE Create single product json, single line to pass jsonL into bq
    - test
    3. replace("org-database-usda","org_database_usda") or manually
    - test
    4. better logic, find all keys in file, and cover all dashes - into underscores _
    - test
  
    5. NEW 400 KEY error.

    find way to query all keys in json object

    ----



    Invalid field name "org-database-usda". Fields must contain only letters, numbers, and underscores, start with a letter or underscore, and be at most 300 characters long. Table: test_food_705b4148_61db_438d_bce3_17a453ff7166_source
    
    Invalid field name "400". Fields must contain only letters, numbers, and underscores, start with a letter or underscore, and be at most 300 characters long. Table: 20210717_1803_food_86928453_b249_4352_b203_9d10969ea70b_source
    
    Invalid field name "ciqual_food_code:en". Fields must contain only letters, numbers, and underscores, start with a letter or underscore, and be at most 300 characters long. Table: 20210718_1732_food_0470cb86_3c79_408a_9f70_f78478881e65_source
    
    Unsupported empty struct type for field 'product.category_properties'


    failed at 00853484
    '''