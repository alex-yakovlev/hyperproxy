import json
from http import server
import os
import urllib


def _format_response(resp):
    return json.dumps(resp, indent=4).encode('UTF-8')


class MockHandler(server.BaseHTTPRequestHandler):
    '''
        Мок API партнера для локальной разработки (т.к. playground-версии нет)
    '''

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        req_path = urllib.parse.urlparse(self.path).path
        if req_path == '/exchange_rates/':
            self.wfile.write(_format_response(self.GET_exchange_rates()))

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.path == '/orders/credit':
            self.wfile.write(_format_response(self.POST_create_order()))

    @staticmethod
    def GET_exchange_rates():
        return {
            'exchange_rates': [
                {'from': 'EUR', 'to': 'USD', 'rate': '1.06212'},
                {'from': 'GBP', 'to': 'USD', 'rate': '1.24431'},
                {'from': 'USD', 'to': 'JPY', 'rate': '154.242'},
                {'from': 'USD', 'to': 'CHF', 'rate': '0.91222'},
                {'from': 'USD', 'to': 'CAD', 'rate': '1.37911'},
                {'from': 'AUD', 'to': 'USD', 'rate': '0.64387'},
                {'from': 'NZD', 'to': 'USD', 'rate': '0.58996'},
                {'from': 'USD', 'to': 'RUB', 'rate': '93.5975'},
                {'from': 'EUR', 'to': 'RUB', 'rate': '99.64'},
                {'from': 'AUD', 'to': 'CAD', 'rate': '0.88808'},
                {'from': 'AUD', 'to': 'NZD', 'rate': '1.09107'},
                {'from': 'AUD', 'to': 'JPY', 'rate': '99.324'},
                {'from': 'AUD', 'to': 'CHF', 'rate': '0.58739'},
                {'from': 'CHF', 'to': 'JPY', 'rate': '169.063'},
                {'from': 'GBP', 'to': 'NZD', 'rate': '2.10849'},
                {'from': 'EUR', 'to': 'AUD', 'rate': '1.6492'},
                {'from': 'EUR', 'to': 'CAD', 'rate': '1.46475'},
                {'from': 'EUR', 'to': 'DKK', 'rate': '7.45937'},
                {'from': 'EUR', 'to': 'GBP', 'rate': '0.85348'},
                {'from': 'EUR', 'to': 'JPY', 'rate': '163.834'},
                {'from': 'EUR', 'to': 'CHF', 'rate': '0.96895'},
                {'from': 'EUR', 'to': 'NZD', 'rate': '1.79974'},
                {'from': 'EUR', 'to': 'NOK', 'rate': '11.62567'},
                {'from': 'EUR', 'to': 'SEK', 'rate': '11.56596'},
                {'from': 'GBP', 'to': 'AUD', 'rate': '1.9321'},
                {'from': 'GBP', 'to': 'CAD', 'rate': '1.71608'},
                {'from': 'GBP', 'to': 'CHF', 'rate': '1.1351'},
                {'from': 'GBP', 'to': 'JPY', 'rate': '191.931'},
                {'from': 'USD', 'to': 'SEK', 'rate': '10.8891'},
                {'from': 'USD', 'to': 'DKK', 'rate': '7.02235'},
                {'from': 'USD', 'to': 'NOK', 'rate': '10.9451'},
                {'from': 'USD', 'to': 'SGD', 'rate': '1.36275'},
                {'from': 'USD', 'to': 'ZAR', 'rate': '18.97025'},
                {'from': 'USD', 'to': 'MXN', 'rate': '16.72423'},
                {'from': 'EUR', 'to': 'CNY', 'rate': '7.71023'},
                {'from': 'USD', 'to': 'CNY', 'rate': '7.25885'},
                {'from': 'CNY', 'to': 'RUB', 'rate': '12.8742'},
                {'from': 'USD', 'to': 'TRY', 'rate': '32.32679'},
                {'from': 'EUR', 'to': 'TRY', 'rate': '34.35965'},
                {'from': 'TRY', 'to': 'RUB', 'rate': '2.8913'},
            ]
        }

    @staticmethod
    def POST_create_order():
        return {'orders': [
            {
                'id': '001',
                'status': 'credited',
                'amount': '123', 'currency': 'USD'
            },
        ]}


if __name__ == '__main__':
    with server.ThreadingHTTPServer(
        ('', int(os.getenv('PORT'))),
        MockHandler
    ) as httpd:
        httpd.serve_forever()
