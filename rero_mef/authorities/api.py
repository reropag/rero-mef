# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating authorities."""

from invenio_search.api import RecordsSearch

from ..api import AuthRecord
from .fetchers import bnf_id_fetcher, gnd_id_fetcher, mef_id_fetcher, \
    rero_id_fetcher, viaf_id_fetcher
from .minters import bnf_id_minter, gnd_id_minter, mef_id_minter, \
    rero_id_minter, viaf_id_minter
from .providers import BnfProvider, GndProvider, MefProvider, ReroProvider, \
    ViafProvider


class ViafSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-viaf-person-v0.0.1'


class BnfSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-bnf-person-v0.0.1'


class ReroSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-rero-person-v0.0.1'


class GndSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-gnd-person-v0.0.1'


class MefSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = 'authorities-mef-person-v0.0.1'


class MefRecord(AuthRecord):
    """Mef Authority class."""

    minter = mef_id_minter
    fetcher = mef_id_fetcher
    provider = MefProvider

    @classmethod
    def build_ref_string(cls, agency_pid, agency):
        """Build ref string."""
        from flask import current_app
        with current_app.app_context():
            url = current_app.config.get('JSONSCHEMAS_HOST')
            ref_string = 'http://' + url + '/api/' + agency + '/' + agency_pid
            return ref_string

    @classmethod
    def get_mef_by_agency_pid(cls, agency_pid, agency, with_deleted=False):
        """Get mef record by agency pid value."""
        key = agency + '.identifier_for_person'
        search = MefSearch()
        result = (
            search.filter('term', **{key: agency_pid})
            .source()
            .execute()
            .to_dict()
        )
        try:
            mef_pid = result['hits']['hits'][0]['_source']['pid']
            return cls.get_record_by_pid(mef_pid)
        except IndexError:
            return None

    @classmethod
    def get_mef_by_viaf_pid(cls, viaf_pid, with_deleted=False):
        """Get mef record by agency pid value."""
        search = MefSearch()
        result = (
            search.filter('term', viaf=viaf_pid).source().execute().to_dict()
        )
        try:
            mef_pid = result['hits']['hits'][0]['_source']['pid']
            return cls.get_record_by_pid(mef_pid)
        except IndexError:
            return None

    @classmethod
    def mef_sync(
        cls,
        agency=None,
        agency_pid=None,
        viaf_record=None,
        action=None,
        delete_pid=True,
        dbcommit=False,
        reindex=False,
        **kwargs
    ):
        """Create, update or delete Mef record."""
        if viaf_record:
            viaf_pid = viaf_record['viaf_pid']
            mef_record_from_viaf = cls.get_mef_by_viaf_pid(
                viaf_pid=viaf_pid, with_deleted=False
            )
            mef_record_from_agency = cls.get_mef_by_agency_pid(
                agency_pid=agency_pid, agency='viaf', with_deleted=False
            )
            ref_string = cls.build_ref_string(
                agency=agency, agency_pid=agency_pid
            )
            if action == 'update':
                if mef_record_from_viaf and mef_record_from_agency:
                    mef_record_from_viaf.reindex()
                elif mef_record_from_viaf and not mef_record_from_agency:
                    mef_record_from_viaf[agency] = {'$ref': ref_string}
                    mef_record_from_viaf.update(
                        mef_record_from_viaf,
                        dbcommit=dbcommit,
                        reindex=reindex,
                    )
                elif not mef_record_from_viaf and not mef_record_from_agency:
                    from flask import current_app
                    with current_app.app_context():
                        url = current_app.config.get('JSONSCHEMAS_HOST')
                        data = {
                            '$schema': 'http://' + url + '/schemas/'
                            'authorities/mef-person-v0.0.1.json',
                            agency: {'$ref': ref_string},
                            'viaf': viaf_pid,
                        }
                        cls.create(
                            data,
                            id_=None,
                            delete_pid=True,
                            dbcommit=dbcommit,
                            reindex=reindex,
                        )
                else:
                    pass
                    # exception to be throw
            elif action == 'delete':
                if mef_record_from_viaf:
                    mef_record_from_viaf.pop(agency, None)
                    mef_record_from_viaf.update(
                        mef_record_from_viaf,
                        dbcommit=dbcommit,
                        reindex=reindex,
                    )
                # toto: delete mef record if last agency
            else:
                print('mef sync action not yet implemented:', action)
                pass


class GndRecord(AuthRecord):
    """Gnd Authority class."""

    minter = gnd_id_minter
    fetcher = gnd_id_fetcher
    provider = GndProvider
    agency = 'gnd'
    agency_pid_type = 'gnd_pid'


class ReroRecord(AuthRecord):
    """Rero Authority class."""

    minter = rero_id_minter
    fetcher = rero_id_fetcher
    provider = ReroProvider
    agency = 'rero'
    agency_pid_type = 'rero_auth_pid'


class BnfRecord(AuthRecord):
    """Bnf Authority class."""

    minter = bnf_id_minter
    fetcher = bnf_id_fetcher
    provider = BnfProvider
    agency = 'bnf'
    agency_pid_type = 'bnf_pid'


class ViafRecord(AuthRecord):
    """Viaf Authority class."""

    minter = viaf_id_minter
    fetcher = viaf_id_fetcher
    provider = ViafProvider

    @classmethod
    def get_viaf_by_agency_pid(cls, pid, pid_type, with_deleted=False):
        """Get viaf record by agency pid value."""
        search = ViafSearch()
        result = (
            search.filter('term', **{pid_type: pid})
            .source()
            .execute()
            .to_dict()
        )
        try:
            viaf_pid = result['hits']['hits'][0]['_source']['pid']
            return cls.get_record_by_pid(viaf_pid)
        except IndexError:
            return None

    @classmethod
    def create_or_update(
        cls,
        data,
        id_=None,
        delete_pid=True,
        dbcommit=False,
        reindex=False,
        vendor=None,
        **kwargs
    ):
        """Create or update viaf record."""
        pid = data['viaf_pid']
        record = cls.get_record_by_pid(pid)
        if record:
            data['$schema'] = record['$schema']
            data['pid'] = record['pid']
            record.clear()
            record.update(data, dbcommit=True, reindex=True)
            return record, 'update'
        else:
            created_record = cls.create(
                data,
                id_=None,
                delete_pid=True,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            return created_record, 'create'
