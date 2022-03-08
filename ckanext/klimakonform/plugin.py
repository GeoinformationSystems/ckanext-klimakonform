# -*- coding: utf-8 -*-
from re import I
import ckan.plugins as plugins
import ckantoolkit as tk
from ckanext.spatial.plugin.__init__ import SpatialQuery
import ckan.plugins.toolkit as toolkit
from helpers import update_resources, set_of_time_periods, set_of_seasons, set_of_themes
import yaml
from geopy.geocoders import Nominatim
from .database_model import SearchQuery
import logging


from ckanext.discovery.plugins.search_suggestions.interfaces import \
    ISearchTermPreprocessor

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

config = tk.config


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
        context = SpatialQuery()    
        coords_in_filter_bbox = False 

        # bbox = min Longitude , min Latitude , max Longitude , max Latitude 
        #bbox for germany: 5.564941, 47.141223, 15.571542, 55.059744
        bbox_filter = [5.564941, 47.141223, 15.571542, 55.059744]   
  
        
        if 'q' in search_params:
            terms = search_params['q'].split(' ')

            # Looping through query terms and if first match with base return stored coord values
            db_query_results = SearchQuery(search_params).get_results_if_exists()

            if db_query_results is not None:
                db_coords = db_query_results.split(',')
                db_coords_float = [float(item)for item in db_coords]

                if  db_coords_float[0] >= bbox_filter[0] and \
                    db_coords_float[1] >= bbox_filter[1] and \
                    db_coords_float[2] <= bbox_filter[2] and \
                    db_coords_float[3] <= bbox_filter[3]:
                    coords_in_filter_bbox = True                    
                
                if coords_in_filter_bbox:
                    '''Entry found in database'''
                    search_params['extras']['ext_bbox'] = db_query_results
                    search_params['extras']['ext_prev_extent'] = db_query_results
                    search_params['q'] = u''
                    search_params_filtered = SpatialQuery.before_search(context, search_params)
                    
                    log.debug('Search_params_filtered_with_bbox : {}'.format(search_params))
                    return search_params_filtered
                else:
                    log.debug('Found coordinates in Database. Location is not in filter bbox. \
                             Turning off the spatial search')
                    return search_params
            else:
                for term in terms:
                    '''No entry found in DB, try geocoding search-query...'''
                    log.debug('Calling Nominatim API for search query')
                    log.debug('Following query {}'.format(term))
                    try:
                        query_geocoded = geolocator.geocode(term)

                        if query_geocoded is not None:
                            if  query_geocoded.longitude >= bbox_filter[0] and \
                                query_geocoded.latitude >= bbox_filter[1] and \
                                query_geocoded.longitude <= bbox_filter[2] and \
                                query_geocoded.latitude <= bbox_filter[3]:
                                coords_in_filter_bbox = True

                            if coords_in_filter_bbox:
                                bbox = '{0},{1},{0},{1}'.format(query_geocoded.longitude, query_geocoded.latitude)
                                log.debug('Found following coordinates and appended it to query: {}'.format(bbox))

                                search_params['extras']['ext_bbox'] = bbox
                                search_params['extras']['ext_prev_extent'] = bbox
                                search_params['q'] = term

                                #Store result into db
                                SearchQuery(search_params).store()

                                search_params['q'] = u''
                                search_params_filtered = SpatialQuery.before_search(context, search_params)
                                
                                return search_params_filtered
                            else: 
                                log.debug('Found coordinates by calling Nomiatim API. Location is not in filter bbox. \
                                            Turning off the spatial search')
                                pass
                        else:
                            pass
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
    
