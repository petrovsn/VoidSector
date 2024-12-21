
import React from 'react'
import { get_navdata, send_command } from '../network/connections';

import { Canvas } from '@react-three/fiber'


import { entityRenderer } from '../renderers/EntityRenderer';
import { entityRendererCursor } from '../renderers/CursorRenderer';
import { timerscounter } from '../utils/updatetimers';
import { NumericControlWidjet } from './NumericControlWidget';

export class MapEditorBrushesWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      "mode": "deleter", //"creator"
      "active": false,
      "radius": 1000,
      "min_size": 140,
      "max_size": 150,
      "min_weight": 1,
      "max_weight": 5,
      "obstacles_type":"MeteorsCloud",
      "closer":false,
    }

  }



  onChangeParam = (key, value) => {
    let tmp = this.state
    tmp[key] = value
    this.props.onBrushChange(tmp)
    this.setState(tmp)
  }

  get_mode_selector = () => {
    let result = []
    let options = ["deleter", "creator", "brush_weight_editor", "obstacles_creator", "obstacles_deleter", "selector", "cacher", "uncacher"]
    for (let tmp_i in options) {
      result.push(
        <button
          onClick={(e) => {
            this.onChangeParam("mode", options[tmp_i])
          }}
        >
          {options[tmp_i]}
        </button>
      )
    }
    return <div>
      {result}
    </div>
  }


  get_creator_params = () => {
    let inputs = []
    let keys = ["radius", "min_size", "max_size", "min_weight", "max_weight"]
    for (let tmp_i in keys) {
      let keyname = keys[tmp_i]
      inputs.push(
        <label> {keyname}: <input onChange={(e) => { this.onChangeParam(keyname, parseFloat(e.target.value)) }} value={this.state[keyname]}></input></label>
      )
    }
    let keyname = "closer"
    inputs.push(
      <label> {keyname}: <input type='checkbox' onChange={(e) => { this.onChangeParam(keyname, e.target.checked) }} value={this.state[keyname]}></input></label>
    )
    return <div style={
      {
        "display": "flex",
        "flex-direction": "column"
      }}>{inputs}</div>
  }

  get_obstacles_creator_params = () => {
    let inputs = []
    let keys = ["radius"]
    for (let tmp_i in keys) {
      let keyname = keys[tmp_i]
      inputs.push(
        <label> {keyname}: <input onChange={(e) => { this.onChangeParam(keyname, parseFloat(e.target.value)) }} value={this.state[keyname]}></input></label>
      )
    }

    let keyname2 = "obstacles_type"
    inputs.push(
      <label> {keyname2}: <select onChange={(e) => { this.onChangeParam(keyname2, e.target.value) }} value={this.state[keyname2]}>
        <option value={"MeteorsCloud"}>MeteorsCloud</option>
        <option value={"Mine_type1"}>Mine_type1</option>
        <option value={"Mine_type2"}>Mine_type2</option>
        <option value={"Mine_type1/Mine_type2"}>Mine_type1/Mine_type2</option>
        </select></label>
    )

    keys = ["obstacles_min_count", "obstacles_max_count", "obstacles_probability"]
    for (let tmp_i in keys) {
      let keyname = keys[tmp_i]
      inputs.push(
        <label> {keyname}: <input onChange={(e) => { this.onChangeParam(keyname, parseFloat(e.target.value)) }} value={this.state[keyname]}></input></label>
      )
    }


    return <idv style={
      {
        "display": "flex",
        "flex-direction": "column"
      }
    }>{inputs}</idv>
  }

  get_deleter_params = () => {
    let inputs = []
    let keys = ["radius"]
    for (let tmp_i in keys) {
      let keyname = keys[tmp_i]
      inputs.push(
        <label> {keyname}: <input onChange={(e) => { this.onChangeParam(keyname, parseFloat(e.target.value)) }} value={this.state[keyname]}></input></label>
      )
    }
    return <idv style={
      {
        "display": "flex",
        "flex-direction": "column"
      }
    }>{inputs}</idv>
  }

  get_params_panel = () => {
    if (this.state.mode == "creator") {
      return (this.get_creator_params())
    }
    if (this.state.mode == 'brush_weight_editor'){
      return (this.get_creator_params())
    }
    if (this.state.mode == "obstacles_creator") {
      return (this.get_obstacles_creator_params())
    }
    if (this.state.mode == "obstacles_deleter") {
      return (this.get_deleter_params())
    }
    if (this.state.mode == "deleter") {
      return (this.get_deleter_params())
    }
    if (this.state.mode == "selector") {
      return (this.get_deleter_params())
    }
    if (this.state.mode == "cacher") {
      return (this.get_deleter_params())
    }
    if (this.state.mode == "uncacher") {
      return (this.get_deleter_params())
    }
  }

  render() {
    let inputs = [
      <label> State:<button onClick={(e) => { this.onChangeParam("active", !this.state.active) }}> {this.state.active.toString()} </button> </label>,
      this.get_mode_selector()
    ]



    return (<div style={{
      "display": "flex",
      "flex-direction": "column"
    }}>
      <b>Brush Controller</b>
      {inputs}
      {this.get_params_panel()}
    </div>)
  }
}

















