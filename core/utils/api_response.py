
def success_response(message,code,data=None,status=200):
    return Response({
        "success":True,
        "message":message,
        "code":code,
        "data":data
    })
