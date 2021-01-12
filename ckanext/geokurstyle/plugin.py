import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.base as base
import routes.mapper


class GeokurstylePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)    
    plugins.implements(plugins.IRoutes)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'geokurstyle')

    def before_map(self, route_map):
        with routes.mapper.SubMapper(route_map,
                controller='ckanext.geokurstyle.plugin:GeokurStyleController') as m:
            m.connect('legalNotice', '/legalNotice', action='legalNotice')
        return route_map

    def after_map(self, route_map):
        return route_map


class GeokurStyleController(base.BaseController):
    def legalNotice(self):
        return base.render('/legalNotice.html')

    