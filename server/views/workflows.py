from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import renderer_classes
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from server.models import Module, ModuleVersion, Workflow, WfModule
from server.models import AddModuleCommand, ReorderModulesCommand, ChangeWorkflowTitleCommand
from server.serializers import WorkflowSerializer, WorkflowSerializerLite, UserSerializer
from server.versions import WorkflowUndo, WorkflowRedo
from django.db.models import Q
import json

# ---- Workflows list page ----
@login_required
def render_workflows(request):
    user = UserSerializer(request.user)
    initState = {
        'user': user.data
    }
    return TemplateResponse(request, 'workflows.html', {'initState': json.dumps(initState)})

# not login_required as logged out users can view public workflows
def render_workflow(request, pk=None):
    user = UserSerializer(request.user)
    initState = {
        'user': user.data
    }
    return TemplateResponse(request, 'workflow.html', {'initState': json.dumps(initState)})

# ---- Workflow ----

# List all workflows, or create a new workflow.
@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def workflow_list(request, format=None):
    if request.method == 'GET':
        workflows = Workflow.objects.filter(Q(owner=request.user))
        serializer = WorkflowSerializerLite(workflows, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = WorkflowSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Retrieve or delete a workflow instance.
# Or reorder modules
@api_view(['GET', 'PATCH', 'POST', 'DELETE'])
@renderer_classes((JSONRenderer,))
@permission_classes((IsAuthenticatedOrReadOnly, ))
def workflow_detail(request, pk, format=None):
    try:
        workflow = Workflow.objects.get(pk=pk)
    except Workflow.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not workflow.user_authorized_read(request.user):
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WorkflowSerializer(workflow, context={'user' : request.user})
        return Response(serializer.data)

    # We use PATCH to set the order of the modules when the user drags.
    elif request.method == 'PATCH':
        if not workflow.user_authorized_write(request.user):
            return HttpResponseForbidden()

        try:
            ReorderModulesCommand.create(workflow, request.data)
        except ValueError as e:
            # Caused by bad id or order keys not in range 0..n-1 (though they don't need to be sorted)
            return Response({'message': str(e), 'status_code':400}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    elif request.method == 'POST':
        if not workflow.user_authorized_write(request.user):
            return HttpResponseForbidden()

        try:
            if not set(request.data.keys()).intersection({"newName", "public"}):
                raise ValueError('Unknown fields: {}'.format(request.data))

            if 'newName' in request.data:
                ChangeWorkflowTitleCommand.create(workflow, request.data['newName'])

            if 'public' in request.data:
                workflow.public = request.data['public']
                workflow.save()

        except Exception as e:
            return Response({'message': str(e), 'status_code':400}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    elif request.method == 'DELETE':
        if not workflow.user_authorized_write(request.user):
            return HttpResponseForbidden()

        workflow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Invoked when user pressess add_module button
@api_view(['PUT'])
@renderer_classes((JSONRenderer,))
def workflow_addmodule(request, pk, format=None):
    try:
        workflow = Workflow.objects.get(pk=pk)
    except Workflow.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not workflow.user_authorized_write(request.user):
        return HttpResponseForbidden()

    try:
        module_id = request.data['moduleId']
        insert_before = int(request.data['insertBefore'])
        module = Module.objects.get(pk=module_id)

        # always add the latest version of a module
        module_versions = ModuleVersion.objects.filter(module=module)
        module_version=module_versions[len(module_versions)-1]
    except Module.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    delta = AddModuleCommand.create(workflow, module_version, insert_before)

    return Response({"id": delta.wf_module.id}, status.HTTP_201_CREATED)


# Duplicate a workflow. Returns new id
@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def workflow_duplicate(request, pk):
    try:
        workflow = Workflow.objects.get(pk=pk)
    except Workflow.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not workflow.user_authorized_read(request.user):
        return HttpResponseForbidden()

    workflow2 = workflow.duplicate(request.user)

    return Response({"id": workflow2.id}, status.HTTP_201_CREATED)


# Undo or redo
@api_view(['PUT'])
@renderer_classes((JSONRenderer,))
def workflow_undo_redo(request, pk, action, format=None):
    try:
        workflow = Workflow.objects.get(pk=pk)
    except Workflow.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not workflow.user_authorized_write(request.user):
        return HttpResponseForbidden()

    if action=='undo':
        WorkflowUndo(workflow)
    elif action=='redo':
        WorkflowRedo(workflow)

    return Response(status=status.HTTP_204_NO_CONTENT)
