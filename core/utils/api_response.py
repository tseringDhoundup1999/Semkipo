from django.conf import settings
def success_response(message,code,data=None):
    response = {
        "success":True,
        "message":message,
        "code":code,
        "data":data
    }
    return response 
    
    
def error_response(message,code,error=None,debug=None):
    response = {
        "success":False,
        "message":message,
        "code":code,
        "error":error,
        "debug":str(debug)
    }
    if not settings.DEBUG:
        response.pop("debug",None) # remove debug info in production
    return response
    