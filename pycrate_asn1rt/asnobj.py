# -*- coding: UTF-8 -*-
#/**
# * Software Name : pycrate
# * Version : 0.1
# *
# * Copyright © 2017. Benoit Michau. ANSSI.
# *
# * This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License
# * as published by the Free Software Foundation; either version 2
# * of the License, or (at your option) any later version.
# * 
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# * 
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# * 02110-1301, USA.
# *
# *--------------------------------------------------------
# * File Name : pycrate_asn1rt/asnobj.py
# * Created : 2017-01-31
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

from .utils   import *
from .err     import *
from .refobj  import *
from .dictobj import *
from .setobj  import *
from .codecs  import *


ASN1Obj_docstring = """
Common object attributes:
    
    - name: str, the identifier of the object
    
    - mode: str (MODE_*), the mode of the object after compilation.
        - MODE_TYPE : ASN.1 subtype or subclass
        - MODE_VALUE: ASN.1 value
        - MODE_SET  : ASN.1 set of values
    
    - param: bool, True in case the object is a parameterized one.
        Parameterized objects are "empty" and mainly useless for encoding / decoding.
        They are still required to keep track of object references and tag chain.
    
    - tag: None or tuple, contains the tagging of the ASN.1 type.
        If defined, it has the following format:
        (tag value (int),
         tag class (str in TAG_CONTEXT_SPEC / TAG_PRIVATE / TAG_APPLICATION / TAG_UNIVERSAL),
         tag mode (str in TAG_IMPLICIT / TAG_EXPLICIT))
    
    - typeref: None or ASN1Ref, provides the reference to the subtype of the object 
        in case it derives from another user-defined one (and not a native one).
    
    - tr: None or ASN1Obj, provides the actual subtype object
    
    - cont: type-dependent.
    
    - root: None or list of str, provides the identifiers of the root content if 
        defined.
    
    - ext: None or list of str, provides the identifiers of the extended content if
        defined.
    
    - val: None for MODE_TYPE,
           single_value (type-dependent) for MODE_VALUE,
           ASN1Set for MODE_SET.

Attributes for object generic constraints:
    
    - const_val: None or ASN1Set, provides the set of values that constraints the type
    
    - const_tab: None or ASN1Obj (MODE_SET), provides the CLASS set for table lookup
    
    - const_tab_id: None or str, only set if const_tab is set,
        provides the identifier that corresponds to self in const_tab
    
    - const_tab_at: None or tuple of str, only set if const_tab is set,
        provides the path of identifiers to which self must refer for the table lookup in const_tab

Attributes defined for components of a constructed or CLASS type:
    
    - parent: None or ASN1Obj, indicates the parent ASN.1 object container
    
    - opt: bool, indicates if the component is OPTIONAL
    
    - def: None or single value, indicates the DEFAULT value
    
    - uniq: bool, indicates if the component is UNIQUE
    
    - group: None or int, indicates the extension group index for grouped extended components

Special attributes that exists only for some objects:
    
    - root_mand (for SEQUENCE, SET, CLASS)
    - root_opt (for SEQUENCE, SET, CLASS)
    - cont_rev (for ENUM)
    - cont_tags (for CHOICE, SEQUENCE, SET)
    - ext_ident (for CHOICE, SEQUENCE, SET)
    - ext_group (for CHOICE, SEQUENCE, SET)
    - ext_group_obj (for SEQUENCE, SET)
    - ext_nest (for SEQUENCE, SET)
    - defby (for ANY)

Attributes for object specific constraints:
    
    - const_sz (for BIT STRING, OCTET STRING, *String, SEQUENCE OF, SET OF)
    - const_ind (for ENUM and CHOICE)
    - const_cont (for BIT STRING, OCTET STRING)
    - const_cont_enc (for BIT STRING, OCTET STRING)
    - const_alpha (for *String)

Attributes used at run-time:
    
    - struct: None or pycrate.elt.Element instance, provides the complete 
        structure of the transfer syntax with, generated when encoding and 
        decoding the object when using from_*_ws() and to_*_ws() methods.
"""

