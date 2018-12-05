from urlparse import urlparse, urlunparse
import data
import os


class url_builder:
    def __init__(self, app_info):
        self.urlscheme_json_list = app_info.urlscheme_list
        self.fuzz_factors = []
        self.url_results = []

    def build(self):
        # read fuzz.txt to get fuzz factors
        # print os.path.abspath('.')
        fuzz_txt = open('./config/fuzz.txt')
        lines = fuzz_txt.readlines()
        for line in lines:
            self.fuzz_factors.append(line.strip('\n'))

        # parse url scheme got from dynamic detect
        self.build_from_dynamic()

        # build url from static detect (only use scheme info)
        self.build_from_static()

        # print 'url fuzz:', self.url_results
        return self.url_results

    def build_from_dynamic(self):
        for url_json in self.urlscheme_json_list:
            url = url_json['absoluteString']
            url_component = urlparse(url)
            if url_component.query != '':
                # print 'query:', url_component.query
                query = url_component.query
                query_component = query.split('&')
                query_result = []
                query_temp = []
                for i in range(len(query_component)):
                    query_temp = query_result
                    query_result = []
                    for j in range(len(self.fuzz_factors)):
                        cur_query = query_component[i]
                        cur_factor = self.fuzz_factors[j]
                        cur_query = cur_query[0:cur_query.index('=') + 1]
                        cur_query = cur_query + cur_factor
                        if len(query_temp) == 0:
                            query_result.append(cur_query)
                        for each in query_temp:
                            query_result.append(each + '&' + cur_query)

            for each in query_result:
                self.url_results.append(urlunparse((url_component.scheme, url_component.netloc, url_component.path,
                                                   url_component.params, each, url_component.fragment)))

    def build_from_static(self):
        if data.metadata['url_handlers'] is not None:
            for url_scheme in data.metadata['url_handlers']:
                for factor in self.fuzz_factors:
                    self.url_results.append(url_scheme + '://' + factor)


if __name__ == '__main__':
    url = 'scheme://root:password@www.myweb.com/path/to/file.html?a=1&b=2#fragment'
    # print urlparse(url)

    mytuple = ('http', 'www.a.com', 'a/b/c', 'params', 'a=1&b=2', 'fragment')
    # print urlunparse(mytuple)
