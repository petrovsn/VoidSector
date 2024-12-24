
import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';
export class InteractionControlWidget extends React.Component {
 constructor(props) {
  super(props);




  
  this.state = {
  data: {
   "interactable_objects": []
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
 }



  
 componentWillUnmount() {
  let timer_id = timerscounter.get(this.constructor.name)
  clearInterval(timer_id)
 }



  
 proceed_data_message = () => {
  let perf_data = get_system_state( "interact_sm")
  if (perf_data) this.setState({ "data": perf_data })
 }



  
 onInteract = (target_id) => {
  send_command("ship.interact_sm", this.state.data.mark_id, "interact", { "target_id": target_id })
 }



  
 get_interactable_objects = () => {
  let result = []
  for (let i in this.state.data.interactable_objects) {
  let iobj_id = this.state.data.interactable_objects[i]
  result.push(
   <span>
   <label>{iobj_id[0]}</label>
   <button onClick={(e) => { this.onInteract(iobj_id[0]) }}> {iobj_id[1]}</button>
   </span>
  )
  }
  return result
 }



  
 render() {
  return (
  <div
   className='SystemControlWidget'>
   <b>{get_locales("InteractionControl")}</b>
   {this.get_interactable_objects()}
  </div>
  )
 }



  
 }
