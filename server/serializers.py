from rest_framework import serializers
from server.models import Workflow, WfModule, ParameterVal, ParameterSpec, Module, ModuleVersion, StoredObject
from server.utils import seconds_to_count_and_units
from account.utils import user_display
from django.contrib.auth import get_user_model

User = get_user_model()

class StoredObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoredObject
        fields = '__all__'

# So far, no one actually wants to see the default value.
class ParameterSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterSpec
        fields = ('id', 'name', 'id_name', 'type', 'multiline')

class ParameterValSerializer(serializers.ModelSerializer):
    parameter_spec = ParameterSpecSerializer(many=False, read_only=True)

    # Custom serialization for value, to return correct types (e.g. boolean for checkboxes)
    value = serializers.SerializerMethodField()
    def get_value(self, obj):
        return obj.get_value()

    class Meta:
        model = ParameterVal
        fields = ('id', 'parameter_spec', 'value', 'visible', 'menu_items')


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('id', 'name', 'category', 'description', 'link', 'author', 'icon')

class ModuleVersionSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(many=False, read_only=True)
    class Meta:
        model = ModuleVersion
        fields = ('module', 'source_version_hash', 'last_update_time')

class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    def get_display_name(self, obj):
        return user_display(obj)

    class Meta:
        model = User
        fields = ('email', 'display_name', 'id')


class WfModuleSerializer(serializers.ModelSerializer):
    parameter_vals = ParameterValSerializer(many=True, read_only=True)
    module_version = ModuleVersionSerializer(many=False, read_only=True)

    # update interval handling is a little tricky as we need to convert seconds to count+units
    update_interval = serializers.SerializerMethodField()
    def get_update_interval(self, wfm):
        return seconds_to_count_and_units(wfm.update_interval)['count']

    update_units = serializers.SerializerMethodField()
    def get_update_units(self, wfm):
        return seconds_to_count_and_units(wfm.update_interval)['units']

    class Meta:
        model = WfModule
        fields = ('id', 'module_version', 'workflow', 'status', 'error_msg', 'parameter_vals', 'is_collapsed',
                  'notes', 'auto_update_data', 'update_interval', 'update_units', 'last_update_check')


class WorkflowSerializer(serializers.ModelSerializer):
    wf_modules = WfModuleSerializer(many=True, read_only=True)
    revision = serializers.ReadOnlyField()
    read_only = serializers.SerializerMethodField()
    last_update = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    def get_read_only(self, obj):
        return obj.read_only(self.context['user'])

    def get_last_update(self, obj):
        if not obj.last_delta:
            return obj.creation_date
        return obj.last_delta.datetime

    def get_owner_name(self, obj):
        return user_display(obj.owner)

    class Meta:
        model = Workflow
        fields = ('id', 'name', 'revision', 'wf_modules', 'public', 'read_only', 'last_update', 'owner_name')


# Lite Workflow: Don't include any of the modules, just name and ID. For /workflows page
class WorkflowSerializerLite(serializers.ModelSerializer):
    last_update = serializers.SerializerMethodField()
    def get_last_update(self, obj):
        if not obj.last_delta:
            return obj.creation_date
        return obj.last_delta.datetime

    read_only = serializers.SerializerMethodField()
    def get_read_only(self, obj):
        return False                    # lite serializer is only used when listing workflows, which only owner can do

    class Meta:
        model = Workflow
        fields = ('id', 'name', 'public', 'read_only', 'last_update')
