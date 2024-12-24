
import React from 'react'
import { get_navdata, send_command } from '../network/connections';

import { Canvas } from '@react-three/fiber'


import { entityRenderer } from '../renderers/EntityRenderer';
import { entityRendererCursor } from '../renderers/CursorRenderer';
import { timerscounter } from '../utils/updatetimers';
import { get_brush_object } from '../renderers/CursorRenderer';
import { global_observer_pos } from './AdminRadar';
import { get_locales } from '../locales/locales';
export class MapEditorRadarWidget extends React.Component {
  constructor(props) {
    super(props);


    this.state = {
      radar_width: 600,
      scale_factor: 1,

      controlled_observer_pos: [0, 0],

      cursor_position_old: [0, 0],

      data: {
        "observer_pos": [0, 0],
        "hBodies": {},
        "lBodies": {},
        "aZones": {},
      },
      key_pressed: [0, 0],
      clockwise: false,
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
    if (!nav_data) return

    let o = global_observer_pos //this.state.controlled_observer_pos
    o[0] = o[0] + this.state.key_pressed[0]
    o[1] = o[1] + this.state.key_pressed[1]


    nav_data["observer_pos"] = o
    this.setState({
      "data": nav_data,
      "controlled_observer_pos": o
    })
  }

  move_observer = (axis, step) => {
    let o = this.state.controlled_observer_pos
    if (axis === 'X') o[0] = o[0] + step
    if (axis === 'Y') o[1] = o[1] + step

    this.setState({
      "controlled_observer_pos": o
    })
  }

  move_observer_step = (params) => {
    this.setState({
      "key_pressed": params
    })
  }


  onMouseMove = (mouse) => {

    let mouse_position_x = (mouse.x * this.state.radar_width / 2) / this.state.scale_factor + this.state.controlled_observer_pos[0]
    let mouse_position_y = (mouse.y * this.state.radar_width / 2) / this.state.scale_factor + this.state.controlled_observer_pos[1]
    let cursor_position = [mouse_position_x, mouse_position_y]
    if ((this.state.cursor_position_old[0] !== mouse_position_x) && (this.state.cursor_position_old[1] !== mouse_position_y)) {
      this.setState({ "cursor_position_old": cursor_position })
      //console.log("onMouseMove clockwise", this.state.clockwise)
      send_command("map_editor", "marl_id", "cursor_move", { 'position': [mouse_position_x, mouse_position_y], "clockwise": this.state.clockwise })
    }

  }

  get_brush_params = (to_draw) => {
    let tmp = Object.assign({}, this.props.brush_state)
    let mouse_position_x = this.state.cursor_position_old[0]
    let mouse_position_y = this.state.cursor_position_old[1]
    if (to_draw) {
      mouse_position_x = mouse_position_x - this.state.controlled_observer_pos[0]
      mouse_position_y = mouse_position_y - this.state.controlled_observer_pos[1]
    }
    tmp["position"] = [mouse_position_x, mouse_position_y]
    return tmp
  }

  onMouseClick = (e) => {
    if (this.props.brush_state["active"]) {
      let tmp = this.get_brush_params(false)
      if (this.props.brush_state["mode"] == "creator") {
        send_command("map_editor", "admin", "brush_create", tmp)
      }
      else if (this.props.brush_state["mode"] == "obstacles_creator") {
        send_command("map_editor", "admin", "brush_spawn_obstacles", tmp)
      }
      else if (this.props.brush_state["mode"] == "obstacles_deleter") {
        send_command("map_editor", "admin", "brush_delete_obstacles", tmp)
      }
      else if (this.props.brush_state["mode"] == "selector") {
        send_command("map_editor", "admin", "brush_select_body", tmp)
      }
      else if (this.props.brush_state["mode"] == "cacher") {
        send_command("map_editor", "admin", "brush_cache", tmp)
      }
      else if (this.props.brush_state["mode"] == "uncacher") {
        send_command("map_editor", "admin", "brush_uncache", tmp)
      }
      else if (this.props.brush_state["mode"] == "brush_weight_editor"){
        send_command("map_editor", "admin", "brush_edit_weight", tmp)
      }
      else {
        send_command("map_editor", "admin", "brush_delete", tmp)
      }
    }
    else {
      send_command("map_editor", "admin", "select_body", { 'mark_id': null })
    }
  }


  get_buttons_block = () => {
    let step = 20
    return (<div
      className='AccelerationController_btnblock'>
      <button disabled> {"<<<<"} </button>
      <button

        onMouseUp={(e) => { this.move_observer_step([0, 0]) }}
        onMouseDown={(e) => { this.move_observer_step([0, step]) }}
      > Forw </button>
      <button disabled> {">>>>"} </button>

      <button

        onMouseUp={(e) => { this.move_observer_step([0, 0]) }}
        onMouseDown={(e) => { this.move_observer_step([-step, 0]) }}
      > TLeft </button>
      <button

        onMouseUp={(e) => { this.move_observer_step([0, 0]) }}
        onMouseDown={(e) => { this.move_observer_step([0, -step]) }}
      > Back </button>
      <button

        onMouseUp={(e) => { this.move_observer_step([0, 0]) }}
        onMouseDown={(e) => { this.move_observer_step([step, 0]) }}
      > TRight </button>
    </div>)
  }

  get_cursor_position = () => {
    let offset = this.state["cursor_position_old"]




    //let mouse_position_x = (this.state.cursor_position_old[0] * this.state.radar_width / 2) / this.state.scale_factor + offset[0]
    //let mouse_position_y = (this.state.cursor_position_old[1] * this.state.radar_width / 2) / this.state.scale_factor + offset[1]




    //let position = [Math.round(mouse_position_x, 2), Math.round(mouse_position_y, 2)]
    return offset
  }

  render() {
    let objects = entityRenderer.get_objects_from_data(this.state.data, this.state.scale_factor, { "show_gravity": true })
    let selection_objects = entityRenderer.get_selection_marker(this.state.data, this.state.scale_factor, this.props.selected_body_idx)
    let highlighted_objects = entityRenderer.get_selection_marker(this.state.data, this.state.scale_factor, this.props.highlighted_body_idx)
    let aim_markers = entityRendererCursor.get_objects_from_data(this.onMouseMove, this.onMouseClick)
    let radar_size = this.state.radar_width.toString() + "px"
    let brush_objects = get_brush_object(this.get_brush_params(true), this.state.scale_factor)


    let cursor_position = this.get_cursor_position()
    return (<div
      style={{
        'display': 'flex',
        'flex-direction': 'column',
        'align-items': 'center',
        'width': "620px",
        'height': "700px",
        'border': 'solid 1px',

      }}
    >
      <Canvas
        //resize = {{ scroll: true, debounce: { scroll: 50, resize: 0 } }}
        orthographic={true}

        style={{
          'width': radar_size,
          'height': radar_size,
          'border': 'solid',
          'background': 'black'
        }}
      >
        <ambientLight />
        {objects}
        {aim_markers}
        {selection_objects}
        {highlighted_objects}
        {brush_objects}
      </Canvas>

      <div
        style={{
          "display": "flex",
          "flex-direction": "row",
          "justify-content": "space-between"
        }}>
        <label>SCALE: <input
          type="range"
          min={0.05}
          max={2}
          step={0.02}
          class="slider"
          id="valueForward"
          value={this.state.scale_factor}
          onChange={(e) => {
            this.setState({ scale_factor: e.target.value })

          }}
        //value={this.state.progradeAcc}
        /> </label>
        {parseFloat(this.state.scale_factor).toFixed(2)}
        <label>
          "frame_id:"{this.state.frame_id}
        </label>
        {this.get_buttons_block()}
        <button onClick={() => { this.setState({ controlled_observer_pos: [0, 0] }) }}> CLEAR OFFSET</button>
      </div>
      <label>Clockwise:<input type="checkbox" value={this.state.clockwise} onChange={(e) => { this.setState({ "clockwise": e.target.checked }) }}></input></label>
      <label>{get_locales("CURSOR_POS")}: {cursor_position[0].toFixed(0)},{cursor_position[1].toFixed(0)}</label>
    </div >)
  }
}

















