import json

def message(the_word):
    """
    View helper. Generate full JSON respone for generic message.
    """
    return json.dumps({'message': the_word})