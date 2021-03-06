from django.test import TestCase
import json
import pandas as pd
import io
from server.models import Module, ModuleVersion, WfModule, Workflow, ParameterSpec, ParameterVal
from server.tests.utils import *

# Set up a simple pipeline on test data
# Our WfModule unit tests derive from this, below, and WfModule view tests also use this
class WfModuleTestsBase(TestCase):

    def createTestWorkflow(self):
        # Create a standard test workflow, but it has only one module so add two more to test render pipeline
        # Throw a missing value in there to test handling of NA values
        test_csv = 'Class,M,F\n' \
                   'math,10,12\n' \
                   'english,,7\n' \
                   'history,11,13\n' \
                   'economics,20,20'

        self.test_table = pd.read_csv(io.StringIO(test_csv), header=0, skipinitialspace=True)

        self.workflow1 = create_testdata_workflow(csv_text=test_csv)
        self.pspec11 = ParameterSpec.objects.get(id_name='csv')

        self.module2_version = add_new_module_version('Module 2', dispatch='NOP')
        self.pspec21 = add_new_parameter_spec(self.module2_version, ParameterSpec.STRING, def_value='foo')
        self.pspec22 = add_new_parameter_spec(self.module2_version, ParameterSpec.FLOAT, def_value=3.14)
        self.pspec23 = add_new_parameter_spec(self.module2_version, ParameterSpec.INTEGER, def_value=42)
        self.pspec24 = add_new_parameter_spec(self.module2_version, ParameterSpec.CHECKBOX, def_value=True)
        self.pspec25 = ParameterSpec.objects.create(module_version=self.module2_version,
                                                    type=ParameterSpec.MENU,
                                                    def_menu_items='Apple|Banana|Kittens',
                                                    def_value='1')

        self.module3_version = add_new_module_version('Module 3', dispatch='double_M_col')
        self.pspec31 = add_new_parameter_spec(self.module3_version, ParameterSpec.BUTTON)

        self.wfmodule1 = WfModule.objects.get(order=0)
        self.wfmodule2 = add_new_wf_module(self.workflow1, self.module2_version, 1)
        self.wfmodule3 = add_new_wf_module(self.workflow1, self.module3_version, 2)


class WfModuleTests(WfModuleTestsBase):

    def setUp(self):
        self.createTestWorkflow()

    # check that creating a wf_module correctly sets up new ParameterVals w/ defaults from ParameterSpec
    def test_default_parameters(self):

        # Module 2 parameters should have correct default values
        self.wfmodule2.create_default_parameters()

        pval = ParameterVal.objects.get(parameter_spec=self.pspec21, wf_module=self.wfmodule2)
        self.assertEqual(pval.get_value(), 'foo')

        pval = ParameterVal.objects.get(parameter_spec=self.pspec22, wf_module=self.wfmodule2)
        self.assertEqual(pval.get_value(), 3.14)

        pval = ParameterVal.objects.get(parameter_spec=self.pspec23, wf_module=self.wfmodule2)
        self.assertEqual(pval.get_value(), 42)

        pval = ParameterVal.objects.get(parameter_spec=self.pspec24, wf_module=self.wfmodule2)
        self.assertEqual(pval.get_value(), True)

        pval = ParameterVal.objects.get(parameter_spec=self.pspec25, wf_module=self.wfmodule2)
        self.assertEqual(pval.selected_menu_item_string(), 'Banana')

        # button has no value, so just checking existence here
        self.wfmodule3.create_default_parameters()
        pval = ParameterVal.objects.get(parameter_spec=self.pspec31, wf_module=self.wfmodule3)
        self.assertEqual(pval.visible, True)


    # test stored versions of data: create, retrieve, set, list, and views
    def test_wf_module_data_versions(self):
        text1 = 'just pretend this is json'
        text2 = 'and this is a later version'

        # nothing ever stored
        nothing = self.wfmodule1.retrieve_data()
        self.assertIsNone(nothing)

        # save and recover data
        ver1 = self.wfmodule1.store_data(text1)
        self.wfmodule1.set_stored_data_version(ver1)
        self.wfmodule1.save()
        self.wfmodule1.refresh_from_db()
        textout = self.wfmodule1.retrieve_data()
        self.assertEqual(textout, text1)
        firstver = self.wfmodule1.get_stored_data_version()

        # create another version
        secondver = self.wfmodule1.store_data(text2)
        self.wfmodule1.set_stored_data_version(secondver)
        self.assertNotEqual(firstver, secondver)
        textout = self.wfmodule1.retrieve_data()
        self.assertEqual(textout, text2)

        # change the version back
        self.wfmodule1.set_stored_data_version(firstver)
        textout = self.wfmodule1.retrieve_data()
        self.assertEqual(textout, text1)

        # invalid version string should error
        with self.assertRaises(ValueError):
            self.wfmodule1.set_stored_data_version('foo')

        # list versions
        verlist = self.wfmodule1.list_stored_data_versions()
        self.assertListEqual(verlist, [firstver, secondver])  # sorted by creation date, ascending

        # but like, none of this should have created versions on any other wfmodule
        self.assertEqual(self.wfmodule2.list_stored_data_versions(), [])


    def test_wf_module_duplicate(self):
        wfm1 = self.wfmodule1

        # store data to test that it is duplicated
        s1 = wfm1.store_data("some data")
        s2 = wfm1.store_data("some more data")
        wfm1.set_stored_data_version(s2)
        self.assertEqual(len(wfm1.list_stored_data_versions()), 2)

        # duplicate into another workflow, as we would do when duplicating a workflow
        workflow2 = add_new_workflow("Test Workflow 2")
        wfm1d = wfm1.duplicate(workflow2)

        self.assertEqual(wfm1d.workflow, workflow2)
        self.assertEqual(wfm1d.module_version, wfm1.module_version)
        self.assertEqual(wfm1d.order, wfm1.order)
        self.assertEqual(wfm1d.notes, wfm1.notes)
        self.assertEqual(wfm1d.auto_update_data, wfm1.auto_update_data)
        self.assertEqual(wfm1d.last_update_check, wfm1.last_update_check)
        self.assertEqual(wfm1d.update_interval, wfm1.update_interval)
        self.assertEqual(wfm1d.is_collapsed, wfm1.is_collapsed)

        # parameters should be duplicated
        self.assertEqual(ParameterVal.objects.filter(wf_module=wfm1d).count(), ParameterVal.objects.filter(wf_module=wfm1).count())

        # Stored data should contain a clone of content only, not complete version history
        self.assertIsNotNone(wfm1d.stored_data_version)
        self.assertEqual(wfm1d.stored_data_version, wfm1.stored_data_version)
        self.assertEqual(wfm1d.retrieve_data(), wfm1.retrieve_data())
        self.assertEqual(len(wfm1d.list_stored_data_versions()), 1)


