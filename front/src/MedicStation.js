
import React from 'react'
import { take_control } from './modules/network/connections';
import './styles/MedicStation.css'
import { get_locales } from './modules/locales/locales';

import { send_command, get_system_state, get_observer_id, get_http_address } from './modules/network/connections';
import { timerscounter } from './modules/utils/updatetimers';
export class MedicStation extends React.Component {
  constructor(props) {
    super(props);


    this.state = {
      plague_matrix: null,
      data: {

      },
      hided: true,
    }
  }

  componentDidMount() {
    let timer_id = timerscounter.get(this.constructor.name)
    if (!timer_id) {
      clearInterval(timer_id)
    }

    timer_id = setInterval(this.proceed_data_message, 30)
    timerscounter.add(this.constructor.name, timer_id)


    let timer_id2 = timerscounter.get(this.constructor.name + "_plague")
    if (!timer_id2) {
      clearInterval(timer_id2)
    }
    timer_id2 = setInterval(this.update_plague_matrix, 1000)
    timerscounter.add(this.constructor.name + "_plague", timer_id2)

    if (!get_observer_id()) {
      take_control("Sirocco")
    }
  }

  componentWillUnmount() {
    let timer_id = timerscounter.get(this.constructor.name)
    clearInterval(timer_id)
    timer_id = timerscounter.get(this.constructor.name + "_plague")
    clearInterval(timer_id)
  }

  update_plague_matrix = () => {
    var myInit = {
      method: "GET",
      headers: { "username": this.username },
    }

    return fetch(get_http_address() + "/medicine/plague_matrix", myInit)
      .then(response => {
        let code = response.status;
        if (code === 200) {
          return response.json()
        }
      }).then(data => {
        console.log("update_plague_matrix", data)
        this.setState({ "plague_matrix": data["plague_matrix"] })
      }).catch(data => {
        //console.log(data)
      })
  }

  proceed_data_message = () => {
    let med_data = get_system_state("med_sm")
    if (med_data) this.setState({ "data": med_data })
  }



  get_playerole_cards = () => {
    let result = [<b>{get_locales("Hospital Crew Control")}</b>]
    for (let rolename in this.state.data.roles) {
      result.push(<PlayerRoleHealthCard
        username={this.props.username}
        rolename={rolename}
        data={this.state.data.roles[rolename]}
      />)
    }
    return result
  }

  remove_unit_from_hospital = () => {
    send_command("ship.med_sm", get_observer_id(), "remove_unit_from_hospital", { "value": 1 })
  }
  toogle_med_activity = () => {
    send_command("ship.med_sm", get_observer_id(), "toogle_activity", {})
  }

  get_hospital_crew_control = () => {
    if (this.state.data) {
      if (!this.state.data.hospital)
        return []
    }

    return <div style={{
      "display": "flex",
      "flex-direction": "column",
      "padding-bottom": "5px"
    }}>
      <b>{get_locales("Hospital NPC Crew Control")}</b>
      <label>{get_locales("humans in hospital")}: {this.state.data["hospital"]["units"]}/{this.state.data["hospital"]["capacity"]}</label>
      <progress value={this.state.data["hospital"]["progress"]} max={100}></progress>
      {((this.props.username === "admin") | (this.props.username === "master_medic")) ?
        <button onClick={(e) => { this.remove_unit_from_hospital() }}> return to active crew </button> :
        <none></none>
      }
      <button onClick={(e) => { this.toogle_med_activity() }}> toogle_med_activity </button>

    </div>

  }


  render() {
    return (
      <div style={{
        "display": "flex",
        "flex-direction": "row"
      }}>
        <div
          className='SystemControlWidget'>
          {this.get_hospital_crew_control()}
          {this.get_playerole_cards()}
        </div>

        <PlagueMatrixSection plague_matrix={this.state.plague_matrix} roles={this.state.data.roles} username = {this.props.username}></PlagueMatrixSection>
      </div>
    )
  }

}


class PlayerRoleHealthCard extends React.Component {
  constructor(props) {
    super(props);


    this.state = {
      selected_plague_state: null,
      selected_plague_phase_x: 3,
      selected_plague_phase_y: 3
    }
  }
  apply_cure = (scale_name, cure_type) => {
    send_command("ship.med_sm", get_observer_id(), "apply_" + cure_type + "_cure", { role: this.props.rolename, "axis": scale_name })
  }

