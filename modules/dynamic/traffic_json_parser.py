

class TrafficParser:

    def __init__(self,traffic_list):
        self.traffic_list = traffic_list
        self.result = []


    def start_parser(self):
        for traffic_item in self.traffic_list:
            url = traffic_item["url"]
            if not url.startswith('https://'):
                self.result.append(url)