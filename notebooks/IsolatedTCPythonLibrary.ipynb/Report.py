""" standard """
from datetime import datetime

""" custom """


class Report(object):
    """ """
    def __init__(self):
        """ """
        self._report_objects = []

        # indexes
        self._http_method_idx = {}
        self._status_code_idx = {}

        # attributes
        self._api_calls = 0
        self._filter_count = 0
        self._filter_count_api = 0
        self._filter_count_post = 0
        self._request_time = None
        self._results_filtered = 0
        self._results_unfiltered = 0
        self._start = datetime.now()

    def add(self, data_obj):
        """ """
        self._report_objects.append(data_obj)
        if data_obj.track:
            self._filter_count += 1

        # create indexes for request objects
        if data_obj.type == 'ro':
            if hasattr(data_obj, 'http_method'):
                self._http_method_idx.setdefault(data_obj.http_method, []).append(data_obj)
            if hasattr(data_obj, 'status_code'):
                self._status_code_idx.setdefault(data_obj.status_code, []).append(data_obj)

            # track this filter
            if data_obj.track:
                self._filter_count_api += 1
        elif data_obj.type == 'pfo':
            self._filter_count += 1
            self._filter_count_post += 1

    def add_api_call(self):
        """ """
        self._api_calls += 1

    def add_request_time(self, data):
        """ """
        if self._request_time is None:
            self._request_time = data
        else:
            self._request_time += data

    def add_filtered_results(self, data):
        """ """
        self._results_filtered += data

    def add_unfiltered_results(self, data):
        """ """
        self._results_unfiltered += data

    @property
    def api_calls(self):
        """ """
        return self._api_calls

    @property
    def failures(self):
        """ """
        for k, v in self._status_code_idx.items():
            if k not in [200, 201, 202]:
                for f in v:
                    yield '{0!s}'.format(f)

    @property
    def request_time(self):
        """ """
        return self._request_time

    @property
    def results_filtered(self):
        """ """
        return self._results_filtered

    @property
    def results_unfiltered(self):
        """ """
        return self._results_unfiltered

    @property
    def runtime(self):
        """ """
        return datetime.now() - self._start

    @property
    def stats(self):
        """ """
        report = '\n{0!s:_^80}\n'.format('Stats')

        #
        # api stats
        #
        report += '\n{0!s:40}\n'.format('API Stats')
        report += '  {0!s:<29}{1!s:<50}\n'.format('API Calls', self.api_calls)
        report += '  {0!s:<29}{1!s:<50}\n'.format('Unfiltered Results', self.results_unfiltered)
        report += '  {0!s:<29}{1!s:<50}\n'.format('Filtered Results', self.results_filtered)

        #
        # filter counts
        #
        report += '\n{0!s:40}\n'.format('Filters')
        report += '  {0!s:<29}{1!s:<50}\n'.format('API Filters', self._filter_count_api)
        report += '  {0!s:<29}{1!s:<50}\n'.format('Post Filters', self._filter_count_post)
        report += '  {0!s:<29}{1!s:<50}\n'.format('Total Filters', self._filter_count)

        #
        # http methods
        #
        if len(self._http_method_idx.items()) > 0:
            report += '\n{0!s:40}\n'.format('HTTP Methods')
            for k, v in self._http_method_idx.items():
                report += '  {0!s:<29}{1!s:<50}\n'.format(k, len(v))

        #
        # status codes
        #
        if len(self._status_code_idx.items()) > 0:
            report += '\n{0!s:40}\n'.format('Status Codes')
            for k, v in self._status_code_idx.items():
                report += '  {0!s:<29}{1!s:<50}\n'.format(k, len(v))

        #
        # performance
        #
        report += '\n{0!s:40}\n'.format('Performance Stats')
        if self.request_time is not None:
            report += '  {0!s:<29}{1!s:<50}\n'.format('Request Time', self.request_time)
            report += '  {0!s:<29}{1!s:<50}\n'.format('Processing Time', (self.runtime - self.request_time))
        report += '  {0!s:<29}{1!s:<50}\n'.format('Run Time', self.runtime)

        return report

    @property
    def stats_dict(self):
        """ """
        report = {
            'API calls': self.api_calls,
            'Unfiltered Results': self.results_unfiltered,
            'Filtered Results': self.results_filtered,
            'HTTP Methods': [],
            'Status Codes': []}

        #
        # http methods
        #
        report += '\n{0:40}\n'.format('HTTP Methods')
        for k, v in self._http_method_idx.items():
            report['HTTP Methods'].append({k: len(v)})

        #
        # status codes
        #
        for k, v in self._status_code_idx.items():
            report['Status Codes'].append({k: len(v)})

        #
        # performance
        #
        if self.request_time is not None:
            report['Request Time'] = self.request_time
            report['Processing Time'] = (self.runtime - self.request_time)
        report['Run Time'] = self.runtime

        return report

    def __iter__(self):
        """ """
        for ro in self._report_objects:
            yield ro
