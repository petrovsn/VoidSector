import React from 'react'
import { get_http_address, get_system_state, send_command } from '../network/connections'
import { timerscounter } from '../utils/updatetimers'
import { get_locales } from '../locales/locales'

export class AlianceManager extends React.Component {
  constructor() {
    super()
    this.state = {
      data: {
      },
      input_value: ""
    }
  }

  componentDidMount() {
    let timer_id = timerscounter.get(this.constructor.name)
    if (!timer_id) {
      clearInterval(timer_id)
    }
    timer_id = setInterval(this.proceed_message, 1000)
    timerscounter.add(this.constructor.name, timer_id)
  }

  componentWillUnmount() {
    let timer_id = timerscounter.get(this.constructor.name)
    clearInterval(timer_id)
  }

  proceed_message = () => {
    let system_state = get_system_state("launcher_sm")

    this.setState({
      "data": system_state
    })
  }

  add_to_allies = (mark_id) =>{
    send_command("ship.launcher_sm", this.state.data.mark_id, "add_to_aliance", {"mark_id":mark_id})
  }

  remove_from_alies = (mark_id) =>{
    send_command("ship.launcher_sm", this.state.data.mark_id, "remove_from_aliance", {"mark_id":mark_id})
  }

  get_aliance_list = () => {
    let result = []
    for(let tmp_i in this.state.data.aliance){
      result.push(<button onClick={(e)=>{this.remove_from_alies(this.state.data.aliance[tmp_i])}}>{this.state.data.aliance[tmp_i]}[x]</button>)
    }
    return <div>{result}</div>
  }

  get_input_panel = () =>{
    return(
      <div>
        <input style={{
          "width":"100px",
        }} onChange={(e)=>{this.setState({"input_value":e.target.value})}} value={this.state.input_value}></input>
        <button onClick={(e)=>{this.add_to_allies(this.state.input_value)}}>{get_locales("mark_as_allias")}</button>
      </div>
    )
  }

  render() {
    return <div className='SystemControlWidget'>
      <b>{get_locales("Aliance_controller")}</b>
      {this.get_aliance_list()}
      {this.get_input_panel()}
    </div>
  }
}
