// workflow.page.js - the master JavaScript for /workflows/N

import React from 'react'
import ReactDOM from 'react-dom'
import { Provider, connect } from 'react-redux'
import * as Actions from './workflow-reducer'
import { getPageID, csrfToken } from './utils'
import Workflow from './workflow'
import workbenchAPI from './WorkbenchAPI'

require('bootstrap/dist/css/bootstrap.css');
require('../css/style.css');

// Global API object, encapsulates all calls to the server
const api = workbenchAPI();

// ---- Workflow container ----

// Handles addModule (and any other actions that change top level workflow state)
const mapStateToProps = (state) => {
  return {
    workflow: state.workflow,
    selected_wf_module: state.selected_wf_module,
    user: state.user,
    // This is the top level dependency injection for all API calls on this page
    api: api
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    addModule: (module_id, insertBefore) => {
      dispatch(Actions.addModuleAction(module_id, insertBefore))
    },
    removeModule: (wf_module_id) => {
      dispatch(Actions.removeModuleAction(wf_module_id))
    },
    changeParam: (paramID, newVal) => {
      api.onParamChanged(paramID, newVal)
    }
  }
}

const WorkflowContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(Workflow)



// --- Websocket handling ----

// Start listening for events
const socket = new WebSocket("ws://" + window.location.host + "/workflows/" + getPageID());

socket.onmessage = function(e) {
  var data = JSON.parse(e.data);
  if ('type' in data) {
    switch (data.type) {

      case 'wfmodule-status':
        Actions.store.dispatch(Actions.wfModuleStatusAction(data.id, data.status, data.error_msg ? data.error_msg : ''));
        return

      case 'reload-workflow':
        Actions.store.dispatch(Actions.reloadWorkflowAction());
        return
    }
  }
}


// --- Main ----

// Render with Provider to root so all objects in the React DOM can access state
ReactDOM.render(
    <Provider store={Actions.store}>
      <WorkflowContainer/>
    </Provider>,
    document.getElementById('root')
);

// Load the page, Select the first module in the workflow (if one exists, else shows Module Library)
Actions.store.dispatch(Actions.initialLoadWorkflowAction())
