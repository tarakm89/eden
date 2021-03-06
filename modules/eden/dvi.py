# -*- coding: utf-8 -*-

""" Sahana Eden DVI Model

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3DVIModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3DVIModel(S3Model):

    names = ["dvi_recreq",
             "dvi_body",
             "dvi_morgue",
             "dvi_checklist",
             "dvi_effects",
             "dvi_identification"]

    def model(self):

        db = current.db
        T = current.T
        request = current.request
        s3 = current.response.s3

        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        pe_label = self.pr_pe_label
        person_id = self.pr_person_id
        pr_gender = self.pr_gender
        pr_age_group = self.pr_age_group

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        datetime_represent = S3DateTime.datetime_represent

        # ---------------------------------------------------------------------
        # Recovery Request
        #
        task_status = {
            1:T("Not Started"),
            2:T("Assigned"),
            3:T("In Progress"),
            4:T("Completed"),
            5:T("Not Applicable"),
            6:T("Not Possible")
        }

        tablename = "dvi_recreq"
        table = self.define_table(tablename,
                                  Field("date", "datetime",
                                        label = T("Date/Time of Find"),
                                        default = request.utcnow,
                                        requires = IS_UTC_DATETIME(allow_future=False),
                                        represent = lambda val: datetime_represent(val, utc=True),
                                        widget = S3DateTimeWidget(future=0)),
                                  Field("marker", length=64,
                                        label = T("Marker"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Marker"),
                                                                        T("Number or code used to mark the place of find, e.g. flag code, grid coordinates, site reference number or similar (if available)")))),
                                  person_id(label = T("Finder")),
                                  Field("bodies_found", "integer",
                                        label = T("Bodies found"),
                                        requires = IS_INT_IN_RANGE(1, 99999),
                                        represent = lambda v, row=None: IS_INT_AMOUNT.represent(v),
                                        default = 0,
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Number of bodies found"),
                                                                        T("Please give an estimated figure about how many bodies have been found.")))),
                                  Field("bodies_recovered", "integer",
                                        label = T("Bodies recovered"),
                                        requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999)),
                                        represent = lambda v, row=None: IS_INT_AMOUNT.represent(v),
                                        default = 0),
                                  Field("description", "text"),
                                  location_id(label=T("Location")),
                                  Field("status", "integer",
                                        requires = IS_IN_SET(task_status,
                                                             zero=None),
                                        default = 1,
                                        label = T("Task Status"),
                                        represent = lambda opt: \
                                                    task_status.get(opt, UNKNOWN_OPT)),
                                  *s3.meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Body Recovery Request"),
            title_display = T("Request Details"),
            title_list = T("Body Recovery Requests"),
            title_update = T("Update Request"),
            title_search = T("Search Request"),
            subtitle_create = T("Add New Request"),
            subtitle_list = T("List of Requests"),
            label_list_button = T("List of Requests"),
            label_create_button = T("Add Request"),
            label_delete_button = T("Delete Request"),
            msg_record_created = T("Recovery Request added"),
            msg_record_modified = T("Recovery Request updated"),
            msg_record_deleted = T("Recovery Request deleted"),
            msg_list_empty = T("No requests found"))

        # Resource configuration
        self.configure(tablename,
                       list_fields = ["id",
                                      "date",
                                      "marker",
                                      "location_id",
                                      "bodies_found",
                                      "bodies_recovered",
                                      "status"
                                     ])

        # Reusable fields
        dvi_recreq_id = S3ReusableField("dvi_recreq_id", table,
                                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                        "dvi_recreq.id",
                                                        "[%(marker)s] %(date)s: %(bodies_found)s bodies")),
                                        represent = lambda id: id,
                                        label=T("Recovery Request"),
                                        ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Morgue
        #
        tablename = "dvi_morgue"
        table = db.define_table(tablename,
                                self.super_link("pe_id", "pr_pentity"),
                                self.super_link("site_id", "org_site"),
                                Field("name",
                                      unique=True,
                                      notnull=True),
                                organisation_id(),
                                Field("description"),
                                location_id(),
                                *s3.meta_fields())

        # Reusable Field
        morgue_id = S3ReusableField("morgue_id", table,
                                    requires = IS_NULL_OR(IS_ONE_OF(db,
                                                    "dvi_morgue.id", "%(name)s")),
                                    represent = self.morgue_represent,
                                    ondelete = "RESTRICT")

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Morgue"),
            title_display = T("Morgue Details"),
            title_list = T("Morgues"),
            title_update = T("Update Morgue Details"),
            title_search = T("Search Morgues"),
            subtitle_create = T("Add New Morgue"),
            subtitle_list = T("List of Morgues"),
            label_list_button = T("List of Morgues"),
            label_create_button = T("Add Morgue"),
            label_delete_button = T("Delete Morgue"),
            msg_record_created = T("Morgue added"),
            msg_record_modified = T("Morgue updated"),
            msg_record_deleted = T("Morgue deleted"),
            msg_list_empty = T("No morgues found"))

        # Search Method?

        # Resource Configuration?
        self.configure(tablename,
                       super_entity=("pr_pentity", "org_site"))

        # Components
        self.add_component("dvi_body", dvi_morgue="morgue_id")

        # ---------------------------------------------------------------------
        # Body
        #
        bool_repr = lambda opt: (opt and [T("yes")] or [""])[0]
        tablename = "dvi_body"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  self.super_link("track_id", "sit_trackable"),
                                  pe_label(requires = [IS_NOT_EMPTY(error_message=T("Enter a unique label!")),
                                                       IS_NOT_ONE_OF(db, "dvi_body.pe_label")]),
                                  morgue_id(),
                                  dvi_recreq_id(label = T("Recovery Request")),
                                  Field("date_of_recovery", "datetime",
                                        default = request.utcnow,
                                        requires = IS_UTC_DATETIME(allow_future=False),
                                        represent = lambda val: datetime_represent(val, utc=True)),
                                  Field("recovery_details","text"),
                                  Field("incomplete", "boolean",
                                        label = T("Incomplete"),
                                        represent = bool_repr),
                                  Field("major_outward_damage", "boolean",
                                        label = T("Major outward damage"),
                                        represent = bool_repr),
                                  Field("burned_or_charred", "boolean",
                                        label = T("Burned/charred"),
                                        represent = bool_repr),
                                  Field("decomposed","boolean",
                                        label = T("Decomposed"),
                                        represent = bool_repr),
                                  pr_gender(label=T("Apparent Gender")),
                                  pr_age_group(label=T("Apparent Age")),
                                  location_id(label=T("Place of Recovery")),
                                  *s3.meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Dead Body Report"),
            title_display = T("Dead Body Details"),
            title_list = T("Dead Body Reports"),
            title_update = T("Edit Dead Body Details"),
            title_search = T("Find Dead Body Report"),
            subtitle_create = T("Add New Report"),
            subtitle_list = T("List of Reports"),
            label_list_button = T("List Reports"),
            label_create_button = T("Add Report"),
            label_delete_button = T("Delete Report"),
            msg_record_created = T("Dead body report added"),
            msg_record_modified = T("Dead body report updated"),
            msg_record_deleted = T("Dead body report deleted"),
            msg_list_empty = T("No dead body reports available"))

        # Search method
        body_search = S3Search(name = "body_search_simple",
                               field = ["pe_label"],
                               label = T("ID Tag"),
                               comment = T("To search for a body, enter the ID tag number of the body. You may use % as wildcard. Press 'Search' without input to list all bodies."))

        # Resource configuration
        self.configure(tablename,
                       super_entity=("pr_pentity", "sit_trackable"),
                       create_onaccept=self.body_onaccept,
                       create_next=URL(f="body", args=["[id]", "checklist"]),
                       search_method=body_search,
                       list_fields=["id",
                                    "pe_label",
                                    "gender",
                                    "age_group",
                                    "incomplete",
                                    "date_of_recovery",
                                    "location_id"
                                   ])

        # ---------------------------------------------------------------------
        # Checklist of operations
        #
        checklist_item = S3ReusableField("checklist_item", "integer",
                                         requires = IS_IN_SET(task_status, zero=None),
                                         default = 1,
                                         label = T("Checklist Item"),
                                         represent = lambda opt: \
                                                     task_status.get(opt, UNKNOWN_OPT))

        tablename = "dvi_checklist"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  checklist_item("personal_effects",
                                                 label = T("Inventory of Effects")),
                                  checklist_item("body_radiology",
                                                 label = T("Radiology")),
                                  checklist_item("fingerprints",
                                                 label = T("Fingerprinting")),
                                  checklist_item("anthropology",
                                                 label = T("Anthropolgy")),
                                  checklist_item("pathology",
                                                 label = T("Pathology")),
                                  checklist_item("embalming",
                                                 label = T("Embalming")),
                                  checklist_item("dna",
                                                 label = T("DNA Profiling")),
                                  checklist_item("dental",
                                                 label = T("Dental Examination")),
                                  *s3.meta_fields())

        # CRUD Strings
        CREATE_CHECKLIST = T("Create Checklist")
        s3.crud_strings[tablename] = Storage(
            title_create = CREATE_CHECKLIST,
            title_display = T("Checklist of Operations"),
            title_list = T("List Checklists"),
            title_update = T("Update Task Status"),
            title_search = T("Search Checklists"),
            subtitle_create = T("New Checklist"),
            subtitle_list = T("Checklist of Operations"),
            label_list_button = T("Show Checklist"),
            label_create_button = CREATE_CHECKLIST,
            msg_record_created = T("Checklist created"),
            msg_record_modified = T("Checklist updated"),
            msg_record_deleted = T("Checklist deleted"),
            msg_list_empty = T("No Checklist available"))

        # Resource configuration
        self.configure(tablename, list_fields=["id"])

        # ---------------------------------------------------------------------
        # Effects Inventory
        #
        tablename = "dvi_effects"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("clothing", "text"),  # @todo: elaborate
                                  Field("jewellery", "text"), # @todo: elaborate
                                  Field("footwear", "text"),  # @todo: elaborate
                                  Field("watch", "text"),     # @todo: elaborate
                                  Field("other", "text"),
                                  *s3.meta_fields())

        # CRUD Strings
        ADD_PERSONAL_EFFECTS = T("Add Personal Effects")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PERSONAL_EFFECTS,
            title_display = T("Personal Effects Details"),
            title_list = T("List Personal Effects"),
            title_update = T("Edit Personal Effects Details"),
            title_search = T("Search Personal Effects"),
            subtitle_create = T("Add New Entry"),
            subtitle_list = T("Personal Effects"),
            label_list_button = T("List Records"),
            label_create_button = ADD_PERSONAL_EFFECTS,
            msg_record_created = T("Record added"),
            msg_record_modified = T("Record updated"),
            msg_record_deleted = T("Record deleted"),
            msg_list_empty = T("No Details currently registered"))

        self.configure(tablename, list_fields=["id"])

        # ---------------------------------------------------------------------
        # Identification Report
        #
        dvi_id_status = {
            1:T("Unidentified"),
            2:T("Preliminary"),
            3:T("Confirmed"),
        }

        dvi_id_methods = {
            1:T("Visual Recognition"),
            2:T("Physical Description"),
            3:T("Fingerprints"),
            4:T("Dental Profile"),
            5:T("DNA Profile"),
            6:T("Combined Method"),
            9:T("Other Evidence")
        }

        tablename = "dvi_identification"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("status", "integer",
                                        requires = IS_IN_SET(dvi_id_status, zero=None),
                                        default = 1,
                                        label = T("Identification Status"),
                                        represent = lambda opt: \
                                                    dvi_id_status.get(opt, UNKNOWN_OPT)),
                                  person_id("identity",
                                            label=T("Identified as"),
                                            comment = self.person_id_comment("identity"),
                                            empty=False),
                                  person_id("identified_by",
                                            default=current.auth.s3_logged_in_person(),
                                            label=T("Identified by"),
                                            comment = self.person_id_comment("identified_by"),
                                            empty=False),
                                  Field("method", "integer",
                                        requires = IS_IN_SET(dvi_id_methods, zero=None),
                                        default = 1,
                                        label = T("Method used"),
                                        represent = lambda opt: \
                                                    dvi_id_methods.get(opt, UNKNOWN_OPT)),
                                  Field("comment", "text"),
                                  *s3.meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Identification Report"),
            title_display = T("Identification Report"),
            title_list = T("List Reports"),
            title_update = T("Edit Identification Report"),
            title_search = T("Search Report"),
            subtitle_create = T("Add New Report"),
            subtitle_list = T("Identification Reports"),
            label_list_button = T("List Reports"),
            label_create_button = T("Add Identification Report"),
            msg_record_created = T("Report added"),
            msg_record_modified = T("Report updated"),
            msg_record_deleted = T("Report deleted"),
            msg_list_empty = T("No Identification Report Available"))

        # Resource configuration
        self.configure(tablename,
                       mark_required = ["identity", "identified_by"],
                       list_fields = ["id"])


        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def body_onaccept(form):
        """ Update body presence log """

        db = current.db

        try:
            body = db.dvi_body[form.vars.id]
        except:
            return
        if body and body.location_id:
            tracker = S3Tracker()
            tracker(body).set_location(body.location_id,
                                       timestmp=body.date_of_recovery)

    # -------------------------------------------------------------------------
    @staticmethod
    def person_id_comment(fieldname):

        T = current.T

        c_title = T("Person.")
        c_comment = T("Type the first few characters of one of the Person's names.")

        ADD_PERSON = T("Add Person")
        return S3AddResourceLink(c="pr",
                                 f="person",
                                 vars=dict(child=fieldname),
                                 label=ADD_PERSON,
                                 title=c_title,
                                 tooltip=c_comment)

    # -------------------------------------------------------------------------
    @staticmethod
    def morgue_represent(id):

        db = current.db
        s3db = current.s3db

        table = s3db.dvi_morgue
        row = db(table.id == id).select(table.name,
                                        limitby=(0, 1)).first()
        if row:
            return row.name
        else:
            return "-"

# END =========================================================================
