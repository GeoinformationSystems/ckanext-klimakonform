import ckan.plugins as p
import ckan.lib.helpers as h

import ckan.lib.base as base


class KlimakonformController(base.BaseController):

    def legal_notice(self):
        return base.render('home/legal_notice.html')