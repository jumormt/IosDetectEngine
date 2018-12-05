import data

class MitmParser:

    def __init__(self,list):
      self.results = dict()
      self.info = list

    def start_parse(self):
        for item in self.info:
            if item in self.results.keys():
                self.results[item] += 1
            else:
                self.results[item] = 1

        # print self.results