class ASN1Obj(Element):
    
    # in order to disable any asnlog() during the runtime
    _SILENT = False
    
    # this enables object verification during Python module initialization
    _SAFE_INIT   = True
    # this enables object value verification when using set_val()
    _SAFE_VAL    = True
    # this enables object's constraints verification when using set_val() or 
    # set_val_unsafe()
    _SAFE_BND    = True
    # this enables object's table constraint verification when using set_val() 
    # or set_val_unsafe()
    _SAFE_BNDTAB = True
    
    #--------------------------------------------------------------------------#
    # class attributes, initialization and safe checking methods
    #--------------------------------------------------------------------------#
    
    _name    = ''
    _mode    = MODE_TYPE
    _tag     = None
    _typeref = None
    _tr      = None
    _param   = False
    _parent  = None
    _opt     = False
    _def     = None
    _uniq    = False
    _group   = None
    _cont    = None
    _root    = None
    _ext     = None
    _val     = None
    
    _const_val    = None
    # _const_sz is only defined for types which can have a SIZE constraint
    #_const_sz     = None
    # _const_alpha is only defined for _String subtypes
    #_const_alpha  = None
    # _const_cont is only defined for BIT STRING and OCTET STRING
    #_const_cont   = None
    #_const_cont_enc = None
    _const_tab    = None
    # _const_tab_id and _const_tab_at are only defined if _const_tab is not None
    #_const_tab_id = None
    #_const_tab_at = None
    
    
    TYPE = None
    TAG  = None
    
    def __init__(self, **kwargs):
        if 'name'      in kwargs: self._name    = kwargs['name']
        if 'mode'      in kwargs: self._mode    = kwargs['mode']
        if 'tag'       in kwargs: self._tag     = kwargs['tag']
        if 'typeref'   in kwargs: self._typeref = kwargs['typeref']
        if 'param'     in kwargs: self._param   = kwargs['param']
        if 'opt'       in kwargs: self._opt     = kwargs['opt']
        elif 'default' in kwargs: self._def     = kwargs['default']
        if 'defby'     in kwargs: self._defby   = kwargs['defby']
        if 'uniq'      in kwargs: self._uniq    = kwargs['uniq']
        if 'group'     in kwargs: self._group   = kwargs['group']
    
    def _safechk_obj(self):
        """
        ensures all internal attributes at initialization have the correct format
        """
        # name
        if not isinstance(self._name, str_types):
            raise(ASN1ObjErr('invalid name, {0!r}'.format(self._name)))
        # mode
        if self._mode not in (MODE_TYPE, MODE_SET, MODE_VALUE):
            raise(ASN1ObjErr('{0}: invalid mode, {1!r}'\
                  .format(self.fullname(), self._mode)))
        # tag
        if not isinstance(self._tag, (NoneType, tuple)):
            raise(ASN1ObjErr('{0}: invalid tag, {1!r}'\
                  .format(self.fullname(), self._tag)))
        elif isinstance(self._tag, tuple) and ( \
        len(self._tag) != 3 or \
        not isinstance(self._tag[0], integer_types) or \
        self._tag[1] not in (TAG_CONTEXT_SPEC, TAG_PRIVATE, TAG_APPLICATION, TAG_UNIVERSAL) or \
        self._tag[2] not in (TAG_IMPLICIT, TAG_EXPLICIT)):
            raise(ASN1ObjErr('{0}: invalid tag, {1!r}'\
                  .format(self.fullname(), self._tag)))
        # typeref
        if not isinstance(self._typeref, (NoneType, ASN1Ref)):
            raise(ASN1ObjErr('{0}: invalid typeref, {1!r}'\
                  .format(self.fullname(), self._typeref)))
        # param
        if not isinstance(self._param, bool):
            raise(ASN1ObjErr('{0}: invalid param, {1!r}'\
                  .format(self.fullname(), self._param)))
        # parent
        if not isinstance(self._parent, (NoneType, ASN1Obj)):
            raise(ASN1ObjErr('{0}: invalid parent, {1!r}'\
                  .format(self.fullname(), self._parent)))
        # opt
        if not isinstance(self._opt, bool):
            raise(ASN1ObjErr('{0}: invalid opt, {1!r}'\
                  .format(self.fullname(), self._opt)))
        # default
        if not isinstance(self._def, NoneType):
            if self._mode == MODE_SET:
                self._safechk_set(self._def)
            else:
                self._safechk_val(self._def)
        # uniq
        if not isinstance(self._uniq, bool):
            raise(ASN1ObjErr('{0}: invalid uniq, {1!r}'\
                  .format(self.fullname(), self._uniq)))
        # group
        if not isinstance(self._group, (NoneType, integer_types)):
            raise(ASN1ObjErr('{0}: invalid group, {1!r}'\
                  .format(self.fullname(), self._group)))
    
    def _safechk_val(self, val):
        """
        ensures the value val has the correct format according to self
        """
        # check val format, implemented for each specific object
        pass
    
    def _safechk_val_int(self, val):
        if not isinstance(val, integer_types):
            raise(ASN1ObjErr('{0}: invalid INTEGER value, {1!r}'\
                  .format(self.fullname(), val)))
    
    def _safechk_val_real(self, val):
        if not isinstance(val, tuple) or len(val) != 3 or \
        not isinstance(val[0], integer_types) or \
        val[1] not in (2, 10) or \
        not isinstance(val[2], integer_types):
            raise(ASN1ObjErr('{0}: invalid REAL value, {1!r}'\
                  .format(self.fullname(), val)))
    
    def _safechk_val_str(self, val):
        if not isinstance(val, str_types):
            raise(ASN1ObjErr('{0}: invalid _String value, {1!r}'\
                  .format(self.fullname(), val)))
    
    def _safechk_set(self, s):
        """
        ensures the set of values s has the correct format according to self
        """
        if not isinstance(s, ASN1Set):
            raise(ASN1ObjErr('{0}: invalid set, {1!r}'.format(self.fullname(), s)))
        for v in s._rv:
            self._safechk_val(v)
        if s._ev is not None:
            for v in s._ev:
                self._safechk_val(v)
    
    def _safechk_set_int(self, si):
        if not isinstance(s, ASN1Set):
            raise(ASN1ObjErr('{0}: invalid set, {1!r}'.format(self.fullname(), s)))
        for v in s._rv:
            self._safechk_val(v)
        for vr in s._rr:
            if not isinstance(vr, ASN1RangeInt):
                raise(ASN1ObjErr('{0}: invalid INTEGER range, {1!r}'\
                      .format(self.fullname(), vr)))
        if s._ev is not None:
            for v in s._ev:
                self._safechk_val(v)
            for vr in s._er:
                if not isinstance(vr, ASN1RangeInt):
                    raise(ASN1ObjErr('{0}: invalid INTEGER range, {1!r}'\
                          .format(self.fullname(), vr)))
    
    def _safechk_set_real(self, sr):
        if not isinstance(s, ASN1Set):
            raise(ASN1ObjErr('{0}: invalid set, {1!r}'.format(self.fullname(), s)))
        for v in s._rv:
            self._safechk_val(v)
        for vr in s._rr:
            if not isinstance(vr, ASN1RangeReal):
                raise(ASN1ObjErr('{0}: invalid REAL range, {1!r}'\
                      .format(self.fullname(), vr)))
        if s._ev is not None:
            for v in s._evt:
                self._safechk_val(v)
            for vr in s._er:
                if not isinstance(vr, ASN1RangeReal):
                    raise(ASN1ObjErr('{0}: invalid REAL range, {1!r}'\
                          .format(self.fullname(), vr)))
    
    def _safechk_set_str(self, ss):
        if not isinstance(s, ASN1Set):
            raise(ASN1ObjErr('{0}: invalid set, {1!r}'.format(self.fullname(), s)))
        for v in s._rv:
            self._safechk_val(v)
        for vr in s._rr:
            if not isinstance(vr, ASN1RangeStr):
                raise(ASN1ObjErr('{0}: invalid _String range, {1!r}'\
                      .format(self.fullname(), vr)))
        if s._ev is not None:
            for v in s._ev:
                self._safechk_val(v)
            for vr in s._er:
                if not isinstance(vr, ASN1RangeStr):
                    raise(ASN1ObjErr('{0}: invalid _String range, {1!r}'\
                          .format(self.fullname(), vr)))
    
    def _safechk_bnd(self, val):
        """
        ensures the value val is within potential constraints defined for self
        """
        # check val against potential constraints
        if self._const_val and \
        self._const_val.ext is None and \
        val not in self._const_val:
            raise(ASN1ObjErr('{0}: value out of constraint, {1!r}'\
                  .format(self.fullname(), val)))
        if self._SAFE_BNDTAB and self._const_tab and self._const_tab_at:
            # check val against a constraint defined within the table constraint
            try:
                const_val = self._get_tab_obj()
            except Exception as err:
                if not self._SILENT:
                    asnlog('%s._from_per_ws: %s, unable to retrieve a defined object, %s'\
                           % (self.__class__.__name__, self._name, err))
            else:
                if self._mode == MODE_VALUE and val != const_val or \
                self._mode == MODE_SET and val not in const_val:
                    raise(ASN1ObjErr('{0}: value out of table constraint, {1!r}'\
                          .format(self.fullname(), val)))
    
    def _get_tab_obj(self):
        try:
            IndIdent = self.get_obj_by_path(self._const_tab_at)._const_tab_id
            IndVal = self.get_val_by_path(self._const_tab_at)
        except:
            raise(ASN1ObjErr('{0}: invalid table constraint @ path, {1!r}'\
                  .format(self.fullname(), self._const_tab_at)))
        try:
            claval = self._const_tab(IndIdent, IndVal)
        except:
            raise(ASN1ObjErr('{0}: unable to select table constraint {1} with value {2!r}'\
                  .format(self.fullname(), IndIdent, IndVal)))
        else:
            try:
                return claval[self._const_tab_id]
            except:
                raise(ASN1ObjErr('{0}: unable to select ident {1} within table value'\
                      .format(self.fullname(), self._const_tab_id)))
    
    
    #--------------------------------------------------------------------------#
    # user-friendly generic representation
    #--------------------------------------------------------------------------#
    
    def fullname(self):
        name = [self._name]
        obj = self
        while obj._parent is not None:
            obj = obj._parent
            name.append(obj._name)
        return '.'.join(reversed(name))
    
    def __repr__(self):
        if self._typeref is not None:
            if isinstance(self._typeref, (ASN1RefType, ASN1RefInstOf)):
                try:
                    typeref = self._typeref.called[1]
                except AttributeError:
                    # .called is ASN1RefParam
                    typeref = repr(self._typeref.called)
            elif isinstance(self._typeref, ASN1RefChoiceComp):
                try:
                    typeref = '%s<' % self._typeref.called[1] + \
                              '<'.join(self._typeref.ced_path)
                except AttributeError:
                    # .called is ASN1RefParam
                    typeref = '%s<' % repr(self._typeref.called) + \
                              '<'.join(self._typeref.ced_path)
            elif isinstance(self._typeref, ASN1RefClassField):
                try:
                    typeref = '%s.&' % self._typeref.called[1] + \
                              '.&'.join(self._typeref.ced_path)
                except AttributeError:
                    # .called is ASN1RefParam
                    typeref = '%s.&' % repr(self._typeref.called) + \
                              '.&'.join(self._typeref.ced_path)
            elif isinstance(self._typeref, ASN1RefClassIntern):
                typeref = '&%s' % '.&'.join(self._typeref.ced_path)
            elif isinstance(self._typeref, ASN1RefClassValField):
                try:
                    typeref = '%s.&%s' % (self._typeref.called[1],
                                          '.&'.join(self._typeref.ced_path))
                except AttributeError:
                    # .called is ASN1RefParam
                    typeref = '%s.&%s' % (repr(self._typeref.called),
                                          '.&'.join(self._typeref.ced_path))
            else:
                assert()
        else:
            typeref = None
        #
        if self._mode == MODE_TYPE:
            if typeref is not None:
                return '<%s ([%s] %s)>' % (self._name,
                                           typeref,
                                           self.TYPE)
            else:
                return '<%s (%s)>' % (self._name,
                                      self.TYPE)
        elif self._mode == MODE_VALUE:
            if self._val is not None:
                val = self._val
            else:
                val = ' '
            if typeref is not None:
                return '<%s ([%s] %s): %s>' % (self._name,
                                               typeref,
                                               self.TYPE,
                                               val)
            else:
                return '<%s (%s): %s>' % (self._name,
                                          self.TYPE,
                                          val)
        elif self._mode == MODE_SET:
            if self._val is not None:
                val = repr(self._val)
            else:
                val = ' '
            if typeref is not None:
                return '<%s ([%s] %s): %s>' % (self._name,
                                               typeref,
                                               self.TYPE,
                                               val)
            else:
                return '<%s (%s): %s>' % (self._name,
                                          self.TYPE,
                                          val)
    
    # TODO: make repr() and show() similar to those from pycrate_core.elt.Envelope
    
    #--------------------------------------------------------------------------#
    # internal attributes access method
    #--------------------------------------------------------------------------#
    
    def get_internals(self):
        """
        returns all internal attributes within a dict
        """
        internals = {
            'name'   : self._name,
            'mode'   : self._mode,
            'tag'    : self._tag,
            'typeref': self._typeref,
            'tr'     : self._tr,
            'param'  : self._param,
            'parent' : self._parent,
            'opt'    : self._opt,
            'def'    : self._def,
            'uniq'   : self._uniq,
            'group'  : self._group,
            'cont'   : self._cont,
            'root'   : self._root,
            'ext'    : self._ext,
            'val'    : self._val,
            'const_val': self._const_val,
            'const_tab': self._const_tab
            }
        if hasattr(self, 'cont_tags'):
            internals['cont_tags']      = self._cont_tags
        if hasattr(self, '_root_mand'):
            internals['root_mand']      = self._root_mand
        if hasattr(self, '_root_ext'):
            internals['root_ext']       = self._root_ext
        if hasattr(self, '_ext_group'):
            internals['ext_group']      = self._ext_group
        if hasattr(self, '_ext_group_obj'):
            internals['ext_group_obj']  = self._ext_group_obj
        if hasattr(self, '_ext_ident'):
            internals['ext_ident']      = self._ext_ident
        if hasattr(self, '_const_sz'):
            internals['const_sz']       = self._const_sz
        if hasattr(self, '_const_alpha'):
            internals['const_alpha']    = self._const_alpha
        if hasattr(self, '_const_cont'):
            internals['const_cont']     = self._const_cont
        if hasattr(self, '_const_cont_enc'):
            internals['const_cont_enc'] = self._const_cont_enc
        if hasattr(self, '_const_tab_id'):
            internals['const_tab_id']   = self._const_tab_id
        if hasattr(self, '_const_tab_at'):
            internals['const_tab_at']   = self._const_tab_at
        return internals
    
    def get_proto(self):
        """
        returns the prototype of the object
        """
        if self.TYPE in TYPES_BASIC + TYPES_EXT:
            return self.TYPE
        elif self.TYPE in (TYPE_SEQ_OF, TYPE_SET_OF):
            return [self._cont.get_proto()]
        elif self.TYPE in (TYPE_CHOICE, TYPE_SEQ, TYPE_SET, TYPE_CLASS):
            return ASN1Dict([(ident, Comp.get_proto()) for (ident, Comp) in self._cont.items()])
        else:
            assert()
    
    def get_obj_by_path(self, path):
        """
        select an object by navigating in a relative way into a root object 
        according to the submitted path
        """
        obj = self
        for p in path:
            if p == '..':
                obj = obj._parent
            else:
                obj = obj._cont[p]
        return obj
    
    def get_val_by_path(self, path):
        """
        select a value be navigating in a relative way into a root object value
        according to the submitted path
        """
        obj = self
        for p in path:
            if p == '..':
                obj = obj._parent
            else:
                obj = obj._cont[p]
        return obj._val
    
    def get_root(self):
        """
        returns the root object containing self in case self is within a 
        constructed or CLASS object
        """
        par = self._parent
        while par is not None:
            par = self._parent
        return par
    
    def get_root_chain(self):
        """
        returns the list of successive objects containing self up to the root one
        in case self is within a constructed or CLASS object
        """
        chain = [self._parent]
        while chain[-1] is not None:
            chain.append( chain[-1]._parent )
        return chain
    
    def in_class(self):
        """
        returns True in case self is a field of a CLASS, False otherwise
        """
        par = self._parent
        while par is not None:
            if par.TYPE == TYPE_CLASS:
                return True
            else:
                par = par._parent
        return False
    
    #--------------------------------------------------------------------------#
    # internal value access methods
    #--------------------------------------------------------------------------#
    
    def __call__(self):
        return self._val
    
    def get_val(self):
        return self._val
    
    def set_val(self, val):
        self._val = val
        if self._SAFE_VAL:
            self._safechk_val(self._val)
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def set_val_unsafe(self, val):
        self._val = val
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    #--------------------------------------------------------------------------#
    # encoding / decoding methods
    #--------------------------------------------------------------------------#
    
    ###
    # conversion between internal value and ASN.1 syntax
    ###
    
    def _from_asn1(self, txt):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def _to_asn1(self):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def from_asn1(self, txt):
        ret = self._from_asn1(txt)
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
        return ret
    
    def to_asn1(self, val=None):
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            return self._to_asn1()
        else:
            return None
    
    def show(self):
        return '<~ASN1~: %s>' % self.to_asn1()
    
    ###
    # conversion between internal value and ASN.1 PER encoding
    ###
    
    def _from_per(self, char):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def _to_per(self):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def from_uper(self, buf):
        ASN1CodecPER.ALIGNED = False
        if isinstance(buf, bytes_types):
            char = Charpy(buf)
        else:
            char = buf
            #assert( char.len_bit() % 8 == 0 )
        off0 = char._cur
        self._from_per(char)
        off1 = char._cur
        if off1 == off0:
            # char was not consumed at all (all decoded values were implicit)
            # hence a null byte must be consumed for outer decoding
            null = char.get_bytes(8)
            assert( null == b'\0' )
        elif (off1 - off0) % 8:
            # realignement required for outer decoding
            char.forward(8 - ((off1 - off0)%8))
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def to_uper(self, val=None):
        ASN1CodecPER.ALIGNED = False
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            ret = pack_val(*self._to_per())[0]
            if ret:
                return ret
            else:
                return b'\0'
        else:
            return None
    
    def from_aper(self, buf):
        ASN1CodecPER.ALIGNED = True
        ASN1CodecPER._off.append(0)
        if isinstance(buf, bytes_types):
            char = Charpy(buf)
        else:
            char = buf
            assert( char.len_bit() % 8 == 0 )
        self._from_per(char)
        if ASN1CodecPER._off[-1] == 0:
            # char was not consumed at all (all decoded values were implicit)
            # hence a null byte must be consumed
            null = char.get_bytes(8)
            assert( null == b'\0' )
        elif ASN1CodecPER._off[-1] % 8:
            # realignement required for outer decoding
            char.forward(8 - (ASN1CodecPER._off[-1]%8))
        del ASN1CodecPER._off[-1]
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def to_aper(self, val=None):
        ASN1CodecPER.ALIGNED = True
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            ASN1CodecPER._off.append(0)
            ret = pack_val(*self._to_per())[0]
            if not ret:
                ret = b'\0'
            del ASN1CodecPER._off[-1]
            return ret
        else:
            return None
     
    # methods generating complete transfer structure in _struct attributes
    
    def _from_per_ws(self, char):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def _to_per_ws(self):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def from_uper_ws(self, buf):
        ASN1CodecPER.ALIGNED = False
        if isinstance(buf, bytes_types):
            char = Charpy(buf)
        else:
            char = buf
            #assert( char.len_bit() % 8 == 0 )
        off0 = char._cur
        self._from_per_ws(char)
        off1 = char._cur
        pad = None
        if off1 == off0:
            # char was not consumed at all (all decoded values were implicit)
            # hence a null byte must be consumed
            pad = Uint('P', val=0, bl=8, rep=REPR_BIN)
            pad._from_char(char)
            self._struct.append(pad)
            assert( pad() == 0 )
        elif (off1 - off0) % 8:
            # realignment required for outer decoding
            pad = Uint('P', val=0, bl=(8-((off1 - off0)%8)), rep=REPR_BIN)
            pad._from_char(char)
            self._struct.append(pad)
            assert( pad() == 0 )
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def to_uper_ws(self, val=None):
        ASN1CodecPER.ALIGNED = False
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            _struct = self._to_per_ws()
            bl = _struct.get_bl()
            if bl == 0:
                _struct.append( Uint('P', val=0, bl=8, rep=REPR_BIN) )
            elif bl % 8:
                _struct.append( Uint('P', val=0, bl=(8-(bl%8)), rep=REPR_BIN) )
            return _struct.to_bytes()
        else:
            return None
    
    def from_aper_ws(self, buf):
        ASN1CodecPER.ALIGNED = True
        ASN1CodecPER._off.append(0)
        if isinstance(buf, bytes_types):
            char = Charpy(buf)
        else:
            char = buf
            assert( char.len_bit() % 8 == 0 )
        self._from_per_ws(char)
        if ASN1CodecPER._off[-1] == 0:
            # char was not consumed at all (all decoded values were implicit)
            # hence a null byte must be consumed
            pad = Uint('P', val=0, bl=8, rep=REPR_BIN)
            pad._from_char(char)
            self._struct.append(pad)
            assert( pad() == 0 )
        elif ASN1CodecPER._off[-1] % 8:
            # realignement required for outer decoding
            pad = Uint('P', val=0, bl=(8 - (ASN1CodecPER._off[-1]%8)), rep=REPR_BIN)
            pad._from_char(char)
            self._struct.append(pad)
            assert( pad() == 0 )
        del ASN1CodecPER._off[-1]
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def to_aper_ws(self, val=None):
        ASN1CodecPER.ALIGNED = True
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            ASN1CodecPER._off.append(0)
            _struct = self._to_per_ws()
            if ASN1CodecPER._off[-1] == 0:
                _struct.append( Uint('P', val=0, bl=8, rep=REPR_BIN) )
            elif ASN1CodecPER._off[-1] % 8:
                _struct.append( Uint('P', val=0, bl=(8-(ASN1CodecPER._off[-1]%8)), rep=REPR_BIN) )
            del ASN1CodecPER._off[-1]
            return _struct.to_bytes()
        else:
            return None
    
    ###
    # conversion between internal value and ASN.1 BER encoding
    ###
    
    def _from_ber(self, char, TLV):
        # 1) decode the tag chain
        tlv, pc = TLV, 1
        for t in self._tagc:
            tlv = tlv[0]
            cl, pc, tval, lval = tlv[0:4]
            if (cl, tval) != t or (t != self._tagc[-1] and pc == 0):
                raise(ASN1BERDecodeErr('{0}: invalid tag class / pc / value, {1!r}'\
                      .format(self.fullname(), (cl, pc, tval))))
            tlv = tlv[4]
        if pc == 0:
            # 2a) decode primitive content value
            assert( isinstance(tlv, tuple) )
            self._decode_ber_cont(char, tlv)
        else:
            # 2b) continue decoding constructed content
            assert( isinstance(tlv, list) )
            self._decode_ber_cont(char, tlv)
    
    def from_ber(self, buf):
        if isinstance(buf, bytes_types):
            char = Charpy(buf)
        else:
            char = buf
        # decode the whole char buffer into tag, length and value boundary
        TLV = ASN1CodecBER.decode_all(char)
        char_cur, char_lb = char._cur, char._len_bit
        # decode all value content
        self._from_ber(char, TLV)
        char._cur, char._len_bit = char_cur, char_lb
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def _to_ber(self):
        # 1) encode the most inner TLV part
        pc, lval, V = self._encode_ber_cont()
        if not self._tagc:
            # in case no tag is associated to the object (CHOICE, OPEN / ANY)
            # we only have the inner encoding
            return V
        TLV = ASN1CodecBER.encode_tag(self._tagc[-1][0], pc, self._tagc[-1][1])
        TLV.extend( ASN1CodecBER.encode_len(lval) )
        TLV.extend( V )
        if lval == -1:
            TLV.append( (T_BYTES, b'\0\0', 16) )
        # 2) encode the outer part of the object, i.e. the rest of the tag chain
        if len(self._tagc) > 1:
            GEN = [TLV]
            if ASN1CodecBER.ENC_LUNDEF:
                for t in reversed(self._tagc[:-1]):
                    TL = ASN1CodecBER.encode_tag(t[0], 1, t[1])
                    TL.extend( ASN1CodecBER.encode_len(-1) )
                    # append an EOC marker after the value
                    TLV.append( (T_BYTES, b'\0\0', 16) )
                    GEN.append(TL)
            else:
                lval = sum([f[2] for f in TLV]) >> 3
                for t in reversed(self._tagc[:-1]):
                    TL = ASN1CodecBER.encode_tag(t[0], 1, t[1])
                    TL.extend( ASN1CodecBER.encode_len(lval) )
                    lval += sum([f[2] for f in TL]) >> 3
                    GEN.append(TL)
            # revert and flatten GEN
            return [i for j in reversed(GEN) for i in j]
        else:
            return TLV
    
    def to_ber(self, val=None):
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            return pack_val(*self._to_ber())[0]
        else:
            return None
    
    # methods generating complete transfer structure in _struct attributes
    
    def _from_ber_ws(self, char, TLV):
        # 1) decode the tag chain
        tlv, TL, pc = TLV, [], 1
        for t in self._tagc:
            tlv = tlv[0]
            Tag, cl, pc, tval, Len, lval = tlv[0:6]
            if (cl, tval) != t or (t != self._tagc[-1] and pc == 0):
                raise(ASN1BERDecodeErr('{0}: invalid tag class / pc / value, {1!r}'\
                      .format(self.fullname(), (cl, pc, tval))))
            # select the value as a new inner tlv
            tlv = tlv[6]
            if lval == -1:
                # keep track of the End-Of-Content marker
                TL.append( (Tag, Len, tlv[-1][0], tlv[-1][4]) )
            else:
                TL.append( (Tag, Len) )
        #
        if pc == 0:
            # 2a) decode primitive content value
            assert( isinstance(tlv, tuple) )
            V = self._decode_ber_cont_ws(char, tlv)
        else:
            # 2b) continue decoding constructed content
            assert( isinstance(tlv, list) )
            V = self._decode_ber_cont_ws(char, tlv)
        #
        # 3) generate the complete TLV structure
        if TL:
            TL.reverse()
            for tl in TL:
                if len(tl) == 4:
                    # EOC marker
                    TLV = Envelope('TLV', GEN=(tl[0], tl[1], V, tl[2], tl[3]))
                else:
                    TLV = Envelope('TLV', GEN=(tl[0], tl[1], V))
                V = TLV
                V._name = 'V'
        else:
            # in case no tag is associated to the object (CHOICE, OPEN / ANY)
            # we only have the inner encoding
            TLV = V
        # set object name and final struct
        TLV._name = self._name
        self._struct = TLV
    
    def from_ber_ws(self, buf):
        if isinstance(buf, bytes_types):
            char = Charpy(buf)
        else:
            char = buf
        # decode the whole char buffer into tag, length and value boundary
        TLV = ASN1CodecBER.decode_all_ws(char)
        # decode all value content
        self._from_ber_ws(char, TLV)
        if self._SAFE_BND:
            self._safechk_bnd(self._val)
    
    def _to_ber_ws(self):
        # 1) encode the most inner TLV part
        pc, lval, V = self._encode_ber_cont_ws()
        if not self._tagc:
            # in case no tag is associated to the object (CHOICE, OPEN / ANY)
            # we only have the inner encoding
            TLV = V
        else:
            if pc == 1 and ASN1CodecBER.ENC_LUNDEF:
                TLV = Envelope('TLV', GEN=(
                        ASN1CodecBER.encode_tag_ws(self._tagc[-1][0], pc, self._tagc[-1][1]),
                        ASN1CodecBER.encode_len_ws(-1),
                        V,
                        ASN1CodecBER.encode_tag_ws(0, 0, 0),
                        ASN1CodecBER.encode_len_ws(0)))
            else:
                TLV = Envelope('TLV', GEN=(
                        ASN1CodecBER.encode_tag_ws(self._tagc[-1][0], pc, self._tagc[-1][1]),
                        ASN1CodecBER.encode_len_ws(lval),
                        V))
            # 2) encode the outer part of the object, i.e. the rest of the tag chain
            if len(self._tagc) > 1:
                if ASN1CodecBER.ENC_LUNDEF:
                    for t in reversed(self._tagc[:-1]):
                        TLV._name = 'V'
                        TLV = Envelope('TLV', GEN=(ASN1CodecBER.encode_tag_ws(t[0], 1, t[1]),
                                                      ASN1CodecBER.encode_len_ws(-1),
                                                      TLV,
                                                      ASN1CodecBER.encode_tag_ws(0, 0, 0),
                                                      ASN1CodecBER.encode_len_ws(0)))
                else:
                    lval += (TLV[0].get_bl() + TLV[1].get_bl()) >> 3
                    for t in reversed(self._tagc[:-1]):
                        TLV._name = 'V'
                        TLV = Envelope('TLV', GEN=(ASN1CodecBER.encode_tag_ws(t[0], 1, t[1]),
                                                      ASN1CodecBER.encode_len_ws(lval),
                                                      TLV))
                        lval += (TLV[0].get_bl() + TLV[1].get_bl()) >> 3
        # set object name and final struct
        TLV._name = self._name
        self._struct = TLV
        return TLV
    
    def to_ber_ws(self, val=None):
        if val is not None:
            self.set_val(val)
        if self._val is not None:
            return self._to_ber_ws().to_bytes()
        else:
            return None
    
    ###
    # conversion between internal value and ASN.1 CER encoding
    # reusing the BER encoder
    ###
    
    def from_cer(self, buf):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = True
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 1000
        ASN1CodecBER.ENC_OSTR_FRAG  = 1000
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.from_ber(buf)
        _restore_ber_params()
        return ret
    
    def to_cer(self, val=None):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = True
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 1000
        ASN1CodecBER.ENC_OSTR_FRAG  = 1000
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.to_ber(val)
        _restore_ber_params()
        return ret
    
    # methods generating complete transfer structure in _struct attributes
    
    def from_cer_ws(self, buf):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = True
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 1000
        ASN1CodecBER.ENC_OSTR_FRAG  = 1000
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.from_ber_ws(buf)
        _restore_ber_params()
        return ret
    
    def to_cer_ws(self, val=None):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = True
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 1000
        ASN1CodecBER.ENC_OSTR_FRAG  = 1000
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.to_ber_ws(val)
        _restore_ber_params()
        return ret
    
    ###
    # conversion between internal value and ASN.1 DER encoding
    # reusing the BER encoder
    ###
    
    def from_der(self, buf):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = False
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 0
        ASN1CodecBER.ENC_OSTR_FRAG  = 0
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.from_ber(buf)
        _restore_ber_params()
        return ret
    
    def to_der(self, val=None):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = False
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 0
        ASN1CodecBER.ENC_OSTR_FRAG  = 0
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.to_ber(val)
        _restore_ber_params()
        return ret
    
    # methods generating complete transfer structure in _struct attributes
    
    def from_der_ws(self, buf):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = False
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 0
        ASN1CodecBER.ENC_OSTR_FRAG  = 0
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.from_ber_ws(buf)
        _restore_ber_params()
        return ret
    
    def to_der_ws(self, val=None):
        _save_ber_params()
        ASN1CodecBER.ENC_LLONG      = 0
        ASN1CodecBER.ENC_LUNDEF     = False
        ASN1CodecBER.ENC_BOOLTRUE   = 0xff
        ASN1CodecBER.ENC_REALNR     = 3
        ASN1CodecBER.ENC_BSTR_FRAG  = 0
        ASN1CodecBER.ENC_OSTR_FRAG  = 0
        ASN1CodecBER.ENC_TIME_CANON = True
        ASN1CodecBER.ENC_DEF_CANON  = True
        ret = self.to_ber_ws(val)
        _restore_ber_params()
        return ret
    
    ###
    # convert internal value to ASN.1 GSER encoding
    ###
    # TODO
    
    def from_gser(self, char):
        raise(ASN1NotSuppErr(self.fullname()))
    
    def to_gser(self, buf, val=None):
        raise(ASN1NotSuppErr(self.fullname()))



