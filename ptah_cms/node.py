""" Node implementation """
import uuid
import pyramid_sqla
import sqlalchemy as sqla
import ptah.security
from zope import interface
from ptah.utils import JsonType, JsonDictType, JsonListType

from interfaces import INode

Base = pyramid_sqla.get_base()
Session = pyramid_sqla.get_session()


class Node(Base, ptah.security.PermissionsMapSupport):
    interface.implements(INode, 
                         ptah.security.IOwnersAware,
                         ptah.security.ILocalRolesAware)

    __tablename__ = 'ptah_cms_nodes'

    __id__ = sqla.Column('id', sqla.Integer, primary_key=True)
    __uuid__ = sqla.Column('uuid', sqla.String)
    __type_id__ = sqla.Column('type', sqla.String)
    __parent_id__ = sqla.Column('parent', sqla.String,sqla.ForeignKey(__uuid__))

    __owners__ = sqla.Column('owner', JsonListType(), default=[])
    __local_roles__ = sqla.Column('roles', JsonDictType(), default={})
    __permissions__ = sqla.Column('permissions', JsonListType(), default=[])

    __children__ = sqla.orm.relationship(
        'Node',
        backref=sqla.orm.backref('__parent_ref__',remote_side=[__uuid__]))

    __mapper_args__ = {'polymorphic_on': __type_id__}

    __parent__ = None
    __uuid_generator__ = None

    def __init__(self, **kw):
        self.__owners__ = []
        self.__local_roles__ = {}
        self.__permissions__ = []

        for attr, value in kw.items():
            setattr(self, attr, value)

        if '__parent__' in kw and kw['__parent__'] is not None:
            self.__parent_id__ = kw['__parent__'].__uuid__

        try:
            self.__uuid__ = self.__uuid_generator__()
        except TypeError: # pragma: no cover
            raise TypeError(
                'Subclass of Node has to override __uuid_generator__')
