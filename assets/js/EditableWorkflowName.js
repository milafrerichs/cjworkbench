import React from 'react';
import _ from 'lodash';
import { RIEInput } from 'riek';
import workbenchapi from './WorkbenchAPI';
import PropTypes from 'prop-types'

export default class EditableWorkflowName extends React.Component {
  constructor(props) {
    super(props);
    this.api = workbenchapi();
    this.saveName = this.saveName.bind(this);
    this.state = {
      value: this.props.value
    }
  }

  saveName(newName) {
    // If blank entry, use default title
    var value = newName.value;
    if (!value || (value == "")) {
      value = "Untitled Workflow";
    }
    this.setState({value: value});
    this.api.setWfName(this.props.wfId, value);
  }

  render() {
    return <h4><RIEInput
      value={this.state.value}
      change={this.saveName}
      propName="value"
      className={this.props.editClass}
    /></h4>
  }
}

EditableWorkflowName.propTypes = {
  value:    PropTypes.string,
  wfId:     PropTypes.number
};


