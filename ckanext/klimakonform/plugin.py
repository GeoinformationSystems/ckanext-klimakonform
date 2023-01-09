# encoding: utf-8

from cgi import test
from doctest import ELLIPSIS_MARKER
from re import search
import ckan.plugins as plugins
import ckantoolkit as tk
from ckan import model
from ckanext.spatial.plugin.__init__ import SpatialQuery
import ckan.plugins.toolkit as toolkit
from helpers import update_resources, set_of_time_periods, set_of_seasons, \
        set_of_themes, add_gemet_filter, get_gemet_concept_from_keyword, get_concept_relatives, \
        get_related_concepts_for_keyword
import yaml
from geopy.geocoders import Nominatim
from .database_model import SearchQuery
import logging
import rdflib


from ckanext.discovery.plugins.search_suggestions.interfaces import \
    ISearchTermPreprocessor

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

config = tk.config

gemet_rdf = './public/gemet_mod.rdf'

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

def gemet_filter(search_params):
    return add_gemet_filter(search_params)

def _is_user_text_search(context, query):
    '''
    Decide if a search query is a user-initiated text search.
    '''
    # See https://github.com/ckan/ckanext-searchhistory/issues/1#issue-32079108
    try:
        # log.debug('context-controller: {0}, context-action: {1}, query: {2}'.format(context.controller, context.action, query))

        if (
            context.controller in ('dataset', 'home')
            and context.action in ('search','index')
            and query in (':', '*:*', '')
            #or context.action != 'search'
            #or ((query or '').strip() in (':', '*:*'))
        ):
            return False
    except TypeError:
        # Web context not ready. Happens, for example, in paster commands.
        return False
    return True

def get_related_keywords(list_of_tags):
    tags = [tag['name'] for tag in list_of_tags]

    gemet_keywords_uri = [get_related_concepts_for_keyword(rdf, tag) for tag in tags]

    ### Make a flat list containing unique keywords:
    ###
    filtered_list = list(filter(None, gemet_keywords_uri))
    flat_list_with_relatives = [item for sublist in filtered_list for item in sublist]
    unique_list_with_relatives = list(set(flat_list_with_relatives))

    # Remove None values
    unique_without_none = list(filter(None, unique_list_with_relatives))
    # Make parantheses around every keyword because SOLR needs this 
    #TODO: change this to f-strings when using Python 3.X
    extended_keyword_list = [u'({})'.format(i) for i in unique_without_none]
  
    # Create query from extended list of keywords and search for ckan-packages including these keywords
    if len(extended_keyword_list) > 1:
        #fq = u'tags:(Globalstrahlung OR {})'.format(' OR '.join(unique_without_none))
        fq= u'tags:({})'.format(' OR '.join(extended_keyword_list))
    elif len(extended_keyword_list) == 1:
        fq = u'tags:{}'.format(extended_keyword_list[0])
    else:
        # No GEMET keywords entered
        return [[], []]

    # Search for packages with fq
    packges_t = toolkit.get_action('package_search')(
            data_dict={'fq': fq})  
    # Expose top five results
    top_five_results = packges_t['results'][:5]

    # Construct a keyword dictionary for displaying as formated tags in Frontend
    list_of_tag_dicts = []
    for k in unique_without_none:
        tag_dict = {u'vocabulary_id': None, 
                u'state': u'active', 
                u'display_name': k,  #  u'Bodentrockenheit', 
                u'id': None, # u'e3e0f9e7-1e0b-4400-91ed-8e9a1d031f06'
                u'name': k } # u'Bodentrockenheit'
        list_of_tag_dicts.append(tag_dict)


    return [list_of_tag_dicts, top_five_results]


class KlimakonformPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(ISearchTermPreprocessor)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(SpatialQuery)

    # IConfigurable
    def configure(self, config):
        log.debug("Initializing RDF-schema of GEMET vocab")
        rdf_file = '/usr/lib/ckan/test_env/src/ckanext-klimakonform/ckanext/klimakonform/public/gemet_mod.rdf'
        g = rdflib.Graph()
        skos = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
        global rdf
        rdf = g.parse(rdf_file, namespace=skos)
        return 
    
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
                'get_unique_set_of_themes': get_unique_set_of_themes,
                'get_related_keywords': get_related_keywords}
    
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
            if not _is_user_text_search(toolkit.c, search_params['q']):
                """API search - do not enable spatial search to keep control"""
                log.debug("No user search - disabling spatial search filter")
                return search_params
            else:
                log.debug("User search - enabling spatial search filter")
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
                            return search_params_filtered
                            #search_params_with_gemet = gemet_filter(search_params_filtered)
                            #log.debug('Search_params_filtered_with_bbox : {}'.format(search_params_with_gemet))
                            #return search_params_with_gemet
                        else:
                            log.debug('Found coordinates in Database. Location is not in filter bbox. \
                                    Turning off the spatial search')
                            #search_params_with_gemet = gemet_filter(search_params)
                            #return search_params_with_gemet
                            return search_params
                    else:
                        for term in terms:
                            '''No entry found in DB, try geocoding search-query...'''
                            log.debug('Calling Nominatim API for search query')
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
                                        #search_params_with_gemet = gemet_filter(search_params_filtered)

                                        log.debug('Search_params_filtered_with_bbox : {}'.format(search_params_with_gemet))         
                                        return search_params_filtered
                                        #return search_params_with_gemet
                                    else: 
                                        log.debug('Found coordinates by calling Nomiatim API. Location is not in filter bbox. \
                                                    Turning off the spatial search')
                                        pass
                                else:
                                    """ Turn on gemet filter, if no spatial filter is used"""
                                    #log.debug("Turning on gemet query enrichment")
                                    #return gemet_filter(search_params)
                                    return search_params
                            except Exception as e: 
                                log.debug('Failed to find geolocation because {}'.format(e))
            

            if  _is_user_text_search(toolkit.c, search_params['q']):
                #search_params_with_gemet = gemet_filter(search_params)
                #log.debug('User search final')
                #return search_params_with_gemet
                return search_params
        else:
            log.debug('No User search final')
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
    
