import math

def wilson(successes, total, z=1.959963984540054):
    if type(total) is not int or type(successes) is not int or not 0<=successes<=total: raise ValueError('Invalid audit counts')
    if total==0: return {'estimate':None,'low':None,'high':None,'n':0}
    p=successes/total; d=1+z*z/total;mid=(p+z*z/(2*total))/d
    half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return {'estimate':p,'low':mid-half,'high':mid+half,'n':total}

def precision_recall(tp,fp,fn):
    if any(type(v) is not int or v<0 for v in (tp,fp,fn)): raise ValueError('Counts must be nonnegative integers')
    return {'precision':wilson(tp,tp+fp),'recall':wilson(tp,tp+fn)}