  add_points = (scale_name, points) => {
    send_command("ship.med_sm", get_observer_id(), "add_points", { role: this.props.rolename, "axis": scale_name, "value": points })
  }



  toogle_plague_state = () => {
    let current_state = this.props.data["plague"]["active"]
    send_command("ship.med_sm.plague", get_observer_id(), "set_plague_v2_activity", { role: this.props.rolename, "state": !current_state })
  }

  apply_mutator = (mutator) => {
    send_command("ship.med_sm.plague", get_observer_id(), "set_plague_v2_mutator", { role: this.props.rolename, "mutator": mutator })
  }

  username_is_master = () => {
    return (["master_medic", "admin"].includes(this.props.username))
  }

  get_cure_block = (scale_name) => {
    if (!this.username_is_master()) return []
    let result = []
    let cures = ['light', 'hard', 'crit']
    for (let i in cures) {
      result.push(<button onClick={(e) => {
        this.apply_cure(scale_name, cures[i])
      }}>{cures[i]}</button>)
    }
    return result
  }

  get_control_block = (scale_name) => {
    if (!this.username_is_master()) return []
    let result = []
    let cures = [-1, 1]
    for (let i in cures) {
      result.push(<button onClick={(e) => {
        this.add_points(scale_name, cures[i])
      }}>{cures[i]}</button>)
    }
    return result
  }

  set_plague_phase = () => {
    send_command("ship.med_sm.plague", get_observer_id(), "set_plague_v2_phase", {
      role: this.props.rolename,
      "i": this.state.selected_plague_phase_y,
      "j": this.state.selected_plague_phase_x
    })
  }

  get_plague_phase_setter = () => {
    return <div style={{
      "display": "flex",
      "flex-direction": "column"
    }}>
      <label>HP_axis: <input type='number' max={6} min={1} value={this.state.selected_plague_phase_x} onChange={(e) => { this.setState({ 'selected_plague_phase_x': e.target.value }) }} /> </label>
      <label>MP_axis: <input type='number' max={6} min={1} value={this.state.selected_plague_phase_y} onChange={(e) => { this.setState({ 'selected_plague_phase_y': e.target.value }) }} /> </label>
      <button onClick={(e) => { this.set_plague_phase() }}> SET PHASE</button>
    </div>
  }

  is_master = () =>{
    return ["admin", "master_medic"].includes(this.props.username)
  }

  get_regulator = (scale_name) => {
    return (
      <div>
        <label>
          {scale_name}:{this.props.data[scale_name]} ({get_locales("health_state_" + scale_name + this.props.data[scale_name].toString())})
        </label>
        {this.get_cure_block(scale_name)}
        {this.get_control_block(scale_name)}
      </div>
    )
  }

  get_plague_state = () => {
    return <div style={{
      "display": "flex",
      "flex-direction": "column"
    }}>
      <label>{get_locales("plague_active")}: {this.props.data["plague"]["active"].toString()}</label>
      <label>{get_locales("current_phase")}: {this.props.data["plague"]["current_phase"][1]}, {this.props.data["plague"]["current_phase"][0]}</label>
      <label>{get_locales("mutator")}: {this.props.data["plague"]["mutator"]}</label>
      <label>{get_locales("time2next_phase")}: {this.props.data["plague"]["time2next_phase"]}</label>
    </div>
  }

  is_plague_active = () =>{
    return this.props.data["plague"]["active"]
  }


  get_plague_activation_block = () => {
    return <div style={{
      "display": "flex",
      "flex-direction": "column"
    }}>
      <button onClick={(e) => { this.toogle_plague_state() }}>TOOGLE PLAGUE STATE</button>
    </div>
  }

  get_plague_control_block = () => {
    return <div style={{
      "display": "flex",
      "flex-direction": "row"
    }}>
      <button onClick={(e) => { this.apply_mutator("A") }}>A (-x, y)</button>
      <button onClick={(e) => { this.apply_mutator("B") }}>B (x, -y)</button>
      <button onClick={(e) => { this.apply_mutator("C") }}>C (x-1, y+1)</button>
      <button onClick={(e) => { this.apply_mutator("D") }}>D (x+1, y-1)</button>
    </div>
  }



