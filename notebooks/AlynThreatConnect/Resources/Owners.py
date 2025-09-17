""" standard """
import types

""" custom """
#from threatconnect import ApiProperties
#from threatconnect import OwnerFilterMethods
#from threatconnect.Config.ResourceType import ResourceType
from FilterObject import FilterObject
#from threatconnect.OwnerObject import OwnerObjectAdvanced
from RequestObject import RequestObject
from Resource import Resource
#from threatconnect.OwnerMetricsObject import parse_metrics
#from threatconnect.OwnerMembersObject import parse_member


class Owners(Resource):
    """ """
    def __init__(self, tc_obj):
        """ """
        super(Owners, self).__init__(tc_obj)
        self._filter_class = OwnerFilterObject
        self._resource_type = ResourceType.OWNERS

    def _method_wrapper(self, resource_object):
        """ """
        return OwnerObjectAdvanced(self.tc, self, resource_object)

    @property
    def default_request_object(self):
        """ default request when no filters are provided """
        resource_properties = ApiProperties.api_properties[self._resource_type.name]['properties']
        # create default request object for non-filtered requests
        request_object = RequestObject()
        request_object.set_http_method(resource_properties['base']['http_method'])
        request_object.set_owner_allowed(resource_properties['base']['owner_allowed'])
        request_object.set_request_uri(resource_properties['base']['uri'])
        request_object.set_resource_pagination(resource_properties['base']['pagination'])
        request_object.set_resource_type(self._resource_type)
        return request_object

    def get_owner_by_id(self, data_int):
        """ return owner by id """
        if isinstance(data_int, int):
            for obj in self._objects:
                if obj.id == data_int:
                    return obj
        else:
            return None

    def get_owner_by_name(self, data):
        """ return owner by name """
        if isinstance(data, (str, unicode)):
            for obj in self._objects:
                if obj.name == data:
                    return obj
        else:
            return None

    @property
    def names(self):
        """ generator for owner names """
        for obj in self._objects:
            yield obj.name

    def retrieve_metrics(self):
        """ retrieve owner metrics """
        prop = ApiProperties.api_properties['OWNERS']['properties']['metrics']
        ro = RequestObject()
        ro.set_description('load global metrics')
        ro.set_http_method(prop['http_method'])
        ro.set_owner_allowed(prop['owner_allowed'])
        ro.set_resource_pagination(prop['pagination'])
        ro.set_request_uri(prop['uri'])
        ro.set_resource_type(ResourceType.OWNER_METRICS)
        api_response = self.tc.api_request(ro)

        metrics = []
        if api_response.headers['content-type'] == 'application/json':
            api_response_dict = api_response.json()
            if api_response_dict['status'] == 'Success':
                data = api_response_dict['data']['ownerMetric']
                for item in data:
                    metrics.append(parse_metrics(item))

        return metrics  # if class is called directly

    def retrieve_members(self):
        """ retrieve owner members """
        prop = ApiProperties.api_properties['OWNERS']['properties']['members']
        ro = RequestObject()
        ro.set_description('load owner members')
        ro.set_http_method(prop['http_method'])
        ro.set_owner_allowed(prop['owner_allowed'])
        ro.set_resource_pagination(prop['pagination'])
        ro.set_request_uri(prop['uri'])
        ro.set_resource_type(ResourceType.OWNER_MEMBERS)
        api_response = self.tc.api_request(ro)

        members = []
        if api_response.headers['content-type'] == 'application/json':
            api_response_dict = api_response.json()
            if api_response_dict['status'] == 'Success':
                data = api_response_dict['data']['user']
                for item in data:
                    members.append(parse_member(item))

        return members  # if class is called directly

    def retrieve_mine(self):
        """ retrieve owner mine """

        prop = ApiProperties.api_properties['OWNERS']['properties']['mine']
        ro = RequestObject()
        ro.set_description('load owner mine')
        ro.set_http_method(prop['http_method'])
        ro.set_owner_allowed(prop['owner_allowed'])
        ro.set_resource_pagination(prop['pagination'])
        ro.set_request_uri(prop['uri'])
        ro.set_resource_type(ResourceType.OWNERS)

        data_set = self.tc.api_response_handler(self, ro)
        for obj in data_set:
            self.add_obj(obj)


class OwnerFilterObject(FilterObject):
    """ """

    def __init__(self, tc_obj):
        """ """
        super(OwnerFilterObject, self).__init__(tc_obj)
        # self._owners = []

        # define properties for resource type
        self._resource_type = ResourceType.OWNERS
        self._resource_properties = ApiProperties.api_properties[self._resource_type.name]['properties']

        #
        # add_obj filter methods
        #
        for method_name in self._resource_properties['filters']:
            method = getattr(OwnerFilterMethods, method_name)
            setattr(self, method_name, types.MethodType(method, self))

    @property
    def default_request_object(self):
        """ default request when no filter is provided """
        request_object = RequestObject()
        request_object.set_description('filter by owner')
        request_object.set_http_method(self._resource_properties['base']['http_method'])
        request_object.set_owner_allowed(self._resource_properties['base']['owner_allowed'])
        request_object.set_request_uri(self._resource_properties['base']['uri'])
        request_object.set_resource_pagination(self._resource_properties['base']['pagination'])
        request_object.set_resource_type(self._resource_type)

        return request_object
