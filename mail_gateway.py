# -*- coding: utf-8 -*-
##############################################################################
#
#    fetchmail_parsing module for OpenERP, Allows to map variable names inside email body to fields on related model
#    Copyright (C) 2011 SYLEAM Info Services (<http://www.Syleam.fr/>)
#              Sylvain Garancher <sylvain.garancher@syleam.fr>
#
#    This file is a part of fetchmail_parsing
#
#    fetchmail_parsing is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    fetchmail_parsing is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
import re
import email
import tools
import xmlrpclib


class email_server_tools(osv.osv_memory):
    _inherit = 'email.server.tools'

    def process_email(self, cr, uid, model, message, custom_values=None, attach=True, context=None):
        if context is None:
            context = {}

        if custom_values is None:
            custom_values = {}

        model_obj = self.pool.get(model)

        if isinstance(message, xmlrpclib.Binary):
            message = str(message.data)

        if isinstance(message, unicode):
            message = message.encode('utf-8')

        msg_txt = email.message_from_string(message)

        # Retrieve the body part of the message
        body = ''
        if not msg_txt.is_multipart() or 'text/plain' in msg_txt.get('Content-Type'):
            encoding = msg_txt.get_content_charset()
            body = msg_txt.get_payload(decode=True)
            if 'text/html' in msg_txt.get('Content-Type'):
                body = tools.html2plaintext(body)

            body = tools.ustr(body, encoding)

        # Retrieve information about the fields
        field_informations = model_obj.fields_get(cr, uid, [], context=context)
        # Search for patterns for specific fields
        for field_name, pattern in context.get('mapping_fields', {}):
            # Add the re.S flag to allow multi line matching data
            field_data = re.search(pattern, body, re.S)
            # If the pattern matches, add its value in custom values
            if field_data:
                # Retrieve data sent by email
                field_value = field_data.group(1)

                # If we fill a m2o field, call name_search
                if field_informations[field_name]['type'] == 'many2one':
                    name_search_value = self.pool.get(field_informations[field_name]['relation']).name_search(cr, uid, field_value, context=context)
                    if name_search_value:
                        field_value = name_search_value[0][0]

                # Add data in custom_values
                custom_values[field_name] = field_value.replace('&#13;', '')

        super(email_server_tools, self).process_email(cr, uid, model, message, custom_values=custom_values, attach=attach, context=context)

email_server_tools()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
