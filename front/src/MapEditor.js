
import React from 'react'

import { send_command } from './modules/network/connections.js'

import { MapEditorRadarWidget } from './modules/widgets/MapEditorRadar.js';
import { HBodiesSelector, BodyEditor, BodySpawner, MapLoader , ShipScreenLoader} from './modules/widgets/BodiesSelector.js';
import { PerformanceViewer } from './modules/widgets/PerformanceWidget.js';
import { MapEditorBrushesWidget } from './modules/widgets/MapEditorBrushes.js';
import './styles/Administration.css'
import './styles/MapEditor.css'




export class MapEditor extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selected_body_idx: "asdas",
      highlighted_body_idx: "",
      brush_state:{"active": false,},
    }
  }

  componentDidMount() {
    this.take_control(null)
    send_command("hBodiesPool", "admin", "set_realtime_update", { 'value': true })
  }
  componentWillUnmount() {
    send_command("hBodiesPool", "admin", "set_realtime_update", { 'value': false })
  }

  take_control = (key) => {
    send_command("connection", key, "take_control_on_entity", { 'target_id': key })
  }


  restart_simulation = () => {
    send_command("server", null, "restart", null, true)
  }

  onBodyHighlight = (mark_id) => {

    this.setState({ "highlighted_body_idx": mark_id })
  }
  onBodySelect = (mark_id) => {
    this.setState({ "selected_body_idx": mark_id })
  }

  onBrushChange = (brush_state) => {
    this.setState({"brush_state":brush_state})
  }

  render() {
    return (<div

      className='Administration'>
      <h4>Administration</h4>
      <div>

      </div>
      <div
        style={{
          "display": "flex",
          "flex-directin": "row"
        }}>
        <MapLoader></MapLoader>
        <ShipScreenLoader></ShipScreenLoader>
        <MapEditorRadarWidget
          selected_body_idx={this.state.selected_body_idx}
          highlighted_body_idx={this.state.highlighted_body_idx}
          onBodySelect={this.onBodySelect}
          brush_state = {this.state.brush_state}
        />
        <div className='BodiesInteractorSection'>
          <HBodiesSelector
            onBodySelect={this.onBodySelect}
            onBodyHighlight={this.onBodyHighlight} />

          <BodyEditor
            selected_body_idx={this.state.selected_body_idx}

          />
          <BodySpawner
            onBodySelect={this.onBodySelect}
          />
          <MapEditorBrushesWidget
              onBrushChange = {this.onBrushChange}
          />
          <PerformanceViewer>

          </PerformanceViewer>
        </div>
      </div>

    </div>)
  }
}
