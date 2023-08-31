from flask import Flask, request
from multiprocessing import Lock
from threading import BoundedSemaphore,Thread
from queue import Queue
import numpy as np
import json

''' don't mind this :) '''
class serial(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj,np.ndarray):
            return obj.tolist()
        return json.JSONDecodeError.default(self,obj)


'''variables'''
app = Flask(__name__)
number_of_workers = 2
bs = BoundedSemaphore(value=number_of_workers)
lock = Lock()
queue = Queue()
m1 = None
m2 = None
results = None
bound = 0

'''multiplication'''
def multiply(args):
    i,j = args
    a = m1[i]
    b = m2[j]
    return np.dot(a,b),i,j
    

'''worker management'''
def worker_manage(queue,res):
    
    while not queue.empty():
        args = queue.get()
        
        with bs:
            with lock:
                ans,i,j = multiply(args)
                results[i][j]=ans
            

'''multiply rout'''
@app.route('/multiply',methods=['POST'])
def matrix_multiply():
    global bound
    global m1,m2,results
    data = request.get_json()
    m1 = np.array(data['m1'])
    m2 = np.array(data['m2'])

    
    if m1.shape[1] != m2.shape[0]:
        return "not a valid request...",400
    
    bound = m1.shape[0]*m2.shape[1]
    
    results = np.zeros((m1.shape[0],m2.shape[1]))
    
    m2 = m2.T
    
    for i in range(m1.shape[0]):
        for j in range(m2.shape[0]):
            queue.put((i,j))
            

    
    threads = [Thread(target=worker_manage,args=(queue,results)) for _ in range(number_of_workers)]
    
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
    
    res = json.dumps(results,cls=serial)
    
    ans = {"answer":res,"number_of_workers":number_of_workers}

    
    return ans,200


'''emtiazi'''
@app.route('/setWorkers',methods = ['PUT'])
def set_worker_num():
    global bs
    global number_of_workers

    data = request.get_json()
    
    n = data.get('number_of_workers')
    if not n:
        return "not valid...",400
    elif n>bound:
        return "{} workers are allowed at most".format(bound)
    else:
        bs = BoundedSemaphore(value=n)
        number_of_workers = n
    return "number of workers is now set to {}".format(n)


        
if __name__=="__main__":
    app.run(host="0.0.0.0",port=2000)
    
