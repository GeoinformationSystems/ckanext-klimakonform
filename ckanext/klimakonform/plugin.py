import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit



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
        return {'klimakonform_test_template_helper_function': helpers.test_template_helper_function}
    
    # IRoutes
    
    def before_map(self, map):

        return map

    def after_map(self, map):        
        map.connect('legal_notice', '/legal-notice',
                    controller='ckanext.klimakonform.controller:KlimakonformController',
                    action='legal_notice')
        return map

    
