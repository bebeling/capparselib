#!/usr/bin/env python
# coding: utf-8
"""
    capparselib.CAPParser
    ~~~~~~~~~~~~~

    :copyright: Kelvin Nicholson (kelvin@kelvinism.com), see AUTHORS for more details
    :license: MOZILLA PUBLIC LICENSE (v1.1), see LICENSE for more details
"""

import os
from lxml import objectify, etree


ATOM_URI = 'http://www.w3.org/2005/Atom'
CAP1_1_URN = 'urn:oasis:names:tc:emergency:cap:1.1'
CAP1_2_URN = 'urn:oasis:names:tc:emergency:cap:1.2'
EDXL_DE_URN = 'urn:oasis:names:tc:emergency:EDXL:DE:1.0'
XML_TYPE = None

CAPLIBRARY_PATH = os.path.realpath(os.path.dirname(__file__))

# Do not put event_code, eventCode
CAP_MAPPINGS = {
    'title': 'cap_headline',
    'summary': 'cap_description',
    'description': 'cap_description',
    'expires': 'cap_expires',
    'responseType': 'cap_response_type',
    'severity': 'cap_severity',
    'urgency': 'cap_urgency',
    'onset': 'cap_effective',
    'web': 'cap_link',
    'category': 'cap_category',
    'certainty': 'cap_certainty',
    'event': 'cap_event',
    'headline': 'cap_headline',
    'instruction': 'cap_instruction',
    'language': 'cap_language',
    'link': 'cap_link',
    'author': 'cap_sender',
    'areaDesc': 'cap_area_description',
    'effective': 'cap_effective',
    'sender': 'cap_sender',
    'contact': 'cap_contact',
    'senderName': 'cap_sender_name',
    'note': 'cap_note',
    'code': 'cap_code',
    'id': 'cap_id',
    'identifier': 'cap_id',
    'msgType': 'cap_message_type',
    'scope': 'cap_scope',
    'sent': 'cap_sent',
    'status': 'cap_status',
    'restriction': 'cap_restriction',
    'source': 'cap_source',
    'incidents': 'cap_incidents',
    'references': 'cap_references',
    'addresses': 'cap_addresses',
}

XML_TYPE_XSD_MAPPINGS = {
    'ATOM': 'schema/atom.xsd',
    'CAP1_2': 'schema/cap12_extended.xsd',
    'CAP1_1': 'schema/cap11_extended.xsd',
    'EDXL_DE': 'schema/edxl-de.xsd',
    'RSS': 'schema/rss-2_0.xsd',
}


