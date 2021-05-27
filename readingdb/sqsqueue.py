import abc

class SQSQueue(abc.ABC):
    @abc.abstractmethod
    def add_message_to_queue(queue_url: str, route_id: str) -> None:
        '''Adds message to designated queue. Requires queue_url && route_id.
        There is definitely a better way to handle the queue designation 
        '''
        raise NotImplementedError('add_message_to_queue is not implemented') 

    @abc.abstractmethod
    def receive_message_from_queue(queue_url: str, ) -> None:
        '''Receives next message from designated queue
        '''
        raise NotImplementedError('receive_message_from_queue is not implemented') 

    @abc.abstractmethod
    def delete_message_from_queue(queue_url: str, message: str) -> None:
        '''Deletes next message from designated queue
        '''
        raise NotImplementedError('delete_message_from_queue is not implemented') 