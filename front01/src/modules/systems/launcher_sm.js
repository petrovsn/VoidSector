import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';
import '../../styles/ShaftsControlWidget.css'

export class ShaftsControlWidget extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      data: null,
      vel_scalar: 0,
      vel_angle: 0
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
    let system_state = get_system_state("launcher_sm")

    this.setState({
      "data": system_state
    })
  }

  get_shafts_section = () => {
    if (!this.state.data) return <div></div>

    let shafts_controllers = []

    for (let k in this.state.data['shafts']) {
      shafts_controllers.push(<LauncherShaftController
        shaft_state={this.state.data['shafts'][k]}
        shaft_id={k}
        mark_id={this.state.data.mark_id}
      />)
    }
    return <div className='shaftsSection'>{shafts_controllers}</div>
  }

  onLaunch = () => {
    send_command("ship.launcher_sm", this.state.data.mark_id, "launch", {})
  }

  onAim = () => {
    send_command("ship.launcher_sm", this.state.data.mark_id, "aim", {
      "vel_angle": this.state.vel_angle,
      "vel_scalar": this.state.vel_scalar
    })
  }

  is_disabled = () => {
    if (this.state.data) {
      if ((this.state.data.status === "OK") && (this.state.data.mark_id)) return false
    }
    return true
  }

  render() {

    let shafts_controllers = []
    let auto_toogle = false
    let auto_reload = false
    if (!this.is_disabled()) {
      shafts_controllers = this.get_shafts_section()
      auto_toogle = this.state.data["auto_toggle"]
      auto_reload = this.state.data["auto_reload"]
    }
    return (
      <div className='LauncherController'>

        <label><b>{get_locales("ProjectileLauncher Control")}</b> {get_locales("auto_toggle")}:
          <input type="checkbox" checked={auto_toogle} onChange={(e) => {
            send_command("ship.launcher_sm", this.state.data.mark_id, "auto_toggle", { "active": e.target.checked })
          }}></input>

          {get_locales("auto_reload")}:
          <input type="checkbox" checked={auto_reload} onChange={(e) => {
            send_command("ship.launcher_sm", this.state.data.mark_id, "auto_reload", { "active": e.target.checked })
          }}></input>
        </label>

        {shafts_controllers}
      </div>)
  }


}



export class LauncherShaftController extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      projectile_type: null,
      launch_params: {},
    }
  }

  send_launch_params = () => {
    send_command("ship.launcher_sm.shaft", this.props.mark_id + '..' + this.props.shaft_id, "set_projectile_params", this.state.launch_params)
  }

  set_launch_params = (key, value) => {
    let tmp = this.state.launch_params
    tmp[key] = value
    this.setState({ launch_params: tmp }, this.send_launch_params())
  }

  get_params_widget = (key) => {
    let min_value = this.props.shaft_state.launch_params[key][0]
    let max_value = this.props.shaft_state.launch_params[key][1]
    let step_value = this.props.shaft_state.launch_params[key][2]
    let init_value = this.props.shaft_state.launch_params[key][3]

    if (!(key in this.state.launch_params)) {
      let tmp = this.state.launch_params
      tmp[key] = init_value
      this.setState({ launch_params: tmp })
    }

    return <span className='projectile_param_widget'>
      {key}
      <input

        type="range"
        min={min_value}
        max={max_value}
        step={step_value}
        class="slider"
        onChange={(e) => {
          this.set_launch_params(key, e.target.value)
        }}
        value={this.state.launch_params[key]}

      />
      <output>{this.state.launch_params[key]}</output>
    </span>
  }

  get_params_widgets = () => {
    let params_adjusters = []
    for (let k in this.props.shaft_state.launch_params) {
      params_adjusters.push(this.get_params_widget(k))
    }
    return params_adjusters

  }


  get_available_projectiles_options = () => {
    let options = []
    for (let i in this.props.shaft_state.available_projectiles) {
      let option = this.props.shaft_state.available_projectiles[i]
      options.push(<option value={option}> {option} </option>)
    }
    return options
  }

  load_projectile = () => {
    this.setState({ launch_params: {} })
    send_command("ship.launcher_sm.shaft", this.props.mark_id + '..' + this.props.shaft_id, "load_projectile", { "type": this.state.projectile_type })
  }
  unload_projectile = () => {
    this.setState({ launch_params: {} })
    send_command("ship.launcher_sm.shaft", this.props.mark_id + '..' + this.props.shaft_id, "load_projectile", { "type": null })
  }

  select_shaft = () => {
    send_command("ship.launcher_sm", this.props.mark_id, "select_shaft", { "shaft_id": this.props.shaft_id })
  }

  render() {
    let labels = []
    for (let k in this.props.shaft) {
      labels.push(<label>{k}:{this.props.shaft[k].Str}</label>)
    }

    let shaftprogress_classname = ""

    if (this.props.shaft_state["progress"] >= 100) {
      shaftprogress_classname = "LauncherShaftController_shaft_progress_ready"
    }
    else if ((this.props.shaft_state["progress"] > 0) && (this.props.shaft_state["progress"] <= 100)) {
      shaftprogress_classname = "LauncherShaftController_shaft_progress_in_progres"
    }
    let additional_ClassName = this.props.shaft_state["selected"] ? "LauncherShaftController_selected" : ""
    // <label>type: {this.props.shaft_state["loaded_type"]}</label>
    return (<div className={'LauncherShaftController ' + additional_ClassName}>
      <button onClick={() => { this.select_shaft() }}><b>{get_locales("SHAFT")}# {this.props.shaft_id} </b></button>

      <div className={"LauncherShaftController_shaft_progress " + shaftprogress_classname}>
        <progress value={this.props.shaft_state["progress"]} max="100"></progress>
      </div>
      <select
        onChange={(e) => { this.setState({ projectile_type: e.target.value }) }}
      >
        <option default value={null}> {null}</option>
        {this.get_available_projectiles_options()}
      </select>

      {this.get_params_widgets()}
      <button onClick={() => { this.load_projectile() }}> {get_locales("load")}</button>
      <button onClick={() => { this.unload_projectile() }}> {get_locales("unload")}</button>

    </div>)
  }
}