class CAPParser(object):
    def __init__(self, raw_cap_xml=None, recover=False):
        self.xml = raw_cap_xml
        self.recover = recover
        self.objectified_xml = None
        self.cap_xml_type = None
        self.alert_list = []
        self.load()

    def process_area(self, info_dict):
        new_area_list = []
        for area_obj in info_dict['area']:
            new_area_dict = {}
            if hasattr(area_obj, 'circle'):
                circle_list = []
                for circle in area_obj['circle']:
                    circle_list.append(circle)
                new_area_dict['circle'] = circle_list
            if hasattr(area_obj, 'polygon'):
                polygon_list = []
                for polygon in area_obj['polygon']:
                    polygon_list.append(polygon)
                new_area_dict['polygon'] = polygon_list
            if hasattr(area_obj, 'geocode'):
                geocode_list = []
                for geocode in area_obj['geocode']:
                    geocode_list.append({"valueName": unicode(geocode.valueName),
                                         "value": unicode(geocode.value)})
                new_area_dict['geocodes'] = geocode_list
            new_area_dict['area_description'] = unicode(area_obj.areaDesc)
            new_area_list.append(new_area_dict)
        info_dict['cap_area'] = new_area_list
        info_dict.pop('area')  # override the area value.
        return info_dict

    def process_category(self, info_dict):
        category_list = []
        for category in info_dict['category']:
            category_list.append(category)
        info_dict['cap_category'] = category_list
        info_dict.pop('category')
        return info_dict

    def process_event_code(self, info_dict):
        event_code_list = []
        for event_code in info_dict['eventCode']:
            event_code_list.append({"valueName": unicode(event_code.valueName),
                                    "value": unicode(event_code.value)})
        info_dict['cap_event_code'] = event_code_list
        info_dict.pop('eventCode')
        return info_dict

    def process_parameter(self, info_dict):
        parameter_list = []
        for parameter in info_dict['parameter']:
            parameter_list.append({"valueName": unicode(parameter.valueName),
                                   "value": unicode(parameter.value)})
        info_dict['cap_parameter'] = parameter_list
        info_dict.pop('parameter')
        return info_dict

    def process_resource(self, info_dict):
        resource_list = []
        for resource in info_dict['resource']:
            resource_list.append({"resourceDesc": unicode(resource.resourceDesc),
                                  "mimeType": unicode(resource.mimeType),
                                  "uri": resource.uri})
        info_dict['cap_resource'] = resource_list
        info_dict.pop('resource')
        return info_dict

    def process_response_type(self, info_dict):
        response_list = []
        for response in info_dict['responseType']:
            response_list.append(response)
        info_dict['cap_response_type'] = response_list
        info_dict.pop('responseType')
        return info_dict

    def parse_alert(self, alert):
        alert_dict = alert.__dict__
        code_list = []
        for code_element in alert.code:
            code_list.append(code_element)
        alert_dict['code'] = code_list

        for alert_key in alert_dict.keys():
            if alert_key in CAP_MAPPINGS:
                new_alert_key = CAP_MAPPINGS[alert_key]
                alert_dict[new_alert_key] = alert_dict.pop(alert_key)

        info_item_list = []
        for info_item in alert.info:
            info_dict = info_item.__dict__

            if 'area' in info_dict.keys():
                info_dict = self.process_area(info_dict)

            if 'category' in info_dict.keys():
                info_dict = self.process_category(info_dict)

            if 'eventCode' in info_dict.keys():
                info_dict = self.process_event_code(info_dict)

            if 'parameter' in info_dict.keys():
                info_dict = self.process_parameter(info_dict)

            if 'resource' in info_dict.keys():
                info_dict = self.process_resource(info_dict)

            if 'responseType' in info_dict.keys():
                info_dict = self.process_response_type(info_dict)

            for info_key in info_dict.keys():
                if info_key in CAP_MAPPINGS:
                    new_info_key = CAP_MAPPINGS[info_key]
                    info_dict[new_info_key] = unicode(info_dict.pop(info_key))

            info_item_list.append(info_dict)

        alert_dict['cap_info'] = info_item_list
        alert_dict.pop('info')
        return alert_dict

    def determine_cap_type(self):
        try:
            parser = etree.XMLParser(recover=self.recover, remove_blank_text=True)  #recovers from bad characters.
            tree = etree.fromstring(self.xml, parser)
        except:
            raise Exception("Invalid XML")

        ns_list = tree.nsmap.values()
        if ATOM_URI in ns_list:
            self.cap_xml_type = 'ATOM'
        elif CAP1_2_URN in ns_list:
            self.cap_xml_type = 'CAP1_2'
        elif CAP1_1_URN in ns_list:
            self.cap_xml_type = 'CAP1_1'
        elif EDXL_DE_URN in ns_list:
            self.cap_xml_type = 'EDXL_DE'
        else:  # probably RSS TODO Unfinished
            self.cap_xml_type = 'RSS'

    def get_objectified_xml(self):
        xsd_filename = XML_TYPE_XSD_MAPPINGS[self.cap_xml_type]
        with open(os.path.join(CAPLIBRARY_PATH, xsd_filename)) as f:
            doc = etree.parse(f)
            schema = etree.XMLSchema(doc)
            try:
                parser = objectify.makeparser(schema=schema, recover=self.recover, remove_blank_text=True)
                a = objectify.fromstring(self.xml, parser)
            except etree.XMLSyntaxError, e:
                raise Exception("Error objectifying XML")
        return a

    def get_alert_list(self):
        alerts = []
        objectified_xml = self.get_objectified_xml()
        if self.cap_xml_type == 'ATOM':
            for alert in objectified_xml.entry:
                alerts.append(alert.content.getchildren()[0])
        elif self.cap_xml_type == 'CAP1_1' or self.cap_xml_type == 'CAP1_2':
            alerts.append(objectified_xml)
        elif self.cap_xml_type == 'EDXL_DE':
            for obj in objectified_xml.contentObject:
                alert = obj.xmlContent.embeddedXMLContent.getchildren()[0]
                alerts.append(alert)
        return alerts

    def load(self):
        if self.xml:
            self.determine_cap_type()
            for alert in self.get_alert_list():
                self.alert_list.append(self.parse_alert(alert))

    def as_dict(self):
        return self.alert_list
