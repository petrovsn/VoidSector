import React from 'react'
import { send_command, get_navdata, get_capmarks, get_solarflare, is_taking_damage, get_map_border } from '../network/connections';

import { Canvas } from '@react-three/fiber'


import { entityRenderer } from '../renderers/EntityRenderer';
import { radarRenderer } from '../renderers/RadarRenderer';

import { entityRendererCursor } from '../renderers/CursorRenderer';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';
import { ShipOvervieweWidget } from './ShipOverview';
export class PlayersRadarWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      scale_width: 600,
      scale_factor: 1,
      radar_width: 600,
      data: {
        "mark_id": "",
        "observer_pos": [0, 0],
        "hBodies": {},
        "lBodies": {},
      },

      entities_list: [],
      entity_hovered: "",

      mouse_pos: 0,
      show_id_labels: true
    }
  }

  componentDidMount() {
    let timer_id = timerscounter.get(this.constructor.name)
    if (!timer_id) {
      clearInterval(timer_id)
    }
    timer_id = setInterval(this.proceed_data_message, 30)
    timerscounter.add(this.constructor.name, timer_id)
  }

  componentWillUnmount() {
    let timer_id = timerscounter.get(this.constructor.name)
    clearInterval(timer_id)
  }

  proceed_data_message = () => {

    let nav_data = get_navdata()

    let cap_marks = get_capmarks()
    this.setState({
      "data": nav_data,
      "cap_marks": cap_marks
    })



  }

  set_entity_hovered = (s) => {
    this.setState({ entity_hovered: s })
  }





  onMouseMove = (mouse) => {
    if ((this.state.mouse_pos[0] !== mouse.x) && (this.state.mouse_pos[0] !== mouse.y)) {
      this.setState({ "mouse_pos": [mouse.x, mouse.y] })

      if (!this.props.can_aim) return

      let vel_angle = mouse.angle() * 180 / 3.14
      let vel_salar = Math.min(mouse.length(), 1)

      send_command("ship.launcher_sm", this.state.data.mark_id, "aim", {
        "vel_angle": vel_angle,
        "vel_scalar": vel_salar
      })
    }
  }

  onMouseClick = () => {

    if (this.props.cap_control) {
      this.onSetMark()
    }
    else {
      this.onLaunch()
    }
  }

  onLaunch = () => {
    if (this.props.can_aim)
      send_command("ship.launcher_sm", this.state.data.mark_id, "launch", {})
  }

  onSetMark = () => {



    let offset = this.state.data["observer_pos"]




    let mouse_position_x = (this.state.mouse_pos[0] * this.state.radar_width / 2) / this.state.scale_factor + offset[0]
    let mouse_position_y = (this.state.mouse_pos[1] * this.state.radar_width / 2) / this.state.scale_factor + offset[1]




    let position = [Math.round(mouse_position_x, 2), Math.round(mouse_position_y, 2)]
    send_command("ship.cap_marks", this.state.data.mark_id, "make_point", { "position": position })



  }

  get_cursor_position = () => {
    let offset = this.state.data["observer_pos"]




    let mouse_position_x = (this.state.mouse_pos[0] * this.state.radar_width / 2) / this.state.scale_factor + offset[0]
    let mouse_position_y = (this.state.mouse_pos[1] * this.state.radar_width / 2) / this.state.scale_factor + offset[1]




    let position = [Math.round(mouse_position_x, 2), Math.round(mouse_position_y, 2)]
    return position
  }

  get_solar_flare_timer = () => {
    let solar_flare_state = get_solarflare()
    if (solar_flare_state) {
      if (solar_flare_state["state"]) {
        return (
          <label className='sf_active'>
            {get_locales("time_to_next_sf_phase")}: {solar_flare_state["time2nextphase"]}
          </label>
        )
      }
      else {
        if (solar_flare_state["timer_state"]) {
          return <label className='sf_active'>
            {get_locales("time_to_flare")}: {solar_flare_state["time2nextphase"]}
          </label>
        }
        else {
          let label_style = "sf_low"
          if (solar_flare_state["probability"] == "high") label_style = "sf_high"
          return (
            <label className={label_style}>
              {get_locales("sf_probability")}: {get_locales(solar_flare_state["probability"])}
            </label>)
        }
      }
    }
  }

  render() {
    let aim_markers = entityRendererCursor.get_objects_from_data(this.onMouseMove, this.onMouseClick)
    if (aim_markers.length === 0) aim_markers = this.props.cap_control ? entityRendererCursor.get_objects_from_data(this.onMouseMove, this.onSetMark) : []
    let cap_markers = radarRenderer.get_capmarks(this.state.cap_marks, this.state.data, this.state.scale_factor)
    let scan_markers = radarRenderer.get_objects_from_data(this.state.data, this.state.scale_factor)
    let objects = entityRenderer.get_objects_from_data(this.state.data, this.state.scale_factor, { "show_id_labels": this.state.show_id_labels, 'arrow_scaling': this.props.arrow_scaling, "map_border": get_map_border() })
    let selection_objects = entityRenderer.get_selection_marker(this.state.data, this.state.scale_factor, this.state.entity_hovered)
    let solar_flares = radarRenderer.get_solar_flares_shades(get_solarflare())
    let damage_shades = radarRenderer.get_damage_shades(is_taking_damage())

    //if (scan_params) radar_arcs= getDistantScanArc(scan_params.close_range, scan_params.distant_range, scan_params.distant_arc, scan_params.distant_dir, [0,0], this.state.scale_factor)



    let cursor_position = this.get_cursor_position()
    return (<div className='PlayersRadar'
    >

      <div className="radarSection">
        <Canvas
          className={"PlayerRadarCanvas"}
          id={"MyCanvas"}
          //resize = {{ scroll: true, debounce: { scroll: 50, resize: 0 } }}
          orthographic={true}


          style={{
            'width': "600px",
            'height': "600px",
            'border': 'solid',
            'background': 'black'
          }}
        >
          <ambientLight />
          {aim_markers}
          {objects}
          {scan_markers}
          {selection_objects}
          {cap_markers}
          {solar_flares}
          {damage_shades}
          onClick = {this.state.onMouseMove}
        </Canvas>
        <div className='RadarShipInfoLayer'>
          <ShipOvervieweWidget
            onSystemSelection={(e) => { }}
          ></ShipOvervieweWidget>
          <div className='ShipNavigationInfo'>
            <label>{get_locales("SCALE")}: <input
              type="range"
              min={0.1}
              max={2}
              step={0.02}
              class="slider"
              id="valueForward"
              value={this.state.scale_factor}
              onChange={(e) => {
                this.setState({ scale_factor: e.target.value })

              }}
            //value={this.state.progradeAcc}
            /> {parseFloat(this.state.scale_factor).toFixed(2)}</label>
            <label>{get_locales("POS")}: {this.state.data.observer_pos[0].toFixed(0)},{this.state.data.observer_pos[1].toFixed(0)}</label>
            <label>{get_locales("CURSOR_POS")}: {cursor_position[0].toFixed(0)},{cursor_position[1].toFixed(0)}</label>
            <label> {get_locales("toogle_id_labels")} <input type="checkbox" checked={this.state.show_id_labels} onChange={(e) => { this.setState({ "show_id_labels": e.target.checked }) }}></input> </label>
            {this.get_solar_flare_timer()}
          </div>
        </div>
      </div>
    </div >)
  }
}
