import React from 'react'
import {get_server_systems_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales';


export class SystemStateViewer extends React.Component {
 constructor(props) {
  super(props);


  this.state = {
   data: {},
   hided: false,
   system_state: {}
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
  this.setState({ "system_state": get_server_systems_state() })
 }
 render() {



   
  let states = []
  for (let k in this.state.system_state) {
   states.push(<label> {k}: {this.state.system_state[k]}</label>)

  }

  return (
   <div className='AdminSystemViewer'>
    <label onClick={() => { this.setState({ hided: !this.state.hided }); }}><b>{get_locales("SYSTEM STATE")}</b></label>
    {states}
   </div>
  )
 }

}
