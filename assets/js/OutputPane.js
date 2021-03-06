// Display of output from currently selected module

import React from 'react'
import TableView from './TableView'
import PropTypes from 'prop-types'

export default class OutputPane extends React.Component {

  constructor(props) {
    super(props);

    // componentDidMount will trigger first load
    this.startState = {
      tableData: null,
      lastLoadedRow : 0,
    };
    this.state = this.startState;

    this.getRow = this.getRow.bind(this);

    // loading flag cannot be in state because we need to suppress fetches in getRow, which is called many times in a tick
    this.loading = false;

    // constants to control loading behaviour
    this.initialRows = 120;   // because react-data-grid seems to preload to 100
    this.preloadRows = 20;    // get new rows when we are this close to the end
    this.deltaRows = 100;     // get this many new rows at a time
  }

  // Load table data from render API
  loadTable(id, toRow) {
    if (id) {
      // console.log("Asked to load to " + toRow );

      this.loading = true;
      this.props.api.render(id, this.state.lastLoadedRow, toRow)
        .then(json => {

          // console.log("Got data to " + json.end_row);
          // Add just retrieved rows to current data, if any
          if (this.state.tableData) {
            json.rows = this.state.tableData.rows.concat(json.rows);
            json.start_row = 0;  // no one looks at this currently, but they might
          }

          // triggers re-render
          this.loading = false;
          this.setState({
            tableData: json,
            lastLoadedRow : json.end_row
          });

        });
    }
  }

  // Load first 100 rows of table when first rendered
  componentDidMount() {
    this.loadTable(this.props.id, this.initialRows)
  }

  // If the revision changes from under us, or we are displaying a different output, reload the table
  componentWillReceiveProps(nextProps) {
    if (this.props.revision != nextProps.revision || this.props.id != nextProps.id) {
      // Reset our state to "empty", then use callback to start loading some rows
      this.setState(this.startState, () => this.loadTable(nextProps.id, this.initialRows));
    }
  }

  // Update only when we are not loading
//  shouldComponentUpdate(nextProps, nextState) {
//    return !nextState.loading;
//  }

  emptyRow() {
    return this.state.tableData.columns.reduce( (obj,col) => { obj[col]=null; return obj; }, {} );
  }

  getRow(i) {
    if (this.state.tableData) {

      // Time to load more rows?
      if (!this.loading) {
        var target = Math.min(i + this.preloadRows, this.state.tableData.total_rows);  // don't try to load past end of data
        if (target > this.state.lastLoadedRow) {
          //console.log("Triggered reload at getRow " + i);
          this.loadTable(this.props.id, this.state.lastLoadedRow + this.deltaRows);
        }
      }

      // Return the row if we have it
      if (i < this.state.lastLoadedRow ) {
        return this.state.tableData.rows[i];
      } else {
        return this.emptyRow();
      }

    } else {
        // nothing loaded yet
        return null;
    }
  }

  render() {

    // Make a table component if we have the data
    var tableView = null;
    var nrows = 0;
    var ncols = 0;
    if (this.props.id && this.state.tableData && this.state.tableData.total_rows>0) {
      tableView =
        <div className="outputpane-data">
          <TableView
            totalRows={this.state.tableData.total_rows}
            columns={this.state.tableData.columns}
            getRow={this.getRow}
          />
        </div>
      nrows = this.state.tableData.total_rows;
      ncols = this.state.tableData.columns.length;
    }

    return (
      <div className="outputpane-box">
        <div className="outputpane-header d-flex flex-row justify-content-start">
          <div className='d-flex flex-column align-items-center justify-content-center mr-5'>
            <div className='content-4 t-m-gray mb-2'>Rows</div>
            <div className='content-2 t-d-gray'>{nrows}</div>
          </div>
          <div className='d-flex flex-column align-items-center justify-content-center'>
            <div className='content-4 t-m-gray mb-2'>Columns</div>
            <div className='content-2 t-d-gray'>{ncols}</div>
          </div>
        </div>
        {tableView}
      </div>
    );
  }
}

OutputPane.propTypes = {
  id:       PropTypes.number,
  revision: PropTypes.number,
  api:      PropTypes.object.isRequired
};