def _save_ber_params():
    global __ber_enc_llong
    global __ber_enc_lundef
    global __ber_enc_booltrue
    global __ber_enc_realnr
    global __ber_enc_bstr_frag
    global __ber_enc_ostr_frag
    global __ber_enc_time_canon
    global __ber_enc_def_canon
    __ber_enc_llong      = ASN1CodecBER.ENC_LLONG
    __ber_enc_lundef     = ASN1CodecBER.ENC_LUNDEF
    __ber_enc_booltrue   = ASN1CodecBER.ENC_BOOLTRUE
    __ber_enc_realnr     = ASN1CodecBER.ENC_REALNR
    __ber_enc_bstr_frag  = ASN1CodecBER.ENC_BSTR_FRAG
    __ber_enc_ostr_frag  = ASN1CodecBER.ENC_OSTR_FRAG
    __ber_enc_time_canon = ASN1CodecBER.ENC_TIME_CANON
    __ber_enc_def_canon  = ASN1CodecBER.ENC_DEF_CANON

def _restore_ber_params():
    global __ber_enc_llong
    global __ber_enc_lundef
    global __ber_enc_booltrue
    global __ber_enc_realnr
    global __ber_enc_bstr_frag
    global __ber_enc_ostr_frag
    global __ber_enc_time_canon
    global __ber_enc_def_canon
    ASN1CodecBER.ENC_LLONG      = __ber_enc_llong
    ASN1CodecBER.ENC_LUNDEF     = __ber_enc_lundef
    ASN1CodecBER.ENC_BOOLTRUE   = __ber_enc_booltrue
    ASN1CodecBER.ENC_REALNR     = __ber_enc_realnr
    ASN1CodecBER.ENC_BSTR_FRAG  = __ber_enc_bstr_frag
    ASN1CodecBER.ENC_OSTR_FRAG  = __ber_enc_ostr_frag
    ASN1CodecBER.ENC_TIME_CANON = __ber_enc_time_canon
    ASN1CodecBER.ENC_DEF_CANON  = __ber_enc_def_canon

