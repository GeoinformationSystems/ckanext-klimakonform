import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from helpers import update_resources, set_of_time_periods, set_of_seasons, set_of_themes
import yaml

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

    