  get_curation_availability = () => {
    return <label>{get_locales("can_be_cured")}: {this.props.data["can_be_cured"].toString()}</label>
  }


  render() {
    let is_master = this.is_master()
    let is_plague_active = this.is_plague_active()
    return (<div className='PlayerRoleHealthCard'>
      <label><b>{get_locales(this.props.rolename)}</b></label>
      {this.get_regulator('HP')}
      {this.get_regulator('MP')}
      {this.get_curation_availability()}
      {is_master?this.get_plague_activation_block():<span></span>}
      {is_plague_active?this.get_plague_state():<span></span>}
      {is_plague_active?this.get_plague_control_block():<span></span>}
      {is_master?this.get_plague_phase_setter():<span></span>}
      <p></p>
    </div>)
  }
}


class PlagueMatrixSection extends React.Component {
  constructor(props) {
    super(props);


    this.state = {
      plague_matrix: null
    }
  }



  componentDidMount() {
    let timer_id = timerscounter.get(this.constructor.name)
    if (!timer_id) {
      clearInterval(timer_id)
    }
    timer_id = setInterval(this.update_plague_matrix, 1000)
    timerscounter.add(this.constructor.name, timer_id)

    if (!get_observer_id()) {
      take_control("Sirocco")
    }

  }

  is_any_infected = () => {
    if (!this.props.roles) return false
    if (["admin", "master_medic"].includes(this.props.username)) return true
    for (let role in this.props.roles) {
      if (this.props.roles[role]["plague"]["active"])
      return true
    }

    return false
  }

  componentWillUnmount() {
    let timer_id = timerscounter.get(this.constructor.name)
    clearInterval(timer_id)
  }

  get_marked_cells = () => {

    let result = []
    for (let role in this.props.roles) {
      if (this.props.roles[role]["plague"]["active"]) {
        let actual_phase = this.props.roles[role]["plague"]["current_phase"]
        result.push(actual_phase)
      }


    }

    return result
  }


  is_cell_marked = (p1, p2, marked_cells) => {

    for (let i = 0; i < marked_cells.length; i++) {
      if (marked_cells[i][0] == p1)
        if (marked_cells[i][1] == p2)
          return true
    }
    return false
  }



  get_plague_matrix = () => {
    let marked_cells = []
    if (this.props.roles) marked_cells = this.get_marked_cells()

    if (!this.props.plague_matrix) return <div>plague_matrix</div>
    let result_column = []
    let result_row = [<button className='plague_matrix_zero_cell' disabled={true}>ZERO</button>]

    for (let i = 0; i < this.props.plague_matrix.length; i++) {
      result_row.push(<button className='plague_matrix_health' disabled={true}>{i}</button>)
    }
    result_row.push(<button className='plague_matrix_zero_cell' disabled={true}>ZERO</button>)

    result_column.push(<div>{result_row}</div>)
    for (let i = 0; i < this.props.plague_matrix.length; i++) {
      result_row = [<button className='plague_matrix_mental' disabled={true}>{i}</button>]
      for (let j = 0; j < this.props.plague_matrix.length; j++) {
        let addClassName = ""
        if (this.is_cell_marked(i, j, marked_cells)) {
          addClassName = " plague_matrix_cell_marked "
        }

        result_row.push(<button className={'plague_matrix_cell' + addClassName} disabled={true}>{this.props.plague_matrix[i][j]}</button>)
      }
      result_row.push(<button className='plague_matrix_mental' disabled={true}>{i}</button>)
      result_column.push(<div>{result_row}</div>)
    }

    result_row = [<button className='plague_matrix_zero_cell' disabled={true}>ZERO</button>]

    for (let i = 0; i < this.props.plague_matrix.length; i++) {
      result_row.push(<button className='plague_matrix_health' disabled={true}>{i}</button>)
    }
    result_row.push(<button className='plague_matrix_zero_cell' disabled={true}>ZERO</button>)
    result_column.push(<div>{result_row}</div>)



    return <div className='plague_matrix_div'> {result_column} </div>

  }

  render() {

    return (
      <div>
        {this.is_any_infected()?
        this.get_plague_matrix():
        <span></span>}
      </div>
    )
  }

}