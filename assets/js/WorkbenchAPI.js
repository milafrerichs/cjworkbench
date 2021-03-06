// Wraps all API calls. Useful both to centralize and abstract these calls,
// also for dependency injection for testing

import { csrfToken } from './utils'

// All API calls which fetch data return a promise which returns JSON
class WorkbenchAPI {

  loadWorkflow(workflowId) {
    return (
      fetch('/api/workflows/' + workflowId, { credentials: 'include'})
      .then(response => response.json()))
  }

  addModule(workflowId, moduleId, insertBefore) {
    return (
      fetch(
        '/api/workflows/' + workflowId + "/addmodule",
        {
          method: 'put',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({insertBefore: insertBefore, moduleId: moduleId})
        }
      ).then(response => response.json())
    )
  }

  deleteModule(wfModuleId) {
    return (
      fetch('/api/wfmodules/' + wfModuleId, {
        method: 'delete',
        credentials: 'include',
        headers: {'X-CSRFToken': csrfToken}
      }));
  }

  setWorkflowPublic(workflowID, isPublic) {
    return (
      fetch('/api/workflows/' + workflowID, {
        method: 'post',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({'public': isPublic})
      }));
  }

  onParamChanged(paramID, newVal) {
    return (
      fetch('/api/parameters/' + paramID, {
        method: 'patch',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(newVal)
      }));
  }

  render(wf_module_id, startrow, endrow) {
    var url = '/api/wfmodules/' + wf_module_id + '/render';

    if (startrow || endrow) {
      url += "?";
      if (startrow) {
        url += "startrow=" + startrow;
      }
      if (endrow) {
        if (startrow)
          url += "&";
        url += "endrow=" + endrow;
      }
    }

    return (
      fetch(url, {credentials: 'include'})
      .then(response => response.json())
    )
  }

  input(wf_module_id) {
    return (
      fetch('/api/wfmodules/' + wf_module_id + '/input', {credentials: 'include'})
      .then(response => response.json())
    )
  }

  // All available modules in the system
  getModules() {
    return (
      fetch('/api/modules/', { credentials: 'include' })
      .then(response => response.json())
    )
  }

  getWfModuleVersions(wf_module_id) {
    // NB need parens around the contents of the return, or this will fail miserably (return undefined)
    return (
        fetch('/api/wfmodules/' + wf_module_id + '/dataversions', {credentials: 'include'})
        .then(response => response.json())
    )
  }

  setWfModuleVersion(wf_module_id, version) {
    return (
      fetch('/api/wfmodules/' + wf_module_id + '/dataversions', {
        method: 'patch',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          selected: version
        })
      }))
  }

  setWfModuleNotes(wf_module_id, text) {
    return (
      fetch('/api/wfmodules/' + wf_module_id, {
        method: 'patch',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          notes: text
        })
      }))
  }

  /** 
   * Toggles whether the module is collapsed or expanded on the front-end. 
   * This gets saved on the back-end, and so the state (collapsed or 
   * expanded) persists across multiple sessions. 
   */
  toggleWfModuleCollapsed(wf_module_id, isCollapsed) {
    return (
      fetch('/api/wfmodules/' + wf_module_id, {
        method: 'patch',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          collapsed: isCollapsed
        })
      }))
  }

  setWfName(wfId, newName) {
    return (
      fetch('/api/workflows/' + wfId, {
        method: 'post',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          newName: newName
        })
      })
    )
  }

  // Params should be an object matching format below
  setWfModuleUpdateSettings(wf_module_id, params) {
    return (
      fetch('/api/wfmodules/' + wf_module_id, {
        method: 'patch',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          'auto_update_data' : params.auto_update_data,  // bool
          'update_interval'  : params.update_interval,   // int
          'update_units'     : params.update_units       // str
        })
      })
    )
  }

  undo(workflow_id) {
    return (
      fetch('/api/workflows/' + workflow_id + '/undo', {
        method: 'put',
        credentials: 'include',
        headers: {
          'X-CSRFToken': csrfToken
        }
      }))
  }

  redo(workflow_id) {
    return (
      fetch('/api/workflows/' + workflow_id + '/redo', {
        method: 'put',
        credentials: 'include',
        headers: {
          'X-CSRFToken': csrfToken
        }
      }))
  }

  duplicate(workflow_id) {
    return (
      fetch('/api/workflows/' + workflow_id + '/duplicate', {credentials: 'include'})
        .then(response => response.json())
    )
  }

}

// Singleton API object for global use
const api = new WorkbenchAPI();
export default () => { return api; }
