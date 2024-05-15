class API_Error(Exception):
    def __init__(self, message, url=None, response=None):
        self.message = message
        self.url = url
        self.response = response
