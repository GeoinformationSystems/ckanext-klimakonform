# -*- coding: utf-8 -*-
import ckan.plugins as plugins
from ckanext.discovery.plugins.search_suggestions.interfaces import \
    ISearchTermPreprocessor
import ckantoolkit as tk
from ckanext.spatial.plugin.__init__ import SpatialQuery
import ckan.plugins.toolkit as toolkit
from helpers import update_resources, set_of_time_periods, set_of_seasons, set_of_themes
import yaml
from geopy.geocoders import Nominatim
import logging

from sqlalchemy import Column, DDL, event, ForeignKey, Index, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from model import Object

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

config = tk.config
Base = declarative_base(cls=Object)



geolocator = Nominatim(user_agent="http")

def load_rekis_file_yaml_to_dict():
    # TODO: change to relative path
    path = '/usr/lib/ckan/test_env/src/ckanext-klimakonform/ckanext/klimakonform/public/rekis_ascii_file_naming.yml' 
    file_dict = yaml.safe_load(open(path))
    return file_dict

def update_resource_info(resources):
    update_resources(resources)
    return resources

def get_unique_set_of_time_periods(resources):
    time_periods = set_of_time_periods(resources)
    return time_periods

def get_unique_set_of_seasons(resources):
    seasons = set_of_seasons(resources)
    return seasons

def get_unique_set_of_themes(resources):
    themes = set_of_themes(resources)
    return themes

class KlimakonformPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(ISearchTermPreprocessor)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(SpatialQuery)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'ckanext-klimakonform')
        toolkit.add_resource('public', 'ckanext-klimakonform')

    # ITemplateHelpers
    def get_helpers(self):
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        from ckanext.klimakonform import helpers 
        return {'rekis_file_dict': load_rekis_file_yaml_to_dict,
                'update_resource_info': update_resource_info,
                'get_unique_set_of_time_periods': get_unique_set_of_time_periods,
                'get_unique_set_of_seasons': get_unique_set_of_seasons,
                'get_unique_set_of_themes': get_unique_set_of_themes}
    
    # IRoutes
    
    def before_map(self, map):

        return map

    def after_map(self, map):        
        map.connect('legal_notice', '/legal-notice',
                    controller='ckanext.klimakonform.controller:KlimakonformController',
                    action='legal_notice')
        return map

    
    #Spatial Query Implementation

    def before_search(self, search_params):
        '''
        This function geocodes every search-query and adds it as additional query-param
        before passing the parameter to the search interfaces
        '''

        #Todo: add caching of geocoded results
        context = SpatialQuery()       
        
        if 'q' in search_params:
            log.debug('Looking for geolocation from search query')
            log.debug('org_search_params = {}'.format(search_params))

            try:
                query_geocoded = geolocator.geocode(search_params['q'])

                if query_geocoded is not None:
                    coords = '{0}+{1}'.format(query_geocoded.latitude, query_geocoded.longitude)

                    bbox = '{0},{1},{0},{1}'.format(query_geocoded.longitude, query_geocoded.latitude)
                    log.debug('Found following coordinates and appended it to query: {}'.format(coords))

                    search_params['extras']['ext_bbox'] = bbox
                    search_params['extras']['ext_prev_extent'] = bbox
                    search_params['q'] = u''
                    search_params_filtered = SpatialQuery.before_search(context, search_params)
                    log.debug('search_params_filtered_with_bbox : {}'.format(search_params))
                    return search_params_filtered
            except Exception as e: 
                log.debug('Failed to find geolocation because {}'.format(e))
        
        return search_params
    

    # ISearchTermPreprocessor

    def preprocess_search_term(self, term):
        '''
        Preprocess and filter a search term.

        ``term`` is a search term extracted from a user's search query.

        If this method returns a false value then the term is ignored
        w.r.t. search suggestions. This is useful for filtering stop
        words and unwelcome content.

        Otherwise the return value of the method is used instead of the
        original search term. In most cases you simply return the value
        unchanged.

        Note that all of this only affects the generation of the search
        suggestions but not the search itself.
        '''
        return term    
    
