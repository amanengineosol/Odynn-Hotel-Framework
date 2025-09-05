from .task import process_live_request


def send_live_request_to_queue(request_data, crawler):
    print("will now prepare and send meassage to queue ")
    process_live_request.apply_async(
        args=(request_data,),
        queue=crawler,          
        routing_key=crawler
    )