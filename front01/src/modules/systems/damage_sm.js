import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';

export class DamageControlWidget extends React.Component {
 constructor(props) {
  super(props);



   



  
  this.state = {
  data: {},
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
 }



  
 componentWillUnmount() {
  let timer_id = timerscounter.get(this.constructor.name)
  clearInterval(timer_id)
 }



  
 proceed_data_message = () => {
  let perf_data = get_system_state( "damage_sm")
  this.setState({ "data": perf_data })
 }

 onRepair = (system_name) =>{
  send_command("ship.damage_sm", this.state.data.mark_id, "repair_system", { "system_name": system_name })
 }



  
 get_systems_hp = () => {
  let result = []
  if (this.state.data) {
  if ("systems_hp" in this.state.data) {
   for (let system_name in this.state.data.systems_hp) {
   let current_hp = this.state.data["systems_hp"][system_name]["current_hp"].toFixed(2)
   result.push(
    <label>{system_name}:{current_hp}/{this.state.data["systems_hp"][system_name]["max_hp"]}</label>
   )
   }
  }
  }
  return result
 }



  

 render() {
  return (
  <div className='SystemControlWidget'>
   <b>DamageControl</b>
   {this.get_systems_hp()}
  </div>
  )
 }



  
 }
